import cv2
import numpy as np
import matplotlib.pyplot as plt
import time
import serial
from utils import *
from threading import Thread
import os
from picamera2 import Picamera2
from sense_hat import SenseHat

sense = SenseHat()

# os.environ["OPENCV_LOG_LEVEL"] = "1"

# cap = cv2.VideoCapture(0)
# print('Waiting for camera', end='')
# while not cap.isOpened():
#     cap = cv2.VideoCapture(0)
#     time.sleep(.1)
#     print('.', end='', flush=True)
# print()
ser = serial.Serial('/dev/ttyACM0', 56700)
ratio = 1
top_crop = 400  # 230

angle = 90
speed = 0
angle_pid = PID(kp=0.3,
                # ki=0.005,
                kd=0.2)

max_angle = 90+60+2
min_angle = 90-60+2
max_screen_angle = 0.2


def send_data_normal():
    clamped_angle = int(np.clip(angle, min_angle, max_angle))
    clamped_speed = int(np.clip(speed, 0, 255))
    direction = 0
    clamped_speed = 0
    data = b'\x00'*5+b'A' + \
        clamped_angle.to_bytes(1, 'little') +\
        clamped_speed.to_bytes(1, 'little') + \
        direction.to_bytes(1, 'little')+b'B'
    ser.write(data)


@app.route('/route_frame_vis')
def route_frame_vis():
    def gen_frame_vis():
        global frame_vis
        while True:
            ret, jpeg = cv2.imencode(
                '.jpg', cv2.cvtColor(frame_vis, cv2.COLOR_BGR2RGB))
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n\r\n')
    return Response(gen_frame_vis(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/route_warped')
def route_warped():
    def gen_warped():
        global warped
        while True:
            ret, jpeg = cv2.imencode('.jpg', warped)
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n\r\n')
    return Response(gen_warped(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/route_binary')
def route_binary():
    def gen_binary():
        global binary
        while True:
            ret, jpeg = cv2.imencode('.jpg', binary)
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n\r\n')
    return Response(gen_binary(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/route_steer')
def route_steer():
    def gen_steer():
        global steer
        while True:
            ret, jpeg = cv2.imencode('.jpg', steer)
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n\r\n')
    return Response(gen_steer(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/route_traffic')
def route_traffic():
    def gen_traffic():
        global traffic
        while True:
            ret, jpeg = cv2.imencode(
                '.jpg', cv2.cvtColor(traffic, cv2.COLOR_BGR2RGB))
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n\r\n')
    return Response(gen_traffic(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/route_traffic_max')
def route_traffic_max():
    def gen_traffic_max():
        global traffic_max
        while True:
            ret, jpeg = cv2.imencode('.jpg', traffic_max)
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n\r\n')
    return Response(gen_traffic_max(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@app.route('/data')
def route_data():
    global angle
    global traffic
    B = traffic[:, :, 0]
    G = traffic[:, :, 1]
    R = traffic[:, :, 2]
    return jsonify({'angle': angle,
                    'traffic': [np.mean(R), np.mean(G), np.mean(B)]})


elapsed_time = 0
server = Thread(target=flask_app)
server.daemon = True
server.start()


picam2 = Picamera2()
picam2.start()

while True:
    try:
        start_time = time.time()
        orientation = sense.get_orientation()
        # ret, frame = cap.read()
        frame = picam2.capture_array()
        frame = cv2.flip(frame, 0)
        frame = cv2.flip(frame, 1)
        height, width, channels = frame.shape

        blank_image = np.zeros((height, width+300, 4), np.uint8)
        blank_image.fill(255)
        blank_image[0:height, 150:width+150] = frame
        frame = blank_image
        height, width, channels = blank_image.shape

        pts = np.array([[(width/2)-(width/2)*ratio, top_crop],
                        [(width/2)+(width/2)*ratio, top_crop],
                        [width, height],
                        [0, height]], np.int32)

        frame_vis = frame.copy()
        cv2.polylines(frame_vis, [pts], isClosed=True,
                      color=(0, 0, 125), thickness=3)

        cv2.rectangle(frame_vis, (690, 70), (690+70, 70+170), (0, 0, 125), 2)

        warped = four_point_transform(frame, pts)

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
        error = -(cog - (width / 2)) / width

        angle_pid.value = -error

        angle = map_value(angle_pid.total,
                          -max_screen_angle, max_screen_angle,
                          max_angle, min_angle)
        # angle = lerp(angle, calc_angle, elapsed_time*3)

        speed = map_value(abs(error), 0, max_screen_angle, 20, 13)

        # steepness compensation
        if orientation['roll'] > 180:
            steepness = orientation['roll'] - 360
        else:
            steepness = orientation['roll']
        steepness = steepness/22
        speed = speed + (speed*-steepness*3)

        if abs(steepness) < 1:
            angle = (1-abs(steepness))*angle + (abs(steepness))*90
        else:
            angle = 90

        send_data_normal()

        # cv2.imshow("frame", frame_vis)
        # cv2.imshow("warped", warped)
        # cv2.imshow("binary", binary)
        # cv2.imshow("steer", steer)
        traffic = frame[70:70+170, 690:690+70]
        # traffic_gray = cv2.cvtColor(traffic, cv2.COLOR_BGR2GRAY)
        traffic_gray = cv2.bitwise_not(image_binary(traffic))
        contours, hierarchy = cv2.findContours(
            traffic_gray, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        maxContour = 0
        for contour in contours:
            contourSize = cv2.contourArea(contour)
            if contourSize > maxContour:
                maxContour = contourSize
                maxContourData = contour
        mask = np.zeros_like(traffic_gray)
        cv2.fillPoly(mask, [maxContourData], 1)
        traffic_gray = np.multiply(traffic_gray, mask)

        traffic_hist = np.sum(traffic_gray, axis=1)
        traffic_dist = np.array(range(len(traffic_hist)))
        traffic_cog = np.sum(
            np.matmul(traffic_hist, traffic_dist))/np.sum(traffic_hist)
        if np.isnan(traffic_cog):
            traffic_cog = width/2

        traffic_max = cv2.line(cv2.cvtColor(traffic_gray, cv2.COLOR_GRAY2BGR),
                               (traffic_gray.shape[1], int(traffic_cog)),
                               (traffic_gray.shape[1]-10, int(traffic_cog)),
                               color=(0, 255, 0),
                               thickness=10)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        elapsed_time = time.time()-start_time
        print(f'\rfps: {1/elapsed_time:>6.2f}', end=' ')
        # print(f'_angle: {calc_angle:>6.2f}', end=' ')
        print(f'angle: {angle:>6.2f}', end=' ')
        print(f'speed: {speed:>6.2f}', end=' ',)
        print(f'steepness: {steepness:>6.2f}', end=' ',)
    except KeyboardInterrupt:
        angle = 90
        speed = 0
        send_data_normal()
        cv2.destroyAllWindows()
        break
print()

# cap.release()
