"""Company themes: brand colours in, a complete and checked dashboard theme out.

A theme is a small set of brand inputs (primary, accent, background, surface, text, positive, negative, warning and
up to six chart colours). Everything else the dashboard needs (lines, tints, heat scale, button text, summary band)
is derived from them, so a company only has to supply what its brand guide already states.

Inputs come from a form, an uploaded token file (JSON design tokens or CSS custom properties) or a logo (PNG, JPG or
SVG, main colours extracted). Before a theme is saved it is checked:
  T-01 text contrast       body and secondary text on background and cards >= 4.5:1 (WCAG 2.1 AA, 1.4.3)
  T-02 button text         text on the primary colour >= 4.5:1
  T-03 chart contrast      every chart colour >= 3:1 against the cards (WCAG 1.4.11 non-text contrast)
  T-04 chart distinct      every pair of chart colours clearly different (CIE76 delta E >= 15)
  T-05 good vs bad         positive and negative are different colour families and each >= 3:1 on cards
A failing colour is nudged lighter or darker (hue kept) until it passes; the report says what was changed so the
person saving the theme can accept it or fix the brand input. Nothing is executed from an upload: files are parsed
for colour values only.
"""
from __future__ import annotations

import base64
import colorsys
import io
import json
import re
from typing import Any, Optional

HEX = re.compile(r"#(?:[0-9a-fA-F]{6}|[0-9a-fA-F]{3})\b")
ROLES = ("primary", "accent", "background", "surface", "text", "positive", "negative", "warning")
MAX_UPLOAD = 1_500_000          # bytes, after base64 decoding

# words in token names / JSON keys -> role (first match wins, most specific first)
ROLE_WORDS = [
    ("positive", r"success|positive|good|up\b|gain"),
    ("negative", r"error|danger|negative|bad|down\b|loss|critical"),
    ("warning", r"warn|caution|amber"),
    ("background", r"background|\bbg\b|canvas|page"),
    ("surface", r"surface|card|panel|paper|container"),
    ("text", r"text|ink|foreground|\bfg\b|body|on-?surface"),
    ("accent", r"accent|secondary|highlight|tertiary"),
    ("primary", r"primary|brand|main|base"),
]
CHART_WORDS = r"chart|palette|data|series|categor|viz|graph"

BUILT_IN = {
    "classic": {"name": "Classic", "builtin": True, "tokens": {}},
    "editorial": {"name": "Editorial (warm)", "builtin": True, "tokens": {}},
    "command": {"name": "Command (dark)", "builtin": True, "tokens": {}},
}


# ------------------------------------------------------------------------------------------------ colour maths
def norm(h: Any) -> Optional[str]:
    if not isinstance(h, str):
        return None
    m = HEX.search(h.strip())
    if not m:
        return None
    v = m.group(0)[1:]
    if len(v) == 3:
        v = "".join(c * 2 for c in v)
    return "#" + v.lower()


def rgb(h: str) -> tuple[float, float, float]:
    h = norm(h) or "#000000"
    return tuple(int(h[i:i + 2], 16) / 255 for i in (1, 3, 5))


def to_hex(r: float, g: float, b: float) -> str:
    return "#" + "".join(f"{max(0, min(255, round(c * 255))):02x}" for c in (r, g, b))


def mix(a: str, b: str, t: float) -> str:
    """t=0 -> a, t=1 -> b."""
    x, y = rgb(a), rgb(b)
    return to_hex(*(x[i] + (y[i] - x[i]) * t for i in range(3)))


def luminance(h: str) -> float:
    def ch(c):
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = rgb(h)
    return 0.2126 * ch(r) + 0.7152 * ch(g) + 0.0722 * ch(b)


