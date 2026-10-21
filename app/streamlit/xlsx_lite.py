"""A small, dependency-free .xlsx writer with the subset of the openpyxl API the UAT export uses.

Why: Streamlit in Snowflake (container runtime) only has extra Python packages when an admin sets up external access
to a package index. The UAT pack must work without that, so it is written with the standard library (zipfile + XML).
Supported: sheets, text / number / date / formula cells, fonts, solid fills (hex or theme + tint), alignment and wrap,
number formats, merged cells, column widths, row heights, frozen panes, landscape fit-to-width printing.
"""
from __future__ import annotations

import datetime as dt
import io
import re
import zipfile
from typing import Any, Optional
from xml.sax.saxutils import escape


def _x(s: Any) -> str:
    return escape(str(s), {'"': "&quot;"})


def _clean(s: str) -> str:
    return re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", s)


class Color:
    def __init__(self, rgb: Optional[str] = None, theme: Optional[int] = None, tint: float = 0.0, type: str = "rgb"):
        self.rgb, self.theme, self.tint = rgb, theme, tint

    def xml(self, tag: str) -> str:
        if self.theme is not None:
            return f'<{tag} theme="{self.theme}"' + (f' tint="{self.tint}"' if self.tint else "") + "/>"
        return f'<{tag} rgb="{self.rgb or "FF000000"}"/>'


def _color(c) -> Optional[Color]:
    if c is None:
        return None
    if isinstance(c, Color):
        return c
    c = str(c).lstrip("#").upper()
    return Color(rgb=c if len(c) == 8 else "FF" + c)


class Font:
    def __init__(self, name: str = "Calibri", size: float = 11, bold: bool = False, color=None, italic: bool = False):
        self.name, self.size, self.bold, self.italic, self.color = name, size, bold, italic, _color(color)

    def key(self):
        return (self.name, self.size, self.bold, self.italic, self.color.xml("c") if self.color else "")

    def xml(self) -> str:
        return ("<font>" + ("<b/>" if self.bold else "") + ("<i/>" if self.italic else "") + f'<sz val="{self.size}"/>'
                + (self.color.xml("color") if self.color else "") + f'<name val="{_x(self.name)}"/></font>')


class PatternFill:
    def __init__(self, fill_type: Optional[str] = None, fgColor=None, **_):
        self.fill_type, self.fg = fill_type, _color(fgColor)

    def key(self):
        return (self.fill_type, self.fg.xml("c") if self.fg else "")

    def xml(self) -> str:
        if not self.fill_type:
            return '<fill><patternFill patternType="none"/></fill>'
        return (f'<fill><patternFill patternType="{self.fill_type}">' + (self.fg.xml("fgColor") if self.fg else "")
                + '<bgColor indexed="64"/></patternFill></fill>')


class Alignment:
    def __init__(self, horizontal: Optional[str] = None, vertical: Optional[str] = None, wrap_text: bool = False):
        self.horizontal, self.vertical, self.wrap_text = horizontal, vertical, wrap_text

    def key(self):
        return (self.horizontal, self.vertical, self.wrap_text)

    def xml(self) -> str:
        a = "".join(f' {k}="{v}"' for k, v in (("horizontal", self.horizontal), ("vertical", self.vertical)) if v)
        return f"<alignment{a}" + (' wrapText="1"' if self.wrap_text else "") + "/>"


class Cell:
    __slots__ = ("value", "font", "fill", "alignment", "number_format")

    def __init__(self):
        self.value, self.font, self.fill, self.alignment, self.number_format = None, None, None, None, None


class _Dim:
    def __init__(self):
        self.width: Optional[float] = None
        self.height: Optional[float] = None


class _Dims(dict):
    def __missing__(self, k):
        self[k] = _Dim()
        return self[k]


class _PageSetup:
    def __init__(self):
        self.orientation, self.fitToWidth, self.fitToHeight = None, None, None


class _PSPr:
    def __init__(self):
        self.fitToPage = False


class _SheetProps:
    def __init__(self):
        self.pageSetUpPr = _PSPr()


def col_letter(n: int) -> str:
    s = ""
    while n:
        n, r = divmod(n - 1, 26)
        s = chr(65 + r) + s
    return s


def _split(ref: str) -> tuple[int, int]:
    m = re.fullmatch(r"([A-Z]+)(\d+)", ref.upper())
    col = 0
    for ch in m.group(1):
        col = col * 26 + ord(ch) - 64
    return int(m.group(2)), col


