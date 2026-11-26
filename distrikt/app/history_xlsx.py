"""Five-period history workbook: explicit assignments, returns and completion flags.

Only the named Historik sheet is imported. The workbook contains fictional
example data; it never creates dates, publishers or completion events itself.
"""
import io
import zipfile
from xml.sax.saxutils import escape

from card_import import read_rows

SHEET = 'Historik'
WIDE_HEADERS = ['kortnummer'] + [
    field + ' ' + str(period)
    for period in range(1, 6)
    for field in ('forkynder', 'udleveret', 'indleveret', 'gennemgået')
]
TEMPLATE_HEADERS = [WIDE_HEADERS[0]] + [
    field + ' ' + str(period)
    for period in range(5, 0, -1)
    for field in ('forkynder', 'udleveret', 'indleveret', 'gennemgået')
]


def _norm(value):
    return str(value or '').strip().casefold()


def _column(number):
    result = ''
    while number:
        number, part = divmod(number - 1, 26)
        result = chr(65 + part) + result
    return result


def _cell(column, row, value='', style=0):
    address = _column(column) + str(row)
    if not value:
        return '<c r="%s" s="%s"/>' % (address, style)
    return '<c r="%s" s="%s" t="inlineStr"><is><t>%s</t></is></c>' % (
        address, style, escape(str(value)))