def contrast(a: str, b: str) -> float:
    la, lb = luminance(a), luminance(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def _lab(h: str) -> tuple[float, float, float]:
    def lin(c):
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (lin(c) for c in rgb(h))
    x = (r * 0.4124 + g * 0.3576 + b * 0.1805) / 0.95047
    y = (r * 0.2126 + g * 0.7152 + b * 0.0722)
    z = (r * 0.0193 + g * 0.1192 + b * 0.9505) / 1.08883

    def f(t):
        return t ** (1 / 3) if t > 0.008856 else 7.787 * t + 16 / 116
    fx, fy, fz = f(x), f(y), f(z)
    return 116 * fy - 16, 500 * (fx - fy), 200 * (fy - fz)


def delta_e(a: str, b: str) -> float:
    p, q = _lab(a), _lab(b)
    return sum((p[i] - q[i]) ** 2 for i in range(3)) ** 0.5


def hls(h: str) -> tuple[float, float, float]:
    return colorsys.rgb_to_hls(*rgb(h))


def from_hls(hh: float, ll: float, ss: float) -> str:
    return to_hex(*colorsys.hls_to_rgb(hh % 1.0, max(0.0, min(1.0, ll)), max(0.0, min(1.0, ss))))


def is_dark(h: str) -> bool:
    return luminance(h) < 0.2


def saturation(h: str) -> float:
    return hls(h)[2] if 0.06 < hls(h)[1] < 0.94 else 0.0


def nudge(color: str, against: str, need: float) -> str:
    """Move a colour's lightness (hue and saturation kept) away from `against` until contrast >= need."""
    if contrast(color, against) >= need:
        return color
    hh, ll, ss = hls(color)
    step = -0.02 if not is_dark(against) else 0.02
    for _ in range(60):
        ll += step
        c = from_hls(hh, ll, ss)
        if contrast(c, against) >= need:
            return c
        if ll <= 0 or ll >= 1:
            break
    return "#000000" if not is_dark(against) else "#ffffff"


def best_on(bg: str) -> str:
    return "#ffffff" if contrast("#ffffff", bg) >= contrast("#111111", bg) else "#111111"


def hue_gap(a: str, b: str) -> float:
    d = abs(hls(a)[0] - hls(b)[0]) * 360
    return min(d, 360 - d)


# ------------------------------------------------------------------------------------------------ inputs
def clean_inputs(raw: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for r in ROLES:
        v = norm((raw or {}).get(r))
        if v:
            out[r] = v
    chart = [norm(c) for c in ((raw or {}).get("chart") or [])]
    out["chart"] = [c for c in dict.fromkeys(chart) if c][:6]
    return out


def _flatten(obj: Any, path: str = "", out: Optional[list] = None) -> list[tuple[str, Any]]:
    out = [] if out is None else out
    if isinstance(obj, dict):
        if ("value" in obj or "$value" in obj) and not isinstance(obj.get("value", obj.get("$value")), (dict, list)):
            out.append((path, obj.get("value", obj.get("$value"))))
            return out
        for k, v in obj.items():
            _flatten(v, f"{path}.{k}" if path else str(k), out)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            _flatten(v, f"{path}[{i}]", out)
    else:
        out.append((path, obj))
    return out


def _assign(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    roles: dict[str, str] = {}
    chart: list[str] = []
    loose: list[str] = []
    for name, value in pairs:
        c = norm(value) if isinstance(value, str) else None
        if not c:
            continue
        key = name.lower().replace("_", "-")
        if re.search(CHART_WORDS, key):
            chart.append(c)
            continue
        for role, pat in ROLE_WORDS:
            if re.search(pat, key):
                roles.setdefault(role, c)
                break
        else:
            loose.append(c)
    if "primary" not in roles and loose:
        roles["primary"] = loose.pop(0)
    if "accent" not in roles and loose:
        roles["accent"] = loose.pop(0)
    if not chart:
        chart = loose
    return clean_inputs({**roles, "chart": chart})


def parse_tokens(text: str) -> dict[str, Any]:
    """JSON design tokens (any nesting, {value}/{$value} leaves) or CSS custom properties / any text with hex."""
    text = (text or "")[:MAX_UPLOAD]
    try:
        return _assign(_flatten(json.loads(text)))
    except (ValueError, TypeError):
        pass
    pairs = re.findall(r"(--?[\w-]+|[\w-]+)\s*:\s*(#[0-9a-fA-F]{3,6})\b", text)
    if pairs:
        return _assign([(k, v) for k, v in pairs])
    return _assign([("", h) for h in HEX.findall(text)])


def parse_logo(data: bytes, filename: str = "") -> dict[str, Any]:
    """Main colours of a logo: SVG fills/strokes by frequency, or a raster image quantised to its main colours."""
    if len(data) > MAX_UPLOAD:
        raise ValueError("The logo is larger than 1.5 MB.")
    if filename.lower().endswith(".svg") or data[:200].lstrip().startswith((b"<svg", b"<?xml")):
        txt = data.decode("utf-8", "ignore")
        counts: dict[str, int] = {}
        for h in HEX.findall(txt):
            c = norm(h)
            counts[c] = counts.get(c, 0) + 1
        ranked = sorted(counts, key=lambda c: -counts[c])
    else:
        from PIL import Image
        img = Image.open(io.BytesIO(data)).convert("RGBA")
        img.thumbnail((160, 160))
        raw = img.tobytes()
        px = [tuple(raw[i:i + 4]) for i in range(0, len(raw), 4) if raw[i + 3] > 200]   # ignore transparent pixels
        if not px:
            raise ValueError("The logo has no visible colours.")
        flat = Image.new("RGB", (len(px), 1))
        flat.putdata([p[:3] for p in px])
        q = flat.quantize(colors=10, method=Image.Quantize.MEDIANCUT)
        pal = q.getpalette()
        counts = {}
        for n, idx in q.getcolors():
            c = to_hex(*(v / 255 for v in pal[idx * 3: idx * 3 + 3]))
            counts[c] = counts.get(c, 0) + n
        ranked = sorted(counts, key=lambda c: -counts[c])
    brand = [c for c in ranked if saturation(c) >= 0.18]
    neutrals = [c for c in ranked if saturation(c) < 0.18]
    if not brand and not neutrals:
        raise ValueError("No colours found in the logo.")
    chosen: list[str] = []
    for c in brand:
        if all(delta_e(c, x) >= 18 for x in chosen):
            chosen.append(c)
    out = {"primary": chosen[0] if chosen else neutrals[0]}
    if len(chosen) > 1:
        out["accent"] = chosen[1]
    dark_neutral = next((c for c in neutrals if luminance(c) < 0.08), None)
    if dark_neutral:
        out["text"] = dark_neutral
    out["chart"] = chosen[:6]
    return clean_inputs(out)


def parse_upload(kind: str, name: str, b64: str) -> dict[str, Any]:
    try:
        data = base64.b64decode(b64 or "", validate=False)
    except Exception as exc:
        raise ValueError("Could not read the file.") from exc
    if len(data) > MAX_UPLOAD:
        raise ValueError("The file is larger than 1.5 MB.")
    if kind == "logo":
        return parse_logo(data, name)
    return parse_tokens(data.decode("utf-8", "ignore"))


# ------------------------------------------------------------------------------------------------ derive + check
DEFAULT_CHART_ROTATE = (0.0, 0.5, 0.12, 0.62, 0.3, 0.82)


def _chart_from(primary: str, accent: Optional[str], given: list[str]) -> list[str]:
    out = list(given)
    seeds = [primary] + ([accent] if accent else [])
    for s in seeds:
        if len(out) < 6 and all(delta_e(s, x) >= 15 for x in out):
            out.append(s)
    hh, ll, ss = hls(primary)
    ss = min(max(ss, 0.42), 0.58)            # generated colours stay calm next to the brand colours
    i = 0
    while len(out) < 6 and i < 40:
        rot = DEFAULT_CHART_ROTATE[i % 6] + (i // 6) * 0.07
        light = (0.36, 0.5, 0.42, 0.56, 0.32, 0.46)[i % 6]
        c = from_hls(hh + rot, light, ss)
        if all(delta_e(c, x) >= 15 for x in out):
            out.append(c)
        i += 1
    return out[:6]


def build(inputs: dict[str, Any]) -> dict[str, Any]:
    """Brand inputs -> full token set + check report. Returns {tokens, checks, inputs, dark}."""
    i = clean_inputs(inputs)
    if not i.get("primary"):
        raise ValueError("A theme needs at least a primary brand colour.")
    checks: list[dict[str, Any]] = []
    primary = i["primary"]
    accent = i.get("accent")
    bg = i.get("background") or "#f6f7f9"
    dark = is_dark(bg)
    card = i.get("surface") or (mix(bg, "#ffffff", 0.85) if not dark else mix(bg, "#ffffff", 0.06))
    ink = i.get("text") or ("#1b1f24" if not dark else "#f2f2f2")

    def fix(label, cid, color, against, need, role):
        c2 = nudge(color, against, need)
        ratio = contrast(c2, against)
        st = "pass" if c2 == color else ("fixed" if ratio >= need else "fail")
        checks.append({"id": cid, "label": label, "status": st, "ratio": round(contrast(color, against), 2),
                       "need": need, "role": role, "from": color, "to": c2,
                       "detail": (f"{color} on {against} is {contrast(color, against):.2f}:1"
                                  + ("" if st == "pass" else f"; adjusted to {c2} ({ratio:.2f}:1)"))})
        return c2

    ink = fix("Text on cards", "T-01", ink, card, 4.5, "text")
    ink = fix("Text on page background", "T-01", ink, bg, 4.5, "text")
    muted = fix("Secondary text on cards", "T-01", mix(ink, card, 0.38), card, 4.5, "muted")
    faint = mix(ink, card, 0.55)
    line, line2 = mix(ink, card, 0.86), mix(ink, card, 0.92)
    on_primary = best_on(primary)
    btn = primary
    if contrast(on_primary, primary) < 4.5:
        darker = nudge(primary, "#ffffff", 4.5)           # white text on a slightly deeper brand colour reads best
        if delta_e(darker, primary) <= 14:
            on_primary, btn = "#ffffff", darker
        else:
            btn = nudge(primary, on_primary, 4.5)
    checks.append({"id": "T-02", "label": "Button text on the primary colour", "role": "primary",
                   "status": "pass" if btn == primary else ("fixed" if contrast(on_primary, btn) >= 4.5 else "fail"),
                   "ratio": round(contrast(on_primary, primary), 2), "need": 4.5, "from": primary, "to": btn,
                   "detail": f"{on_primary} text on {primary} is {contrast(on_primary, primary):.2f}:1"
                             + ("" if btn == primary else f"; buttons use {btn} ({contrast(on_primary, btn):.2f}:1)")})

    chart = _chart_from(primary, accent, i.get("chart") or [])
    fixed_chart = []
    for n, c in enumerate(chart):
        fixed_chart.append(fix(f"Chart colour {n + 1} on cards", "T-03", c, card, 3.0, f"c{n + 1}"))
    # distinct pairs
    for a in range(len(fixed_chart)):
        for b in range(a):
            if delta_e(fixed_chart[a], fixed_chart[b]) < 15:
                hh, ll, ss = hls(fixed_chart[a])
                moved = None
                for step in (0.12, -0.12, 0.2, -0.2):
                    c = from_hls(hh, ll + step, ss)
                    if contrast(c, card) >= 3 and all(delta_e(c, x) >= 15 for k, x in enumerate(fixed_chart) if k != a):
                        moved = c
                        break
                checks.append({"id": "T-04", "label": f"Chart colours {b + 1} and {a + 1} too similar",
                               "status": "fixed" if moved else "fail", "role": f"c{a + 1}",
                               "from": fixed_chart[a], "to": moved or fixed_chart[a],
                               "detail": f"delta E {delta_e(fixed_chart[a], fixed_chart[b]):.1f} (needs 15)"
                                         + (f"; colour {a + 1} adjusted to {moved}" if moved else "")})
                if moved:
                    fixed_chart[a] = moved
    if not any(c["id"] == "T-04" for c in checks):
        checks.append({"id": "T-04", "label": "Chart colours are distinct", "status": "pass", "role": "chart",
                       "detail": f"smallest delta E between any two: "
                                 f"{min(delta_e(x, y) for k, x in enumerate(fixed_chart) for y in fixed_chart[:k]):.1f}"})
    ok = fix("Positive colour on cards", "T-05", i.get("positive") or "#1f8a5b", card, 3.0, "positive")
    bad = fix("Negative colour on cards", "T-05", i.get("negative") or "#c4473a", card, 3.0, "negative")
    gap = hue_gap(ok, bad)
    checks.append({"id": "T-05", "label": "Positive and negative are different colour families", "role": "positive",
                   "status": "pass" if gap >= 60 else "fail",
                   "detail": f"hue difference {gap:.0f}° (needs 60°)" + ("" if gap >= 60 else
                             "; ▲▼ arrows still show direction, but colour alone will not")})
    warn = nudge(i.get("warning") or "#c08a2c", card, 3.0)
    brand = accent or primary
    h_lo, h_hi = mix(primary, card, 0.9), (mix(primary, "#000000", 0.25) if not dark else mix(primary, "#ffffff", 0.2))
    heat = [mix(h_lo, h_hi, k / 6) for k in range(7)]
    tint = mix(primary, card, 0.94)
    band1 = mix(primary, "#000000", 0.45) if not dark else mix(card, "#000000", 0.2)
    band2 = mix(primary, "#000000", 0.15) if not dark else mix(primary, card, 0.6)
    t = {
        "bg": bg, "page": bg, "card": card, "ink": ink, "muted": muted, "faint": faint, "line": line, "line2": line2,
        "brand": brand, "primary": btn, "deep": btn, "on-primary": on_primary, "ai": "#7d44cf" if not dark else "#b79ad9",
        "ok": ok, "bad": bad, "warn": warn, "tint": tint,
        **{f"c{n + 1}": c for n, c in enumerate(fixed_chart)}, "c-other": mix(ink, card, 0.7),
        **{f"h{n + 1}": c for n, c in enumerate(heat)},
        "area": brand, "line-main": fixed_chart[0], "chip-bg": line2, "chip-on": btn, "chip-on-ink": on_primary,
        "heat-empty": tint, "heat-ink": ink, "heat-ink-hi": best_on(heat[-1]),
        "band1": band1, "band2": band2, "band-accent": mix(brand, "#ffffff", 0.55), "band-ink": best_on(band1),
    }
    return {"tokens": t, "checks": checks, "inputs": i, "dark": dark,
            "status": "fail" if any(c["status"] == "fail" for c in checks) else
                      "fixed" if any(c["status"] == "fixed" for c in checks) else "pass"}


def css_vars(tokens: dict[str, str]) -> dict[str, str]:
    """Token set -> CSS custom properties for the dashboard root (only colour values pass)."""
    return {f"--{k}": v for k, v in (tokens or {}).items() if re.fullmatch(r"[a-z0-9-]{1,20}", k) and norm(v) == v}
