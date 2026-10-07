"""Threaded serial client for the Main MCU.

Design notes
------------
* One thread reads the serial port: the RX loop. It splits incoming
  bytes into lines and dispatches them to listeners and to a response
  queue.
* command() sends one line and waits on the response queue for the
  final ok / error reply. It never reads the port directly.
* An outstanding-command counter tracks how many commands have been
  sent but not yet acknowledged. Before a blocking command is issued,
  wait_drain() blocks until the counter reaches zero, so no stale ok
  from a previous burst can be misread as the reply to the new one.
* error:unknown_command lines are dropped on arrival. The HMI only
  ever sends commands the firmware recognizes, so such a line cannot
  be a reply to anything the HMI sent. It is produced by the ESP32
  when it hears garbage on its RX pin. Dropping it keeps the
  outstanding counter in sync with the real command stream.
"""

import threading
import time
from collections import deque
from typing import Callable, Optional

import serial

from config import SERIAL_PORT, SERIAL_BAUD
from protocol import (
    parse_position, parse_sensors, Position, Sensors,
    get_position, get_sensors,
)


COMMAND_TIMEOUT = 15.0
READ_TIMEOUT = 0.05
RESPONSE_QUEUE_MAX = 512
DRAIN_TIMEOUT = 8.0


class Machine:
    def __init__(self, dispatch: Callable[[Callable], None]):
        self.dispatch = dispatch

        self._ser: Optional[serial.Serial] = None
        self._lock = threading.RLock()
        self._rx_thread: Optional[threading.Thread] = None
        self._stop = threading.Event()

        self.position: Optional[Position] = None
        self.sensors: Optional[Sensors] = None
        self.alarm = False

        self._response_q: deque[str] = deque(maxlen=RESPONSE_QUEUE_MAX)
        self._response_event = threading.Event()

        self._command_lock = threading.Lock()

        self._outstanding = 0
        self._outstanding_lock = threading.Lock()
        self._outstanding_event = threading.Event()

        self._position_listeners: list[Callable[[Position], None]] = []
        self._sensor_listeners:   list[Callable[[Sensors], None]] = []

    # ---- Lifecycle ----

    def open(self):
        try:
            self._ser = serial.Serial(
                port=SERIAL_PORT,
                baudrate=SERIAL_BAUD,
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=READ_TIMEOUT,
            )
        except serial.SerialException as exc:
            raise RuntimeError(f"Cannot open {SERIAL_PORT}: {exc}")

        self._stop.clear()
        self._rx_thread = threading.Thread(target=self._rx_loop, daemon=True)
        self._rx_thread.start()

        deadline = time.time() + 8.0
        while time.time() < deadline:
            self.fire(get_position())
            time.sleep(0.25)
            if self.position is not None:
                break

        with self._outstanding_lock:
            self._outstanding = 0
            self._outstanding_event.set()

        self.fire(get_sensors())

    def close(self):
        self._stop.set()
        if self._ser and self._ser.is_open:
            try:
                self._ser.close()
            except Exception:
                pass

    def is_open(self) -> bool:
        return self._ser is not None and self._ser.is_open

    # ---- Listener registration ----

    def on_position(self, cb: Callable[[Position], None]):
        self._position_listeners.append(cb)

    def on_sensors(self, cb: Callable[[Sensors], None]):
        self._sensor_listeners.append(cb)

    # ---- Sending ----

    def _send(self, cmd: str):
        if not self._ser or not self._ser.is_open:
            return
        with self._lock:
            try:
                self._ser.write((cmd + "\n").encode("ascii"))
                self._ser.flush()
            except serial.SerialException:
                return

        with self._outstanding_lock:
            self._outstanding += 1
            self._outstanding_event.clear()

    def fire(self, cmd: str):
        self._send(cmd)

    def outstanding(self) -> int:
        with self._outstanding_lock:
            return self._outstanding

    def wait_drain(self, timeout: float = DRAIN_TIMEOUT) -> bool:
        deadline = time.time() + timeout
        while time.time() < deadline:
            with self._outstanding_lock:
                if self._outstanding == 0:
                    return True
            self._outstanding_event.wait(timeout=0.05)

        with self._outstanding_lock:
            self._outstanding = 0
            self._outstanding_event.set()
        with self._lock:
            self._response_q.clear()
            self._response_event.clear()
        return False

    # ---- Blocking command ----

    def command(self, cmd: str, wait_ok: bool = True,
                timeout: float = COMMAND_TIMEOUT) -> bool:
        with self._command_lock:
            self.wait_drain(timeout=DRAIN_TIMEOUT)

            with self._lock:
                self._response_q.clear()
                self._response_event.clear()

            self._send(cmd)

            if not wait_ok:
                return True

            deadline = time.time() + timeout
            while time.time() < deadline:
                line = self._pop_response(deadline)
                if line is None:
                    continue
                if line == "ok":
                    return True
                if line.startswith("error:"):
                    self.alarm = True
                    return False
            return False

    def _pop_response(self, deadline: float) -> Optional[str]:
        with self._lock:
            if self._response_q:
                return self._response_q.popleft()
        remaining = deadline - time.time()
        if remaining <= 0:
            return None
        self._response_event.wait(timeout=min(0.05, remaining))
        with self._lock:
            self._response_event.clear()
            if self._response_q:
                return self._response_q.popleft()
        return None

    # ---- Receiving ----

    def _rx_loop(self):
        buf = b""
        while not self._stop.is_set():
            try:
                chunk = self._ser.read(256)
            except serial.SerialException:
                time.sleep(0.1)
                continue

            if not chunk:
                continue

            buf += chunk
            while b"\n" in buf:
                raw, buf = buf.split(b"\n", 1)
                line = raw.decode("ascii", errors="replace").strip("\r")
                if line:
                    self._process_line(line)

    def _process_line(self, line: str):
        if line == "error:unknown_command":
            return

        if line == "ok" or line.startswith("error:"):
            with self._outstanding_lock:
                if self._outstanding > 0:
                    self._outstanding -= 1
                if self._outstanding == 0:
                    self._outstanding_event.set()

        pos = parse_position(line)
        if pos is not None:
            self.position = pos
            for cb in self._position_listeners:
                self.dispatch(lambda c=cb, p=pos: c(p))

        sen = parse_sensors(line)
        if sen is not None:
            self.sensors = sen
            for cb in self._sensor_listeners:
                self.dispatch(lambda c=cb, s=sen: c(s))

        if line.startswith("error:"):
            self.alarm = True

        with self._lock:
            self._response_q.append(line)
            self._response_event.set()

    # ---- Convenience ----

    def refresh_status(self):
        self.fire(get_position())
        self.fire(get_sensors())