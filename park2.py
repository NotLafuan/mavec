import serial
import time


ser = serial.Serial('/dev/ttyACM0', 56700)


def move(angle: int, speed: int, dir: int):
    data = b'\x00'*5+b'A' + \
        angle.to_bytes(1, 'big')+speed.to_bytes(1, 'big') + \
        dir.to_bytes(1, 'big')+b'B'
    ser.write(data)


if __name__ == '__main__':
    try:
        move(93, 15, 0)
        time.sleep(1.6)
        move(95, 15, 0)
        time.sleep(1.8)
        move(120, 15, 0)
        time.sleep(1.4)
        move(93, 15, 0)
        time.sleep(0.8)
        move(120, 15, 0)
        time.sleep(1.2)
        move(93, 15, 1)
        time.sleep(0.5)
        move(90, 0, 1)
    except KeyboardInterrupt:
        move(90, 0, 1)

ser.close()
