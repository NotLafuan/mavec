import cv2
import numpy as np
import matplotlib.pyplot as plt
import time
import serial
from utils import *
from threading import Thread

cap = cv2.VideoCapture(0)
print('Waiting for camera', end='')
while not cap.isOpened():
    time.sleep(.5)
    print('.', end='')
print()
# ser = serial.Serial('/dev/ttyACM0', 56700)
ratio = 0.5
top_crop = 300  # 230

angle = 90
speed = 0


def send_data_normal():
    clamped_angle = int(np.clip(angle, 70, 110))
    clamped_speed = int(np.clip(speed, 0, 255))
    data = b'\x00'*5+b'A' + \
        clamped_angle.to_bytes(1, 'big')+clamped_speed.to_bytes(1, 'big')+b'B'
    # ser.write(data)


def gen_frame_vis():
    global frame_vis
    while True:
        ret, jpeg = cv2.imencode('.jpg', frame_vis)
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n\r\n')


@app.route('/route_frame_vis')
def route_frame_vis():
    return Response(gen_frame_vis(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

def gen_warped():
    global warped
    while True:
        ret, jpeg = cv2.imencode('.jpg', warped)
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n\r\n')


@app.route('/route_warped')
def route_warped():
    return Response(gen_warped(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

def gen_binary():
    global binary
    while True:
        ret, jpeg = cv2.imencode('.jpg', binary)
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n\r\n')


@app.route('/route_binary')
def route_binary():
    return Response(gen_binary(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

def gen_steer():
    global steer
    while True:
        ret, jpeg = cv2.imencode('.jpg', steer)
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n\r\n')


@app.route('/route_steer')
def route_steer():
    return Response(gen_steer(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


elapsed_time = 0
server = Thread(target=flask_app)
server.daemon = True
server.start()

while True:
    global frame
    try:
        start_time = time.time()
        ret, frame = cap.read()
        frame = cv2.flip(frame, 0)
        frame = cv2.flip(frame, 1)

        height, width, channels = frame.shape
        pts = np.array([[(width/2)-(width/2)*ratio, top_crop],
                        [(width/2)+(width/2)*ratio, top_crop],
                        [width, height],
                        [0, height]], np.int32)

        frame_vis = frame.copy()
        cv2.polylines(frame_vis, [pts], isClosed=True,
                      color=(0, 0, 125), thickness=3)

        warped = four_point_transform(frame_vis, pts)

        binary = image_binary(warped)

        hist = np.sum(binary, axis=0)
        dist = np.array(range(len(hist)))
        cog = np.sum(np.matmul(hist, dist))/np.sum(hist)
        if np.isnan(cog):
            cog = width/2
        # fig, ax = plt.subplots()
        # ax.plot(hist)
        # fig.canvas.draw()
        # img_plot = np.array(fig.canvas.renderer.buffer_rgba())

        # cv2.imshow("histogram", cv2.cvtColor(img_plot, cv2.COLOR_RGBA2BGR))
        steer = cv2.line(cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR),
                         (int(cog), binary.shape[0]),
                         (int(cog), binary.shape[0]-10),
                         color=(0, 255, 0),
                         thickness=10)
        steer_amount = -(cog - (width / 2)) / width
        calc_angle = map_value(steer_amount, -0.4, 0.4, 120, 60)
        angle = lerp(angle, calc_angle, elapsed_time*2)

        speed = map_value(abs(steer_amount), 0, 0.5, 220, 120)

        send_data_normal()

    #    cv2.imshow("frame", frame_vis)
    #    cv2.imshow("warped", warped)
    #    cv2.imshow("binary", binary)
    #    cv2.imshow("steer", steer)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        elapsed_time = time.time()-start_time
        print(f'\rfps: {1/elapsed_time:>6.2f}', end=' ')
        print(f'_angle: {calc_angle:>5.2f}', end=' ')
        print(f'angle: {angle:>5.2f}', end=' ')
        print(f'speed: {speed:>6.2f}', end=' ',)
    except KeyboardInterrupt:
        break
print()

cv2.destroyAllWindows()
cap.release()
