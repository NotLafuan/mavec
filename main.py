from typing import Any
import cv2
from cv2.typing import MatLike
import numpy as np
import time
import serial
from utils import *
from threading import Thread
from picamera2 import Picamera2
from sense_hat import SenseHat


@dataclass
class Carbot:
    min_angle: float
    max_angle: float
    max_speed: float
    max_screen_angle: float
    max_steep: float
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
        self.angle_pid = PID(kp=1,
                             ki=0.00,
                             kd=0.00)
        self.angle_pid.target = 0

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

        self._x_coords_plate = np.repeat([np.arange(self.width)],
                                         repeats=self.height,
                                         axis=0)

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
        self._steepness = self._steepness/self.max_steep
        return self._steepness

    @property
    def calc_angle(self) -> float:
        if not np.mean(self.binary):
            return self._angle
        masked = cv2.bitwise_and(self._x_coords_plate,
                                 self._x_coords_plate, mask=self.binary)
        means = np.mean(masked, axis=1, where=(masked != 0))
        means = np.nan_to_num(means)
        average = np.mean(means[means != 0])

        self.angle_pid.value = -map_value(average,
                                          0, self.width,
                                          self.min_angle, self.max_angle)
        return self.angle_pid.total

    @property
    def angle(self) -> float:
        steepness = abs(self.steepness)
        self._angle = (1-steepness)*self.calc_angle + (steepness)*90
        return self._angle

    @property
    def speed(self) -> float:
        steepness = self.steepness
        self._speed = map_value(abs(self.angle-90),
                                0, 90,
                                self.max_speed, 13)
        self._speed = self._speed + (self._speed*-steepness)
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
            # data_speed = 0
            data = b'\x00'*5+b'A' + \
                data_angle.to_bytes(1, 'little') +\
                data_speed.to_bytes(1, 'little') + \
                direction.to_bytes(1, 'little')+b'B'
            self.ser.write(data)
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

carbot = Carbot(min_angle=90-60-2,
                max_angle=90+60-2,
                max_speed=20,
                max_screen_angle=0.4,
                max_steep=10)

while True:
    if not carbot.update():
        break
print()
