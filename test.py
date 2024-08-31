from typing import Any
import cv2
from cv2.typing import MatLike
import numpy as np
import matplotlib.pyplot as plt
import time
import serial
from utils import *
from threading import Thread
import os
from picamera2 import Picamera2
from sense_hat import SenseHat


@dataclass
class Carbot:
    min_angle: float
    max_angle: float
    max_speed: float
    max_screen_angle: float
    PORT: str = '/dev/ttyACM0'
    BAUD: int = 56700
    frame: MatLike = None
    frame_vis: MatLike = None
    binary: MatLike = None
    steer: MatLike = None

    _angle: float = 0
    _speed: float = 0
    _steepness: float = 0

    def __post_init__(self) -> None:
        self.sense = SenseHat()
        self.ser = serial.Serial(self.PORT, self.BAUD)
        self.angle_pid = PID(kp=1.2,
                             # ki=0.005,
                             kd=0.0)

        self.picam2 = Picamera2()
        controls = {"ExposureTime": 30_000, "AnalogueGain": 3.0}
        preview_config = self.picam2.create_preview_configuration(
            controls=controls)
        self.picam2.configure(preview_config)
        self.picam2.start()

        self.frame = self.picam2.capture_array()
        self.frame_vis = self.frame.copy()
        self.binary = self.frame.copy()
        self.steer = self.frame.copy()

        self.height, self.width, channels = self.frame.shape
        self._prev_time = time.time()

    @property
    def orientation(self) -> dict[str, Any] | dict[str, int]:
        return self.sense.get_orientation()

    @property
    def steepness(self) -> float:
        orientation = self.orientation
        if orientation['roll'] > 180:
            self._steepness = orientation['roll'] - 360
        else:
            self._steepness = orientation['roll']
        return self._steepness/self.max_angle

    # @property
    # def calc_angle(self) -> float:
    #     hist = np.sum(self.binary, axis=0)
    #     dist = np.array(range(len(hist)))
    #     cog = np.sum(np.matmul(hist, dist))/np.sum(hist)
    #     if np.isnan(cog):
    #         cog = self.width/2
    #     error = -(cog - (self.width / 2)) / self.width
    #     self.angle_pid.value = -error
    #     return map_value(self.angle_pid.total,
    #                      -self.max_screen_angle, self.max_screen_angle,
    #                      self.max_angle, self.min_angle)

    @property
    def calc_angle(self) -> float:
        pts = np.where(self.binary == 255)
        points = []
        for i in range(self.height):
            # print(i)
            points.append([np.mean(pts[1], where=(pts[0] == i)), i])
        points = np.array(points, dtype=np.int16)
        angles = []
        for i in range(len(points)-1, 0, -1):
            angle = np.arctan2(points[i][1]-points[i-1][1],
                       points[i][0]-points[i-1][0])
            angles.append(np.rad2deg(angle))
        return np.mean(angles)

    @property
    def angle(self) -> float:
        if (steepness := abs(self.steepness)) < 1:
            self._angle = (1-steepness)*self.calc_angle + (steepness)*90
        else:
            self._angle = 90
        return self._angle

    @property
    def speed(self) -> float:
        steepness = self.steepness
        self._speed = map_value(abs(self.angle-90),
                                0, 90,
                                self.max_speed, 13)
        self._speed = self._speed + (self._speed*-steepness*3)
        if abs(steepness) < 0.4:
            self._speed = np.clip(self._speed, 0, self.max_speed)
        return self._speed

    def send_data_normal(self, angle: float = None, speed: float = None) -> bool:
        try:
            if angle is None:
                data_angle = int(np.clip(self.angle,
                                         self.min_angle,
                                         self.max_angle))
            else:
                data_angle = angle
            if speed is None:
                data_speed = int(np.clip(self.speed,
                                         0,
                                         255))
            else:
                data_speed = speed
            direction = 0
            # clamped_speed = 0
            data = b'\x00'*5+b'A' + \
                data_angle.to_bytes(1, 'little') +\
                data_speed.to_bytes(1, 'little') + \
                direction.to_bytes(1, 'little')+b'B'
            # self.ser.write(data)
            return True
        except Exception:
            return False

    @property
    def fps(self) -> float:
        elapsed_time = time.time() - self._prev_time
        fps = 1/elapsed_time
        self._prev_time = time.time()
        return fps

    def print_data(self) -> None:
        print(f'\rfps: {self.fps:>6.2f}', end=' ')
        print(f'angle: {self._angle:>6.2f}', end=' ')
        print(f'speed: {self._speed:>6.2f}', end=' ',)
        print(f'steepness: {self._steepness:>6.2f}', end=' ',)

    def update(self) -> bool:
        try:
            self.frame = self.picam2.capture_array()
            self.frame = cv2.flip(self.frame, 0)
            self.frame = cv2.flip(self.frame, 1)

            self.frame_vis = self.frame.copy()

            self.binary = image_binary(self.frame)
            self.steer = self.binary
            self.print_data()
            if not self.send_data_normal():
                return False
            return True
        except KeyboardInterrupt:
            self.send_data_normal(angle=90, speed=0)
            return False


@app.route('/route_frame_vis')
def route_frame_vis():
    def gen_frame_vis():
        global carbot
        while True:
            ret, jpeg = cv2.imencode(
                '.jpg', cv2.cvtColor(carbot.frame_vis, cv2.COLOR_BGR2RGB))
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n\r\n')
    return Response(gen_frame_vis(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/route_steer')
def route_steer():
    def gen_steer():
        global carbot
        while True:
            ret, jpeg = cv2.imencode('.jpg', carbot.steer)
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n\r\n')
    return Response(gen_steer(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


elapsed_time = 0
server = Thread(target=flask_app)
server.daemon = True
server.start()

carbot = Carbot(min_angle=90-60+2,
                max_angle=90+60+2,
                max_speed=20,
                max_screen_angle=0.4)

while True:
    if not carbot.update():
        break
print()