class Worksheet:
    def __init__(self, title: str):
        self.title = title[:31]
        self.cells: dict[tuple[int, int], Cell] = {}
        self.merged: list[str] = []
        self.column_dimensions, self.row_dimensions = _Dims(), _Dims()
        self.freeze_panes: Optional[str] = None
        self.page_setup, self.sheet_properties = _PageSetup(), _SheetProps()

    def __getitem__(self, ref: str) -> Cell:
        return self.cells.setdefault(_split(ref), Cell())

    def __setitem__(self, ref: str, value) -> None:
        self[ref].value = value

    def cell(self, row: int, column: int, value=None) -> Cell:
        c = self.cells.setdefault((row, column), Cell())
        if value is not None:
            c.value = value
        return c

    def merge_cells(self, rng: str) -> None:
        self.merged.append(rng.upper())


class Workbook:
    def __init__(self):
        self.worksheets: list[Worksheet] = [Worksheet("Sheet")]

    @property
    def active(self) -> Worksheet:
        return self.worksheets[0]

    def remove(self, ws: Worksheet) -> None:
        self.worksheets.remove(ws)

    def create_sheet(self, title: str) -> Worksheet:
        ws = Worksheet(title)
        self.worksheets.append(ws)
        return ws

    # -- writing -----------------------------------------------------------------------------------------------------
    def save(self, target) -> None:
        fonts, fills, fmts, xfs = [Font().xml()], ['<fill><patternFill patternType="none"/></fill>',
                                                   '<fill><patternFill patternType="gray125"/></fill>'], {}, ["0|0|0|0|"]
        fkey, filkey, xkey = {Font().key(): 0}, {}, {"0|0|0|0|": 0}
        strings: list[str] = []
        sidx: dict[str, int] = {}

        def style(c: Cell) -> int:
            fi = 0
            if c.font:
                k = c.font.key()
                if k not in fkey:
                    fkey[k] = len(fonts)
                    fonts.append(c.font.xml())
                fi = fkey[k]
            pi = 0
            if c.fill and c.fill.fill_type:
                k = c.fill.key()
                if k not in filkey:
                    filkey[k] = len(fills)
                    fills.append(c.fill.xml())
                pi = filkey[k]
            ni = 0
            fmt = c.number_format
            if fmt is None and isinstance(c.value, (dt.date, dt.datetime)):
                fmt = "yyyy-mm-dd"
            if fmt:
                if fmt not in fmts:
                    fmts[fmt] = 164 + len(fmts)
                ni = fmts[fmt]
            al = c.alignment.xml() if c.alignment else ""
            k = f"{fi}|{pi}|{ni}|{0}|{al}"
            if k not in xkey:
                xkey[k] = len(xfs)
                xfs.append(k)
            return xkey[k]

        sheets_xml = []
        for ws in self.worksheets:
            rows: dict[int, list] = {}
            for (r, c), cell in ws.cells.items():
                rows.setdefault(r, []).append((c, cell))
            for r in ws.row_dimensions:
                rows.setdefault(r, [])
            out = ['<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                   '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
                   'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">']
            if ws.sheet_properties.pageSetUpPr.fitToPage:
                out.append('<sheetPr><pageSetUpPr fitToPage="1"/></sheetPr>')
            out.append("<sheetViews><sheetView workbookViewId=\"0\">")
            if ws.freeze_panes:
                fr, fc = _split(ws.freeze_panes)
                attrs = (f' xSplit="{fc - 1}"' if fc > 1 else "") + (f' ySplit="{fr - 1}"' if fr > 1 else "")
                out.append(f'<pane{attrs} topLeftCell="{ws.freeze_panes}" activePane="bottomRight" state="frozen"/>')
            out.append("</sheetView></sheetViews><sheetFormatPr defaultRowHeight=\"15\"/>")
            cols = sorted(((_split(k + "1")[1], d.width) for k, d in ws.column_dimensions.items() if d.width))
            if cols:
                out.append("<cols>" + "".join(f'<col min="{i}" max="{i}" width="{w}" customWidth="1"/>' for i, w in cols)
                           + "</cols>")
            out.append("<sheetData>")
            for r in sorted(rows):
                h = ws.row_dimensions[r].height if r in ws.row_dimensions else None
                out.append(f'<row r="{r}"' + (f' ht="{h}" customHeight="1"' if h else "") + ">")
                for c, cell in sorted(rows[r], key=lambda x: x[0]):
                    ref = f"{col_letter(c)}{r}"
                    s = style(cell)
                    v = cell.value
                    sa = f' s="{s}"' if s else ""
                    if v is None:
                        out.append(f'<c r="{ref}"{sa}/>')
                    elif isinstance(v, bool):
                        out.append(f'<c r="{ref}"{sa} t="b"><v>{int(v)}</v></c>')
                    elif isinstance(v, (int, float)):
                        out.append(f'<c r="{ref}"{sa}><v>{repr(float(v)) if isinstance(v, float) else v}</v></c>')
                    elif isinstance(v, (dt.date, dt.datetime)):
                        d = v if isinstance(v, dt.datetime) else dt.datetime(v.year, v.month, v.day)
                        serial = (d - dt.datetime(1899, 12, 30)).total_seconds() / 86400
                        out.append(f'<c r="{ref}"{sa}><v>{serial:g}</v></c>')
                    elif isinstance(v, str) and v.startswith("="):
                        out.append(f'<c r="{ref}"{sa}><f>{_x(_clean(v[1:]))}</f></c>')
                    else:
                        t = _clean(str(v))[:32000]
                        if t not in sidx:
                            sidx[t] = len(strings)
                            strings.append(t)
                        out.append(f'<c r="{ref}"{sa} t="s"><v>{sidx[t]}</v></c>')
                out.append("</row>")
            out.append("</sheetData>")
            if ws.merged:
                out.append(f'<mergeCells count="{len(ws.merged)}">'
                           + "".join(f'<mergeCell ref="{m}"/>' for m in ws.merged) + "</mergeCells>")
            out.append('<pageMargins left="0.5" right="0.5" top="0.6" bottom="0.6" header="0.3" footer="0.3"/>')
            ps = ws.page_setup
            if ps.orientation or ps.fitToWidth is not None:
                out.append("<pageSetup" + (f' orientation="{ps.orientation}"' if ps.orientation else "")
                           + (f' fitToWidth="{ps.fitToWidth}"' if ps.fitToWidth is not None else "")
                           + (f' fitToHeight="{ps.fitToHeight}"' if ps.fitToHeight is not None else "") + "/>")
            out.append("</worksheet>")
            sheets_xml.append("".join(out))

        xf_xml = []
        for k in xfs:
            fi, pi, ni, _, al = k.split("|", 4)
            attrs = f'numFmtId="{ni}" fontId="{fi}" fillId="{pi}" borderId="0" xfId="0"'
            attrs += (' applyFont="1"' if fi != "0" else "") + (' applyFill="1"' if pi != "0" else "") \
                + (' applyNumberFormat="1"' if ni != "0" else "") + (' applyAlignment="1"' if al else "")
            xf_xml.append(f"<xf {attrs}>{al}</xf>" if al else f"<xf {attrs}/>")
        styles = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                  '<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
                  + (f'<numFmts count="{len(fmts)}">' + "".join(f'<numFmt numFmtId="{i}" formatCode="{_x(f)}"/>'
                                                              for f, i in fmts.items()) + "</numFmts>" if fmts else "")
                  + f'<fonts count="{len(fonts)}">' + "".join(fonts) + "</fonts>"
                  + f'<fills count="{len(fills)}">' + "".join(fills) + "</fills>"
                  + '<borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders>'
                  + '<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>'
                  + f'<cellXfs count="{len(xf_xml)}">' + "".join(xf_xml) + "</cellXfs>"
                  + '<cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles></styleSheet>')
        sst = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
               f'<sst xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" count="{len(strings)}" '
               f'uniqueCount="{len(strings)}">' + "".join(f'<si><t xml:space="preserve">{_x(s)}</t></si>' for s in strings)
               + "</sst>")
        n = len(self.worksheets)
        wbx = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
               '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
               'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets>'
               + "".join(f'<sheet name="{_x(ws.title)}" sheetId="{i + 1}" r:id="rId{i + 1}"/>'
                         for i, ws in enumerate(self.worksheets))
               + '</sheets><calcPr calcId="191029" fullCalcOnLoad="1"/></workbook>')
        rels = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                + "".join(f'<Relationship Id="rId{i + 1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/'
                          f'relationships/worksheet" Target="worksheets/sheet{i + 1}.xml"/>' for i in range(n))
                + f'<Relationship Id="rId{n + 1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/'
                  f'relationships/styles" Target="styles.xml"/>'
                + f'<Relationship Id="rId{n + 2}" Type="http://schemas.openxmlformats.org/officeDocument/2006/'
                  f'relationships/sharedStrings" Target="sharedStrings.xml"/>'
                + f'<Relationship Id="rId{n + 3}" Type="http://schemas.openxmlformats.org/officeDocument/2006/'
                  f'relationships/theme" Target="theme/theme1.xml"/></Relationships>')
        ctypes = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                  '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                  '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                  '<Default Extension="xml" ContentType="application/xml"/>'
                  '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.'
                  'spreadsheetml.sheet.main+xml"/>'
                  + "".join(f'<Override PartName="/xl/worksheets/sheet{i + 1}.xml" ContentType="application/'
                            f'vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>' for i in range(n))
                  + '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.'
                    'spreadsheetml.styles+xml"/>'
                  '<Override PartName="/xl/sharedStrings.xml" ContentType="application/vnd.openxmlformats-'
                  'officedocument.spreadsheetml.sharedStrings+xml"/>'
                  '<Override PartName="/xl/theme/theme1.xml" ContentType="application/vnd.openxmlformats-'
                  'officedocument.theme+xml"/></Types>')
        root_rels = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                     '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                     '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/'
                     'officeDocument" Target="xl/workbook.xml"/></Relationships>')
        buf = target if hasattr(target, "write") else io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
            z.writestr("[Content_Types].xml", ctypes)
            z.writestr("_rels/.rels", root_rels)
            z.writestr("xl/workbook.xml", wbx)
            z.writestr("xl/_rels/workbook.xml.rels", rels)
            z.writestr("xl/styles.xml", styles)
            z.writestr("xl/sharedStrings.xml", sst)
            z.writestr("xl/theme/theme1.xml", THEME)
            for i, x in enumerate(sheets_xml):
                z.writestr(f"xl/worksheets/sheet{i + 1}.xml", x)
        if not hasattr(target, "write"):
            with open(target, "wb") as f:
                f.write(buf.getvalue())


