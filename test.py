import serial
import threading
import time


ser = serial.Serial('/dev/ttyACM0', 56700)
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
thread1 = threading.Thread(target=print_numbers)

# Start the threads
print('Thread started')
thread1.start()

print('Waiting 1 second...')
time.sleep(1)
angle = 70
speed = 44
for i in range(5):
    ser.write(b'\x00')
print('start')
ser.write(b'A')
ser.write(angle.to_bytes(1))
ser.write(speed.to_bytes(1))
ser.write(b'B')
time.sleep(0.5)
print('finished')

# Wait for the threads to finish
stop_thread = True
for i in range(5):
    time.sleep(1)
    ser.write(b'\x00')
thread1.join()
ser.close()
print("Both threads have finished execution.")
