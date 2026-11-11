"""Drawing kit for Susanoo's generated figures: palette, SVG helpers, text fitting and box geometry.

Ported from LionDriver's assurance/01-management/figures/figkit.py (MIT, same maintainer) and adapted.
Standard library only; every function is deterministic, so generated SVGs are byte-stable and can be
checked in CI with --check.
"""
from __future__ import annotations

from xml.sax.saxutils import escape

# ---------------------------------------------------------------- palette
FONT = "Inter, 'Segoe UI', Helvetica, Arial, sans-serif"
INK, MUTED, FAINT, LINE, HAIR = "#0F172A", "#475569", "#94A3B8", "#CBD5E1", "#E2E8F0"
CHIP = "#F8FAFC"
SAFETY, SAFETY_BG = "#C2410C", "#FFF7ED"   # protective / safety function
SW, SW_BG = "#0F766E", "#F0FDFA"           # computing / software-dominant
HW, HW_BG = "#4F46E5", "#EEF2FF"           # hardware / mechanical / electrical
EXT, EXT_BG = "#475569", "#F1F5F9"         # outside the boundary
GREEN, GREEN_BG = "#2E9E6A", "#ECFDF5"
AMBER, AMBER_BG = "#D97706", "#FFFBEB"
RED, RED_BG = "#D2553F", "#FEF2F2"
GREY_BG = "#F1F5F9"


class FigureError(Exception):
    """Raised when a figure's source record or layout does not match what the figure expects."""


# ---------------------------------------------------------------- SVG helpers

def fmt(v: float) -> str:
    return f"{v:.1f}".rstrip("0").rstrip(".")


def el(tag: str, text: str | None = None, **attrs) -> str:
    """One SVG element; attribute names use _ for - (stroke_width -> stroke-width); a trailing _ is dropped."""
    a = "".join(f' {k.rstrip("_").replace("_", "-")}="{v}"' for k, v in attrs.items() if v not in ("", None))
    return f"<{tag}{a}/>" if text is None else f"<{tag}{a}>{escape(text)}</{tag}>"


def text(x, y, s, size=11, fill=INK, weight="", anchor="", style="") -> str:
    return el("text", s, x=fmt(x), y=fmt(y), font_size=size, fill=fill, font_weight=weight,
              text_anchor=anchor, font_style=style)


def rect(x, y, w, h, fill="#FFFFFF", stroke=LINE, sw=1.2, rx=8, dash="") -> str:
    return el("rect", None, x=fmt(x), y=fmt(y), width=fmt(w), height=fmt(h), rx=rx, fill=fill, stroke=stroke,
              stroke_width=sw, stroke_dasharray=dash)


def line(x1, y1, x2, y2, stroke=MUTED, sw=1.4, dash="", start="", end="") -> str:
    return el("line", None, x1=fmt(x1), y1=fmt(y1), x2=fmt(x2), y2=fmt(y2), stroke=stroke, stroke_width=sw,
              stroke_dasharray=dash, marker_start=start, marker_end=end)


ARROWS = (f'<marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
          f'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{MUTED}"/></marker>')


def svg(width: int, height: int, title: str, desc: str, body: list[str]) -> str:
    head = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
            f'viewBox="0 0 {width} {height}" font-family="{FONT}" role="img">')
    return "\n".join([head, el("title", title), el("desc", desc), f"<defs>{ARROWS}</defs>",
                      rect(0, 0, width, height, fill="#FFFFFF", stroke="none", rx=0, sw=0), *body, "</svg>"]) + "\n"


def header(width: int, title: str, subtitle: str, ref: str) -> list[str]:
    return [text(40, 44, title, size=20, weight=700),
            text(40, 66, subtitle, size=12.5, fill=MUTED),
            text(width - 40, 44, ref, size=11, fill=MUTED, anchor="end"),
            line(40, 82, width - 40, 82, stroke=HAIR, sw=1)]


def footer(width: int, height: int, note: str) -> list[str]:
    return [line(40, height - 34, width - 40, height - 34, stroke=HAIR, sw=1),
            text(40, height - 16, note, size=10.5, fill=MUTED)]


def legend(x: float, y: float, entries: list[tuple[str, str, str]]) -> tuple[list[str], float]:
    """entries: (fill, stroke, label); a stroke ending in ' dashed' is drawn dashed. Returns (svg, end x)."""
    out = []
    for fill, stroke, label in entries:
        dash = ""
        if stroke.endswith(" dashed"):
            stroke, dash = stroke[:-7], "4 3"
        out.append(rect(x, y - 10, 14, 12, fill=fill, stroke=stroke, rx=3, dash=dash))
        out.append(text(x + 20, y, label, size=11, fill=MUTED))
        x += 34 + text_w(label, 11)
    return out, x


def pill(cx, cy, label, fill=CHIP, color=INK, stroke=LINE, size=9.5) -> list[str]:
    """A rounded label centred on (cx, cy)."""
    w, h = text_w(label, size, True) + 10, size + 6
    return [rect(cx - w / 2, cy - h / 2, w, h, fill=fill, stroke=stroke, rx=h / 2, sw=0.8),
            text(cx, cy + size * 0.36, label, size=size, fill=color, weight=600, anchor="middle")]


# ---------------------------------------------------------------- text metrics

def text_w(s: str, size: float, bold: bool = False) -> float:
    """Approximate rendered width of s (Inter-like metrics)."""
    w = 0.0
    for ch in s:
        if ch in "il.,:;'|!·":
            w += 0.28
        elif ch in "fjrt() -/":
            w += 0.36
        elif ch.isupper() or ch in "mwMW≥≤–—…→×↔":
            w += 0.70
        elif ch.isdigit():
            w += 0.56
        else:
            w += 0.55
    return w * size * (1.06 if bold else 1.0)


def wrap(s: str, width: float, size: float, max_lines: int = 2, bold: bool = False) -> list[str]:
    """Word-wrap s into at most max_lines lines no wider than width; the last line ends with … if cut."""
    words, lines, cur = s.split(), [], ""
    for i, wd in enumerate(words):
        cand = (cur + " " + wd).strip()
        if text_w(cand, size, bold) <= width or not cur:
            cur = cand
            continue
        lines.append(cur)
        cur = wd
        if len(lines) == max_lines:
            break
    else:
        lines.append(cur)
        return lines
    last = lines[-1]
    while last and text_w(last + " …", size, bold) > width:
        last = last.rsplit(" ", 1)[0] if " " in last else last[:-1]
    lines[-1] = last.rstrip(",;:(") + " …"
    return lines


# ---------------------------------------------------------------- geometry

def border_point(box: tuple[float, float, float, float], tx: float, ty: float) -> tuple[float, float]:
    """Where the segment from the centre of box towards (tx, ty) leaves the box."""
    x, y, w, h = box
    cx, cy = x + w / 2, y + h / 2
    dx, dy = tx - cx, ty - cy
    if dx == 0 and dy == 0:
        return cx, cy
    sx = (w / 2) / abs(dx) if dx else float("inf")
    sy = (h / 2) / abs(dy) if dy else float("inf")
    s = min(sx, sy)
    return cx + dx * s, cy + dy * s


def connect(a: tuple, b: tuple) -> tuple[float, float, float, float]:
    """Endpoints of a straight connector between the borders of boxes a and b."""
    acx, acy = a[0] + a[2] / 2, a[1] + a[3] / 2
    bcx, bcy = b[0] + b[2] / 2, b[1] + b[3] / 2
    x1, y1 = border_point(a, bcx, bcy)
    x2, y2 = border_point(b, acx, acy)
    return x1, y1, x2, y2
