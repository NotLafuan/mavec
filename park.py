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
        move(94, 15, 0)
        time.sleep(2.8)
        move(90, 0, 0)
        time.sleep(1)
        move(70, 15, 1)
        time.sleep(2)
        move(90, 15, 1)
        time.sleep(0.4)
        move(120, 15, 1)
        time.sleep(.7)
        move(70, 15, 0)
        time.sleep(1)
        move(90, 15, 1)
        time.sleep(0.5)
        move(90, 0, 1)
    except KeyboardInterrupt:
        move(90, 0, 1)

ser.close()
