import serial
import time


ser = serial.Serial('/dev/ttyACM0', 56700)


def move(angle: int, speed: int, dir: int):
    data = b'\x00'*5+b'A' + \
        angle.to_bytes(1, 'big')+speed.to_bytes(1, 'big') + \
        dir.to_bytes(1, 'big')+b'B'
    ser.write(data)


if __name__ == '__main__':
    move(93, 15, 1)
    time.sleep(2)
    move(95, 15, 1)
    time.sleep(2)
    move(90, 0, 0)
ser.close()
