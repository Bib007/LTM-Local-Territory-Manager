"""Store private task images in the same transaction as their task."""
import base64
import json
import re
import struct
import zlib
import uuid

from photo_ocr import validate_png
from ui_errors import UIError

MAX_IMAGES = 5
MAX_BYTES = 2_000_000
MAX_ENCODED = 4 * ((MAX_BYTES + 2) // 3)
MAX_TOTAL = 48_000_000
IDENTIFIER = re.compile(r'[0-9a-f]{32}')


def create_table(db):
    db.execute('CREATE TABLE IF NOT EXISTS notes.task_images (id TEXT PRIMARY KEY, payload TEXT NOT NULL, deleted_at TEXT, batch TEXT)')


def valid_png(png):
    if not isinstance(png, str) or len(png) > MAX_ENCODED:
        raise ValueError('Et klargjort opgavebillede må højst fylde 2 MB.')
    raw = validate_png(png)
    if len(raw) > MAX_BYTES:
        raise ValueError('Et klargjort opgavebillede må højst fylde 2 MB.')
    # Validate the compressed pixel stream with an explicit expansion bound.
    width, height, _, colour = struct.unpack('>IIBB', raw[16:26])
    stride = width * {0: 1, 2: 3, 4: 2, 6: 4}[colour] + 1
    decoder = zlib.decompressobj()
    pixels = bytearray()
    output = bytearray(raw[:8])
    offset = 8
    try:
        while offset < len(raw):
            size = struct.unpack_from('>I', raw, offset)[0]
            kind = raw[offset + 4:offset + 8]
            end = offset + size + 12
            if kind in (b'IHDR', b'IDAT', b'IEND'):
                output.extend(raw[offset:end])
            if kind == b'IDAT':
                pixels.extend(decoder.decompress(raw[offset + 8:end - 4], stride * height + 1 - len(pixels)))
                if len(pixels) > stride * height:
                    raise ValueError()
            offset = end
        if (len(pixels) != stride * height or not decoder.eof or decoder.unused_data
                or any(pixels[i] > 4 for i in range(0, len(pixels), stride))):
            raise ValueError()
    except (zlib.error, ValueError):
        raise ValueError('PNG-billedet er beskadiget.') from None
    return bytes(output)


def valid_name(name):
    if not isinstance(name, str) or not name.strip() or len(name.strip()) > 150:
        raise ValueError('Ugyldigt navn på opgavebillede.')
    return name.strip()


def update_images(store, note, edits):
    if not isinstance(edits, dict):
        raise ValueError('Ugyldige billedvedhæftninger.')
    add, remove = edits.get('add', []), edits.get('remove', [])
    if (not isinstance(add, list) or len(add) > MAX_IMAGES or not isinstance(remove, list)
            or len(remove) > MAX_IMAGES or any(not isinstance(i, str) or not IDENTIFIER.fullmatch(i) for i in remove)):
        raise ValueError('Ugyldige billedvedhæftninger.')

    current = note.get('images', [])
    remaining = [image for image in current if image['id'] not in remove]
    if len(remaining) + len(add) > MAX_IMAGES:
        raise UIError('Du kan højst vedhæfte {count} billeder til en opgave.', count=MAX_IMAGES)
    new = []
    for image in add:
        if not isinstance(image, dict):
            raise ValueError('Ugyldige billedvedhæftninger.')
        name, png = valid_name(image.get('name')), image.get('png')
        png = base64.b64encode(valid_png(png)).decode('ascii')
        new.append({'id': uuid.uuid4().hex, 'note_id': note['id'], 'name': name, 'png': png})

    for image in current:
        if image['id'] in remove:
            delete_image(store, image['id'])
    if new:
        used = store.db.execute('SELECT coalesce(sum(length(payload)),0) FROM notes.task_images').fetchone()[0]
        if used + sum(len(image['png']) + 1024 for image in new) > MAX_TOTAL:
            raise ValueError('Der er ikke plads til flere opgavebilleder. Fjern billeder fra gamle opgaver først.')
        for image in new:
            store.put('task_images', image)
            remaining.append({'id': image['id'], 'name': image['name']})
    if remaining:
        note['images'] = remaining
    else:
        note.pop('images', None)


def delete_image(store, ident):
    store.workflow_track('task_images', ident)
    store.db.execute('DELETE FROM notes.task_images WHERE id=?', (ident,))
    store._dirty_modules.add('task_images')


def purge_note_images(store, predicate, value):
    select = 'SELECT payload FROM notes.records WHERE deleted_at IS NOT NULL AND '
    for row in store.db.execute(select + predicate, (value,)):
        for image in json.loads(row[0]).get('images', []):
            delete_image(store, image['id'])


def read_image(store, note_id, image_id):
    with store.lock:
        note = store.get('notes', note_id)
        if not note or not any(image['id'] == image_id for image in note.get('images', [])):
            return None
        image = store.get('task_images', image_id)
        if not image or image['note_id'] != note_id:
            return None
        return base64.b64decode(image['png'], validate=True)


def validate_backup(notes, images):
    referenced = {}
    for ident, payload, _, _ in notes:
        note = json.loads(payload)
        links = note.get('images', [])
        if not isinstance(links, list) or len(links) > MAX_IMAGES or links and note.get('entity') == 'activity':
            raise ValueError('Sikkerhedskopien har ugyldige opgavebilleder.')
        for link in links:
            if not isinstance(link, dict) or set(link) != {'id', 'name'}:
                raise ValueError('Sikkerhedskopien har ugyldige opgavebilleder.')
            key = link.get('id')
            if not isinstance(key, str) or not IDENTIFIER.fullmatch(key) or key in referenced:
                raise ValueError('Sikkerhedskopien har ugyldige opgavebilleder.')
            referenced[key] = (ident, valid_name(link.get('name')))
    total = 0
    for ident, payload, deleted, batch in images:
        total += len(payload)
        if total > MAX_TOTAL or deleted is not None or batch is not None:
            raise ValueError('Sikkerhedskopien har ugyldige opgavebilleder.')
        item = json.loads(payload)
        if (not isinstance(item, dict) or set(item) != {'id','note_id','name','png'}
                or item['id'] != ident or referenced.pop(ident, None) != (item['note_id'], item['name'])):
            raise ValueError('Sikkerhedskopien har ugyldige opgavebilleder.')
        if base64.b64encode(valid_png(item['png'])).decode('ascii') != item['png']:
            raise ValueError('Sikkerhedskopien har ugyldige opgavebilleder.')
    if referenced:
        raise ValueError('Sikkerhedskopien mangler opgavebilleder.')
