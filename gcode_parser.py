"""Minimal but functional G-code parser and toolpath renderer."""

import math
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Move:
    kind: str          # 'rapid' | 'linear' | 'arc_cw' | 'arc_ccw'
    x0: float
    y0: float
    x1: float
    y1: float
    i: float = 0.0
    j: float = 0.0
    feed: Optional[float] = None


@dataclass
class ParsedJob:
    moves: List[Move] = field(default_factory=list)
    min_x: float = 0.0
    max_x: float = 0.0
    min_y: float = 0.0
    max_y: float = 0.0

    @property
    def width(self) -> float:  return max(self.max_x - self.min_x, 1e-3)
    @property
    def height(self) -> float: return max(self.max_y - self.min_y, 1e-3)


def parse_file(path: str) -> ParsedJob:
    with open(path, "r", errors="replace") as fh:
        return parse_text(fh.read())


def parse_text(text: str) -> ParsedJob:
    job = ParsedJob()
    x = y = 0.0
    abs_mode = True
    scale = 1.0
    feed: Optional[float] = None

    first = True
    for raw in text.splitlines():
        line = raw.split(";", 1)[0].strip()
        if not line:
            continue
        tokens = line.split()
        if not tokens:
            continue
        code = tokens[0].upper()

        if code == "G20":  scale = 25.4;  continue
        if code == "G21":  scale = 1.0;   continue
        if code == "G90":  abs_mode = True; continue
        if code == "G91":  abs_mode = False; continue
        if code == "G28" or code == "G92": continue

        if code in ("G0", "G1", "G2", "G3"):
            nx, ny, ni, nj, nf = x, y, 0.0, 0.0, feed
            for t in tokens[1:]:
                if not t: continue
                c = t[0].upper()
                try:
                    v = float(t[1:])
                except ValueError:
                    continue
                if c == "X": nx = v * scale if abs_mode else x + v * scale
                elif c == "Y": ny = v * scale if abs_mode else y + v * scale
                elif c == "I": ni = v * scale
                elif c == "J": nj = v * scale
                elif c == "F": nf = v * scale

            kind = {"G0": "rapid", "G1": "linear",
                    "G2": "arc_cw", "G3": "arc_ccw"}[code]
            job.moves.append(Move(kind=kind, x0=x, y0=y, x1=nx, y1=ny,
                                  i=ni, j=nj, feed=nf))

            if first:
                job.min_x = job.max_x = x
                job.min_y = job.max_y = y
                first = False
            job.min_x = min(job.min_x, nx); job.max_x = max(job.max_x, nx)
            job.min_y = min(job.min_y, ny); job.max_y = max(job.max_y, ny)
            x, y = nx, ny

    return job


def arc_points(mv: Move, segments: int = 48):
    """Yield (x, y) points along an arc move."""
    cx, cy = mv.x0 + mv.i, mv.y0 + mv.j
    r = math.hypot(mv.i, mv.j)
    if r < 1e-6:
        yield mv.x1, mv.y1
        return
    a0 = math.atan2(mv.y0 - cy, mv.x0 - cx)
    a1 = math.atan2(mv.y1 - cy, mv.x1 - cx)
    if mv.kind == "arc_cw":
        if a1 >= a0: a1 -= 2 * math.pi
    else:
        if a1 <= a0: a1 += 2 * math.pi
    for i in range(1, segments + 1):
        t = a0 + (a1 - a0) * i / segments
        yield cx + r * math.cos(t), cy + r * math.sin(t)