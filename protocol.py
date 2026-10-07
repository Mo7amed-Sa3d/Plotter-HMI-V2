"""Builders for the Main MCU serial protocol, plus response parsers."""

import re
from dataclasses import dataclass
from typing import Optional


# ---- Command builders ------------------------------------------------------

def move_linear(x=None, y=None, f=None):
    parts = ["MOVE_LINEAR"]
    if x is not None: parts.append(f"X{x:.4f}")
    if y is not None: parts.append(f"Y{y:.4f}")
    if f is not None: parts.append(f"F{f:.2f}")
    return " ".join(parts)

def move_rapid(x=None, y=None):
    parts = ["MOVE_RAPID"]
    if x is not None: parts.append(f"X{x:.4f}")
    if y is not None: parts.append(f"Y{y:.4f}")
    return " ".join(parts)

def wait_idle():       return "WAIT_IDLE"
def home_x():          return "HOME_X"
def zero_x(x):         return f"ZERO_X X{x:.4f}"
def zero_y(y):         return f"ZERO_Y Y{y:.4f}"
def feed(mm, f=None):
    cmd = f"FEED X{mm:.4f}"
    if f is not None: cmd += f" F{f:.2f}"
    return cmd
def auto_feed():       return "AUTO_FEED"
def set_pwm(ch, duty): return f"SET_PWM P{int(ch)} S{int(duty)}"
def pwm_off(ch):       return f"PWM_OFF P{int(ch)}"
def get_sensors():     return "GET_SENSORS"
def get_position():    return "GET_POSITION"
def eject_paper():     return "EJECT_PAPER"
def stop():            return "STOP"
def reset():           return "RESET"


# ---- Response parsers ------------------------------------------------------

@dataclass
class Position:
    x: float
    y: float
    f: float
    qx: float
    qy: float
    homed: bool
    s1: bool
    s2: bool
    s3: bool

@dataclass
class Sensors:
    s1: bool
    s2: bool
    s3: bool
    x_limit: bool


_POS_RE = re.compile(
    r"<POS:X=([-\d.]+),Y=([-\d.]+),F=([-\d.]+),QX=([-\d.]+),QY=([-\d.]+),"
    r"H=(\d),S1=(\d),S2=(\d),S3=(\d)>"
)

_SEN_RE = re.compile(r"<SENSORS:S1=(\d),S2=(\d),S3=(\d),XLIM=(\d)>")


def parse_position(line: str) -> Optional[Position]:
    m = _POS_RE.search(line)
    if not m:
        return None
    return Position(
        x=float(m.group(1)), y=float(m.group(2)), f=float(m.group(3)),
        qx=float(m.group(4)), qy=float(m.group(5)),
        homed=bool(int(m.group(6))),
        s1=bool(int(m.group(7))),
        s2=bool(int(m.group(8))),
        s3=bool(int(m.group(9))),
    )


def parse_sensors(line: str) -> Optional[Sensors]:
    m = _SEN_RE.search(line)
    if not m:
        return None
    return Sensors(
        s1=bool(int(m.group(1))),
        s2=bool(int(m.group(2))),
        s3=bool(int(m.group(3))),
        x_limit=bool(int(m.group(4))),
    )