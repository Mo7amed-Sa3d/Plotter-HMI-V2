"""Flask HTTP server providing a remote UI."""

import json
import threading
from pathlib import Path

from flask import Flask, Response, jsonify, request, send_from_directory

from config import WEB_PORT
from machine import Machine
from job import Job, JobState
from protocol import (home_x, move_linear, move_rapid, zero_x, zero_y,
                      set_pwm, pwm_off, feed, auto_feed, eject_paper, stop)

WEB_ROOT = Path(__file__).parent / "web"


def create_app(machine: Machine, job: Job):
    app = Flask(__name__, static_folder=None)

    @app.route("/")
    def index():
        return send_from_directory(WEB_ROOT, "index.html")

    @app.route("/<path:path>")
    def static_files(path):
        return send_from_directory(WEB_ROOT, path)

    @app.route("/api/status")
    def status():
        p = machine.position
        s = machine.sensors
        return jsonify({
            "position": None if not p else {
                "x": p.x, "y": p.y, "f": p.f, "qx": p.qx, "qy": p.qy,
                "homed": p.homed,
            },
            "sensors": None if not s else {
                "s1": s.s1, "s2": s.s2, "s3": s.s3, "x_limit": s.x_limit,
            },
            "job": {
                "state": job.state.name,
                "progress": job.progress,
                "file": job.path,
                "speed": job.speed_override,
                "force_a": job.force_a,
                "force_b": job.force_b,
            },
        })

    @app.route("/api/command", methods=["POST"])
    def command():
        data = request.get_json(force=True)
        cmd = data.get("cmd")
        if cmd == "home":
            machine.command(home_x())
        elif cmd == "zero":
            machine.command(zero_x(0.0))
            machine.command(zero_y(0.0))
        elif cmd == "jog":
            machine.fire(move_linear(data["x"], data["y"], data.get("f", 40)))
        elif cmd == "stop":
            machine.fire(stop())
        elif cmd == "force":
            job.set_force(data["channel"], data["duty"])
        elif cmd == "speed":
            job.set_speed(data["value"])
        elif cmd == "feed":
            machine.fire(feed(data["mm"], data.get("f", 20)))
        elif cmd == "auto_feed":
            machine.fire(auto_feed())
        elif cmd == "eject":
            machine.fire(eject_paper())
        elif cmd == "pause":
            job.pause()
        elif cmd == "resume":
            job.resume()
        elif cmd == "cancel":
            job.cancel()
        elif cmd == "start":
            job.start(data["path"])
        else:
            return jsonify({"error": "unknown command"}), 400
        return jsonify({"ok": True})

    @app.route("/api/files")
    def files():
        from config import USB_MOUNT_POINTS
        out = []
        for mp in USB_MOUNT_POINTS:
            p = Path(mp)
            if p.exists():
                for f in p.rglob("*.gcode"):
                    out.append(str(f))
                for f in p.rglob("*.nc"):
                    out.append(str(f))
        return jsonify(out)

    return app


def start_server(machine: Machine, job: Job):
    app = create_app(machine, job)
    t = threading.Thread(
        target=lambda: app.run(host="0.0.0.0", port=WEB_PORT,
                               debug=False, use_reloader=False),
        daemon=True)
    t.start()
    return t