def template_xlsx():
    """Deterministic, macro-free Excel template with five coloured column groups."""
    ns = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
    rows = []
    rows.append('<row r="1" ht="38" customHeight="1">' +
                _cell(1, 1, 'HISTORIK  /  DISTRIKTSKORT', 1) + '</row>')
    rows.append('<row r="2" ht="33" customHeight="1">' +
                _cell(1, 2, 'Slet den fiktive eksempelrække. Nyeste periode til venstre. Dato: ÅÅÅÅ-MM-DD. '
                      'Indleveret betyder IKKE automatisk gennemgået; vælg kun Ja når det er dokumenteret.', 2) + '</row>')
    group_cells = [_cell(1, 3, 'KORT', 3)]
    for position, period in enumerate(range(5, 0, -1)):
        group_cells.append(_cell(2 + 4 * position, 3, 'PERIODE %s  ·  %s' %
                                 (period, 'NYEST' if period == 5 else 'ÆLDRE'), 3 if period % 2 else 4))
    rows.append('<row r="3" ht="29" customHeight="1">' + ''.join(group_cells) + '</row>')
    rows.append('<row r="4" ht="31" customHeight="1">' + ''.join(
        _cell(i + 1, 4, h.upper(), 5) for i, h in enumerate(TEMPLATE_HEADERS)) + '</row>')
    sample = ['FIK-001',
              'Fiktiv E', '2026-08-02', '2026-08-15', 'Ja',
              'Fiktiv D', '2026-06-02', '2026-06-15', 'Nej',
              'Fiktiv C', '2026-04-03', '2026-04-20', 'Ja',
              'Fiktiv B', '2026-02-03', '2026-02-20', 'Nej',
              'Fiktiv A', '2025-12-03', '2025-12-20', 'Ja']
    rows.append('<row r="5" ht="26" customHeight="1">' + ''.join(
        _cell(i + 1, 5, value, 6) for i, value in enumerate(sample)) + '</row>')
    # Styled empty rows are guides, not import records.
    for row in range(6, 56):
        rows.append('<row r="%s" ht="24" customHeight="1">%s</row>' % (
            row, ''.join(_cell(i, row, style=7 if row % 2 else 8) for i in range(1, 22))))
    widths = [(1, 17)] + [(2 + 4 * i + j, (23, 19, 19, 17)[j])
                            for i in range(5) for j in range(4)]
    cols = ''.join('<col min="%s" max="%s" width="%s" customWidth="1" style="7"/>' %
                   (i, i, width) for i, width in widths)
    merges = ['A1:U1', 'A2:U2'] + [
        '%s3:%s3' % (_column(2 + 4 * i), _column(5 + 4 * i)) for i in range(5)]
    validations = ''.join(
        '<dataValidation type="list" allowBlank="1" showErrorMessage="1" errorTitle="Vælg Ja eller Nej" '
        'error="Gennemgået er kun Ja, når en gennemgang er dokumenteret." sqref="%s5:%s10004">'
        '<formula1>"Ja,Nej"</formula1></dataValidation>' % (_column(5 + 4 * i), _column(5 + 4 * i))
        for i in range(5))
    sheet = ('<worksheet xmlns="' + ns + '"><sheetViews><sheetView workbookViewId="0">'
             '<pane xSplit="1" ySplit="4" topLeftCell="B5" activePane="bottomRight" state="frozen"/>'
             '</sheetView></sheetViews><sheetFormatPr defaultRowHeight="22"/>'
             '<cols>' + cols + '</cols><sheetData>' + ''.join(rows) + '</sheetData>'
             '<autoFilter ref="A4:U10004"/>'
             '<mergeCells count="%s">' % len(merges) +
             ''.join('<mergeCell ref="%s"/>' % ref for ref in merges) + '</mergeCells>'
             '<dataValidations count="5">' + validations +
             '</dataValidations></worksheet>')
    # All input columns are Excel text format: leading zeroes and ISO dates survive.
    styles = ('<styleSheet xmlns="' + ns + '">'
              '<fonts count="3"><font><sz val="11"/><name val="Aptos"/></font>'
              '<font><b/><sz val="15"/><color rgb="FFFFFFFF"/><name val="Aptos Display"/></font>'
              '<font><b/><sz val="10"/><color rgb="FF173251"/><name val="Aptos"/></font></fonts>'
              '<fills count="8"><fill><patternFill patternType="none"/></fill>'
              '<fill><patternFill patternType="gray125"/></fill>'
              + ''.join('<fill><patternFill patternType="solid"><fgColor rgb="%s"/>'
                        '<bgColor indexed="64"/></patternFill></fill>' % color
                        for color in ('FF173251', 'FFEAF4FC', 'FF277E9D', 'FF336D84',
                                      'FFCADFEB', 'FFF5F9FD')) +
              '</fills><borders count="1"><border/></borders>'
              '<cellStyleXfs count="1"><xf numFmtId="0"/></cellStyleXfs>'
              '<cellXfs count="9"><xf numFmtId="0" xfId="0"/>'
              '<xf numFmtId="49" fontId="1" fillId="2" xfId="0" applyNumberFormat="1"/>'
              '<xf numFmtId="49" fontId="2" fillId="3" xfId="0" applyNumberFormat="1"/>'
              '<xf numFmtId="49" fontId="1" fillId="4" xfId="0" applyNumberFormat="1"/>'
              '<xf numFmtId="49" fontId="1" fillId="5" xfId="0" applyNumberFormat="1"/>'
              '<xf numFmtId="49" fontId="2" fillId="6" xfId="0" applyNumberFormat="1"/>'
              '<xf numFmtId="49" fillId="7" xfId="0" applyNumberFormat="1"/>'
              '<xf numFmtId="49" xfId="0" applyNumberFormat="1"/>'
              '<xf numFmtId="49" fillId="7" xfId="0" applyNumberFormat="1"/>'
              '</cellXfs><cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/>'
              '</cellStyles></styleSheet>')
    types = ('<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
             '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
             '<Default Extension="xml" ContentType="application/xml"/>'
             '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
             '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
             '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/></Types>')
    parts = {
        '[Content_Types].xml': types,
        '_rels/.rels': ('<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                       '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
                       'Target="xl/workbook.xml"/></Relationships>'),
        'xl/workbook.xml': ('<workbook xmlns="' + ns +
                            '" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
                            '<sheets><sheet name="' + SHEET + '" sheetId="1" r:id="rId1"/></sheets></workbook>'),
        'xl/_rels/workbook.xml.rels': ('<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                                      '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
                                      'Target="worksheets/sheet1.xml"/>'
                                      '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" '
                                      'Target="styles.xml"/></Relationships>'),
        'xl/styles.xml': styles,
        'xl/worksheets/sheet1.xml': sheet,
    }
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        for filename, xml in parts.items():
            archive.writestr(filename, xml)
    return stream.getvalue()


