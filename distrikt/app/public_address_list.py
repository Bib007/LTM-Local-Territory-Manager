"""Privacy-filtered address index for the approved, publicly shared Drive PDF.

Never read raw IB or geo records here: callers pass only public_members() or
public_manual_front() results, which have already removed protected details.
"""
import re


def _clean(value):
    return re.sub(r'\s+', ' ', str(value or '')).strip()


def _natural(value):
    return tuple((0, int(part)) if part.isdigit() else (1, part.casefold())
                 for part in re.split(r'(\d+)', _clean(value)))


def address_entries(members, manual_rows=()):
    """Make a deterministic, approval-preview-safe list; never add IB metadata."""
    rows = []
    for address in members:
        number = _clean(address.get('number'))
        floor = _clean(address.get('floor')).rstrip('.')
        door = _clean(address.get('door'))
        suffix = (floor + ('. ' if floor and door else '') + door).strip()
        label = number + (', ' + suffix if suffix else '') if number else suffix or 'Uden husnummer'
        rows.append({'road': _clean(address.get('road')) or 'Ukendt vej',
                     'postcode': _clean(address.get('postcode')),
                     'label': label, 'manual': False})
    # No automatic expansion of ranges: only display safe, explicitly saved
    # manual front rows. Unsafe manual entries have already been withheld.
    for row in manual_rows:
        road, numbers = _clean(row.get('road')), _clean(row.get('numbers'))
        if road and numbers:
            rows.append({'road': road, 'postcode': '', 'label': numbers, 'manual': True})
    return sorted(rows, key=lambda a: (a['road'].casefold(), a['postcode'],
                                      _natural(a['label']), a['manual']))


def _wrap(value, size, width):
    """Conservative Helvetica line wrapping; never elide an address suffix."""
    limit = max(4, int(width / (size * 0.97)))
    words = _clean(value).split(' ')
    lines = []
    line = ''
    for word in words:
        while len(word) > limit:
            if line:
                lines.append(line)
                line = ''
            lines.append(word[:limit])
            word = word[limit:]
        if not word:
            continue
        if line and len(line) + 1 + len(word) > limit:
            lines.append(line)
            line = ''
        line = (line + ' ' + word).strip()
    if line:
        lines.append(line)
    return lines or ['—']


def _fill(x, y, w, h, color):
    return 'q %.3f %.3f %.3f rg %.2f %.2f %.2f %.2f re f Q' % (*color, x, y, w, h)


def _rule(x1, y1, x2, y2, color=(.83, .88, .92)):
    return 'q %.3f %.3f %.3f RG .55 w %.2f %.2f m %.2f %.2f l S Q' % (*color, x1, y1, x2, y2)


def address_pages(entries, number, name='', width=841.89, height=595.28):
    """Readable two-column landscape pages, continued automatically as needed.

    Returns PDF drawing commands without modifying any image or private data.
    """
    from pdf_export import text
    left = 39
    gap = 27
    col_width = (width - 2 * left - gap) / 2
    xs = (left, left + col_width + gap)
    top, bottom = 455, 64
    pages = [[]]
    col, y = 0, top
    ordinal = 0
    manual = any(row['manual'] for row in entries)

    def advance():
        nonlocal col, y
        if col == 0:
            col = 1
        else:
            pages.append([])
            col = 0
        y = top

    groups = []
    for entry in entries:
        key = (entry['road'], entry['postcode'])
        if not groups or groups[-1][0] != key:
            groups.append((key, []))
        groups[-1][1].append(entry)

    for (road, postcode), items in groups:
        heading = road + (' · ' + postcode if postcode else '')
        heading_lines = _wrap(heading, 11, col_width - 12)
        need_heading = True
        for item in items:
            remaining = _wrap(item['label'], 10, col_width - 60)
            first = True
            while remaining:
                if need_heading:
                    header_height = 15 + len(heading_lines) * 14
                    if y - header_height - 20 < bottom:
                        advance()
                    x = xs[col]
                    if y != top:
                        y -= 7
                    pages[-1].append(_fill(x, y - header_height + 2, col_width, header_height - 2, (.92, .96, .98)))
                    pages[-1].append(_fill(x, y - header_height + 2, 3, header_height - 2, (.12, .48, .62)))
                    for i, line in enumerate(heading_lines):
                        pages[-1].append('q .10 .32 .43 rg ' + text(x + 12, y - 18 - i * 14, line, 11) + ' Q')
                    y -= header_height + 3
                    need_heading = False
                available = int((y - bottom - 5) // 13)
                if available < 1:
                    advance()
                    need_heading = True
                    continue
                chunk, remaining = remaining[:available], remaining[available:]
                x = xs[col]
                row_height = 5 + len(chunk) * 13
                if ordinal % 2 == 0:
                    pages[-1].append(_fill(x, y - row_height + 2, col_width, row_height, (.973, .982, .988)))
                if first:
                    ordinal += 1
                    pages[-1].append('q .48 .56 .63 rg ' + text(x + 8, y - 12, str(ordinal).zfill(3), 8) + ' Q')
                for i, line in enumerate(chunk):
                    pages[-1].append('q .14 .20 .27 rg ' + text(x + 41, y - 13 - 13 * i, line, 10) + ' Q')
                y -= row_height
                first = False
                if remaining:
                    advance()
                    need_heading = True
        y -= 9

    if not entries:
        pages[0].append('q .32 .40 .47 rg ' + text(52, 396, 'Ingen adresser er registreret til offentlig visning.', 13) + ' Q')

    total = len(pages)
    result = []
    for index, commands in enumerate(pages):
        page_number = index + 3
        title = [
            _fill(0, height - 102, width, 102, (.105, .20, .30)),
            _fill(39, height - 84, 4, 59, (.19, .69, .75)),
            'q .74 .87 .94 rg ' + text(54, height - 37, 'LTM  /  DIGITALT DISTRIKTSKORT', 9) + ' Q',
            'q 1 1 1 rg ' + text(54, height - 70, 'ADRESSELISTE', 25) + ' Q',
            'q 1 1 1 rg ' + text(width - 210, height - 57, 'KORT  ' + _clean(number), 13, maxchars=23) + ' Q',
            'q .25 .33 .40 rg ' + text(42, height - 122, _clean(name), 12, maxchars=105) + ' Q',
            'q .25 .33 .40 rg ' + text(width - 220, height - 122,
                                     '%s %s' % (len(entries), 'registrerede vejlinjer' if manual else 'adresser'), 10) + ' Q',
            _rule(42, height - 137, width - 42, height - 137),
        ]
        footnote = 'Manuelle nummerintervaller gengives som registreret.' if manual else 'Adresser fra kortets godkendte offentlige adressevalg.'
        footer = [
            _rule(42, 52, width - 42, 52),
            'q .47 .55 .62 rg ' + text(42, 33, footnote, 8) + ' Q',
            'q .47 .55 .62 rg ' + text(width - 155, 33,
                                    'Side %s af %s' % (page_number, total + 2), 9) + ' Q',
        ]
        result.append(title + commands + footer)
    return result