# Office default theme (colours only), so theme + tint fills resolve the same as in the corporate template.
THEME = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
         '<a:theme xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" name="Office Theme"><a:themeElements>'
         '<a:clrScheme name="Office"><a:dk1><a:sysClr val="windowText" lastClr="000000"/></a:dk1>'
         '<a:lt1><a:sysClr val="window" lastClr="FFFFFF"/></a:lt1><a:dk2><a:srgbClr val="44546A"/></a:dk2>'
         '<a:lt2><a:srgbClr val="E7E6E6"/></a:lt2><a:accent1><a:srgbClr val="4472C4"/></a:accent1>'
         '<a:accent2><a:srgbClr val="ED7D31"/></a:accent2><a:accent3><a:srgbClr val="A5A5A5"/></a:accent3>'
         '<a:accent4><a:srgbClr val="FFC000"/></a:accent4><a:accent5><a:srgbClr val="5B9BD5"/></a:accent5>'
         '<a:accent6><a:srgbClr val="70AD47"/></a:accent6><a:hlink><a:srgbClr val="0563C1"/></a:hlink>'
         '<a:folHlink><a:srgbClr val="954F72"/></a:folHlink></a:clrScheme>'
         '<a:fontScheme name="Office"><a:majorFont><a:latin typeface="Calibri Light"/><a:ea typeface=""/>'
         '<a:cs typeface=""/></a:majorFont><a:minorFont><a:latin typeface="Calibri"/><a:ea typeface=""/>'
         '<a:cs typeface=""/></a:minorFont></a:fontScheme>'
         '<a:fmtScheme name="Office"><a:fillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill>'
         '<a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:solidFill><a:schemeClr val="phClr"/></a:solidFill>'
         '</a:fillStyleLst><a:lnStyleLst><a:ln w="6350"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln>'
         '<a:ln w="12700"><a:solidFill><a:schemeClr val="phClr"/></a:solidFill></a:ln><a:ln w="19050"><a:solidFill>'
         '<a:schemeClr val="phClr"/></a:solidFill></a:ln></a:lnStyleLst><a:effectStyleLst><a:effectStyle>'
         '<a:effectLst/></a:effectStyle><a:effectStyle><a:effectLst/></a:effectStyle><a:effectStyle><a:effectLst/>'
         '</a:effectStyle></a:effectStyleLst><a:bgFillStyleLst><a:solidFill><a:schemeClr val="phClr"/></a:solidFill>'
         '<a:solidFill><a:schemeClr val="phClr"/></a:solidFill><a:solidFill><a:schemeClr val="phClr"/></a:solidFill>'
         '</a:bgFillStyleLst></a:fmtScheme></a:themeElements></a:theme>')