def _error(line, period, values, message):
    return {'line': line, 'period': period, 'values': values, 'completed': False,
            'error': message}


def wide_records(lines):
    """Expand one card row to <=5 reviewed loan rows; preserve physical line numbers."""
    from history_import import day
    records = []
    card_rows = set()
    for line, original in lines:
        if not any(str(value).strip() for value in original):
            continue
        cells = list(original) + [''] * max(0, len(WIDE_HEADERS) - len(original))
        number = str(cells[0]).strip()
        if any(str(x).strip() for x in cells[len(WIDE_HEADERS):]):
            records.append(_error(line, 0, [number, '', '', '', ''],
                                  'Linjen indeholder kolonner uden for de fem perioder.'))
            continue
        if not number:
            records.append(_error(line, 0, ['', '', '', '', ''], 'Kortnummeret mangler.'))
            continue
        if _norm(number) in card_rows:
            records.append(_error(line, 0, [number, '', '', '', ''],
                                  'Kortnummeret optræder på flere rækker; brug én række pr. kort.'))
            continue
        card_rows.add(_norm(number))
        if getattr(cells[0], 'issue', ''):
            records.append(_error(line, 0, [number, '', '', '', ''],
                                  'Kortnummer: ' + cells[0].issue))
            continue
        found = False
        previous_assigned = None
        direction = None
        for index in range(5):
            part = cells[1 + index * 4:5 + index * 4]
            if not any(str(value).strip() for value in part):
                continue
            found = True
            name, assigned, returned, completed = [str(value).strip() for value in part]
            values = [number, '', name, assigned, returned]
            trouble = next(((WIDE_HEADERS[1 + index * 4 + j] + ': ' + cell.issue)
                            for j, cell in enumerate(part) if getattr(cell, 'issue', '')), None)
            flag = _norm(completed)
            if not trouble and flag not in ('', 'nej', 'no', 'ja', 'yes'):
                trouble = 'Gennemgået %s: vælg Ja eller Nej.' % (index + 1)
            if not trouble and flag in ('ja', 'yes') and not returned:
                trouble = 'Gennemgået %s kræver en indleveringsdato.' % (index + 1)
            if not trouble and assigned:
                try:
                    normalized_assigned = day(assigned)
                    if previous_assigned:
                        if normalized_assigned == previous_assigned:
                            trouble = 'Perioderne må ikke have samme udleveringsdato.'
                        else:
                            step = 1 if normalized_assigned > previous_assigned else -1
                            if direction is not None and step != direction:
                                trouble = 'Perioderne skal stå i datoorden, nyeste eller ældste udlevering først.'
                            elif direction is None:
                                direction = step
                    previous_assigned = normalized_assigned
                except (ValueError, TypeError):
                    pass  # Normal history-import validation reports the invalid date.
            if trouble:
                records.append(_error(line, index + 1, values, trouble))
            else:
                records.append({'line': line, 'period': index + 1,
                                'values': values, 'completed': flag in ('ja', 'yes')})
        if not found:
            records.append(_error(line, 0, [number, '', '', '', ''],
                                  'Angiv mindst én periode med udlevering på kortet.'))
    if len(records) > 10000:
        raise ValueError('Importér højst 10.000 historikperioder ad gangen.')
    return records


def xlsx_records(data):
    """Read only the dedicated data sheet; never evaluate formulas or external links."""
    rows = read_rows(data, sheet_name=SHEET, column_cells=True, strict_sheet=True)
    header_index = next((i for i, (_, values) in enumerate(rows)
                         if [_norm(x) for x in values] in (WIDE_HEADERS, TEMPLATE_HEADERS)), None)
    if header_index is None:
        raise ValueError('Brug Historik-fanen med kolonnerne kortnummer og de fem perioder fra skabelonen.')
    if header_index >= 20:
        raise ValueError('Kolonneoverskrifterne skal stå i de første 20 rækker.')
    headers = [_norm(value) for value in rows[header_index][1]]
    columns = [headers.index(header) for header in WIDE_HEADERS]
    return [(line, [values[index] if index < len(values) else '' for index in columns]
                   + list(values[len(headers):]))
            for line, values in rows[header_index + 1:]]
