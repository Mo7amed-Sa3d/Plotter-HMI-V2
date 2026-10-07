"""Central configuration for the HMI application."""

from pathlib import Path

# ---- Serial link to Main MCU (UART on GPIO 14/15) ----
SERIAL_PORT = "/dev/ttyAMA0"
SERIAL_BAUD = 115200
SERIAL_TIMEOUT = 30.0

# ---- Files ----
USB_MOUNT_POINTS = ["/media/usb", "/mnt/usb", "/media/pi", "/media/pi/USB"]
JOBS_DIR = Path("/home/pi/hmi_jobs")

# ---- Machine parameters (must match Main MCU) ----
X_MAX_MM = 500.0
Y_MAX_MM = 1000.0
DEFAULT_SPEED = 40.0
DEFAULT_FORCE_A = 200
DEFAULT_FORCE_B = 200

# ---- Registration ----
CAMERA_RESOLUTION = (1280, 720)
MARK_SEARCH_RADIUS_MM = 5.0
REGISTRATION_MARKS = [
    (10.0, 10.0),
    (10.0, 90.0),
    (90.0, 90.0),
    (90.0, 10.0),
]

# ---- Web server ----
WEB_PORT = 5000

# ---- Responsive UI reference ----
REF_WIDTH = 480
REF_HEIGHT = 800

MIN_SCALE = 0.75
MAX_SCALE = 3.0

PORTRAIT_THRESHOLD = 1

# ---- UI ----
FULLSCREEN = True

# ---- Paths ----
BASE_DIR = Path(__file__).resolve().parent