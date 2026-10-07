"""Registration mark detection and rigid-transform computation."""

import math
from dataclasses import dataclass
from typing import List, Optional, Tuple

import cv2
import numpy as np

from config import CAMERA_RESOLUTION


@dataclass
class Transform:
    """2x3 affine transform: [x'] = [a b tx][x]
                            [y']   [c d ty][y]"""
    a: float = 1.0; b: float = 0.0; tx: float = 0.0
    c: float = 0.0; d: float = 1.0; ty: float = 0.0

    def apply(self, x: float, y: float) -> Tuple[float, float]:
        return (self.a * x + self.b * y + self.tx,
                self.c * x + self.d * y + self.ty)


def capture_image(camera, timeout=3.0):
    import time
    time.sleep(0.3)
    array = camera.capture_array()
    return array


def find_mark(image: np.ndarray,
              expected_x_px: float, expected_y_px: float,
              search_radius_px: int = 80) -> Optional[Tuple[float, float]]:
    h, w = image.shape[:2]

    x0 = max(0, int(expected_x_px - search_radius_px))
    x1 = min(w, int(expected_x_px + search_radius_px))
    y0 = max(0, int(expected_y_px - search_radius_px))
    y1 = min(h, int(expected_y_px + search_radius_px))
    if x1 <= x0 or y1 <= y0:
        return None

    roi = image[y0:y1, x0:x1]
    if roi.ndim == 3:
        gray = cv2.cvtColor(roi, cv2.COLOR_RGB2GRAY)
    else:
        gray = roi

    _, thresh = cv2.threshold(gray, 0, 255,
                              cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL,
                                   cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return None

    largest = max(contours, key=cv2.contourArea)
    if cv2.contourArea(largest) < 10:
        return None

    M = cv2.moments(largest)
    if M["m00"] < 1e-6:
        return None
    cx = x0 + M["m10"] / M["m00"]
    cy = y0 + M["m01"] / M["m00"]
    return cx, cy


def compute_transform(nominal: List[Tuple[float, float]],
                      measured: List[Tuple[float, float]]) -> Transform:
    src = np.array(nominal, dtype=np.float64)
    dst = np.array(measured, dtype=np.float64)

    src_mean = src.mean(axis=0)
    dst_mean = dst.mean(axis=0)

    src_c = src - src_mean
    dst_c = dst - dst_mean

    H = src_c.T @ dst_c

    U, _, Vt = np.linalg.svd(H)
    R = Vt.T @ U.T
    if np.linalg.det(R) < 0:
        Vt[-1, :] *= -1
        R = Vt.T @ U.T

    t = dst_mean - R @ src_mean

    return Transform(
        a=R[0, 0], b=R[0, 1], tx=t[0],
        c=R[1, 0], d=R[1, 1], ty=t[1],
    )