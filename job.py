"""Job runner: streams G-code to the Main MCU with pause/resume."""

import threading
import time
from enum import Enum, auto
from typing import Callable, Optional

from config import DEFAULT_FORCE_A, DEFAULT_FORCE_B, DEFAULT_SPEED
from gcode_parser import Move, ParsedJob, parse_file
from machine import Machine
from protocol import (move_linear, move_rapid, set_pwm, pwm_off,
                      wait_idle, set_pwm as _sp)


class JobState(Enum):
    IDLE = auto()
    RUNNING = auto()
    PAUSED = auto()
    FINISHED = auto()
    ERROR = auto()


class Job:
    def __init__(self, machine: Machine, dispatch: Callable):
        self.machine = machine
        self.dispatch = dispatch

        self.state = JobState.IDLE
        self.path: Optional[str] = None
        self.job: Optional[ParsedJob] = None
        self.progress = 0.0
        self.current_index = 0
        self.total_moves = 0
        self.speed_override = DEFAULT_SPEED
        self.force_a = DEFAULT_FORCE_A
        self.force_b = DEFAULT_FORCE_B

        self._thread: Optional[threading.Thread] = None
        self._pause = threading.Event()
        self._cancel = threading.Event()

        self._state_listeners: list[Callable[[Job], None]] = []
        self._move_listeners: list[Callable[[float], None]] = []

    def on_state(self, cb): self._state_listeners.append(cb)
    def on_progress(self, cb): self._move_listeners.append(cb)

    def _notify_state(self):
        for cb in self._state_listeners:
            self.dispatch(lambda c=cb: c(self))

    def _notify_progress(self):
        for cb in self._move_listeners:
            self.dispatch(lambda c=cb, p=self.progress: c(p))

    # ---- Public API ----

    def start(self, path: str):
        if self.state in (JobState.RUNNING, JobState.PAUSED):
            return
        self.path = path
        self.job = parse_file(path)
        self.total_moves = len(self.job.moves)
        self.current_index = 0
        self.progress = 0.0
        self._pause.clear()
        self._cancel.clear()
        self.state = JobState.RUNNING
        self._notify_state()

        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def pause(self):
        if self.state == JobState.RUNNING:
            self._pause.set()
            self.state = JobState.PAUSED
            self.machine.command(wait_idle())
            self._notify_state()

    def resume(self):
        if self.state == JobState.PAUSED:
            self._pause.clear()
            self.state = JobState.RUNNING
            self._notify_state()

    def cancel(self):
        if self.state in (JobState.RUNNING, JobState.PAUSED):
            self._cancel.set()
            self._pause.clear()
            self.machine.command("STOP", wait_ok=False)

    def set_speed(self, mm_s: float):
        self.speed_override = max(1.0, min(200.0, mm_s))

    def set_force(self, channel: int, duty: int):
        if channel == 0: self.force_a = max(0, min(255, duty))
        else:            self.force_b = max(0, min(255, duty))
        self.machine.command(set_pwm(channel, duty if channel == 0 else 0),
                             wait_ok=False)
        self.machine.command(set_pwm(channel, duty), wait_ok=False)

    # ---- Runner thread ----

    def _run(self):
        try:
            self.machine.command(set_pwm(0, self.force_a), wait_ok=False)

            while self.current_index < self.total_moves:
                if self._cancel.is_set():
                    break
                while self._pause.is_set() and not self._cancel.is_set():
                    time.sleep(0.05)
                if self._cancel.is_set():
                    break

                mv = self.job.moves[self.current_index]
                self._send_move(mv)
                self.current_index += 1
                self.progress = self.current_index / self.total_moves
                self._notify_progress()

            self.machine.command(wait_idle())

        except Exception:
            self.state = JobState.ERROR
            self._notify_state()
            return

        self.machine.command(pwm_off(0), wait_ok=False)
        self.state = JobState.FINISHED if not self._cancel.is_set() else JobState.IDLE
        self._notify_state()

    def _send_move(self, mv: Move):
        f = mv.feed or self.speed_override
        f = min(f, self.speed_override) if self.speed_override else f

        if mv.kind == "rapid":
            self.machine.fire(move_rapid(mv.x1, mv.y1))
        elif mv.kind == "linear":
            self.machine.fire(move_linear(mv.x1, mv.y1, f))
        else:
            from gcode_parser import arc_points
            for (px, py) in arc_points(mv):
                self.machine.fire(move_linear(px, py, f))

        time.sleep(0.002)