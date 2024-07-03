import serial
import time

ser = serial.Serial('/dev/ttyACM0', 57600)
stop_thread = False

# Define a function to be executed in a separate thread


def print_numbers():
    global stop_thread, ser
    text = ''
    while not stop_thread:
        data = ser.read().decode()
        if data != '\n':
            text += data
            continue
        print(text)
        text = ''


# Create threads for each function
# thread1 = threading.Thread(target=print_numbers)

# Start the threads
print('Thread started')
# thread1.start()

print('Waiting 1 second...')
time.sleep(1)
angle = 90
speed = 0
direction = 1
print('start')
# ser.write(b'A')
# ser.write(angle.to_bytes(1))
# ser.write(speed.to_bytes(1))
# ser.write(b'B')
data = b'\x00'*5+b'A' + \
    angle.to_bytes(1, 'big') +\
    speed.to_bytes(1, 'big') + \
    direction.to_bytes(1, 'big')+b'B'
ser.write(data)
time.sleep(0.5)
print('finished')

# Wait for the threads to finish
stop_thread = True
for i in range(5):
    time.sleep(0.3)
    ser.write(b'AAAA')
# thread1.join()
ser.close()
print("Both threads have finished execution.")
