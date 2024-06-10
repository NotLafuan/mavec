import serial

ser = serial.Serial('/dev/ttyACM0', 56700)

angle = 90
speed = 0
direction = 0
print('start')
data = b'\x00'*5+b'A'+angle.to_bytes(1, 'big')+speed.to_bytes(1, 'big')+direction.to_bytes(1, 'big')+b'B'
ser.write(data)
print('finished')

ser.close()

