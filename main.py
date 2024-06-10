import cv2
import numpy as np
import matplotlib.pyplot as plt
import time
import serial

cap = cv2.VideoCapture(0)
ser = serial.Serial('/dev/ttyACM0', 56700)
ratio = 0.5
top_crop = 300 # 230

angle = 90
speed = 0


def lerp(a,b,t):
    return a + (b - a) * t

def send_data_normal():
    clamped_angle = int(np.clip(angle, 70, 110))
    clamped_speed = int(np.clip(speed, 0, 255))
    data = b'\x00'*5+b'A' + \
        clamped_angle.to_bytes(1)+clamped_speed.to_bytes(1)+b'B'
    ser.write(data)


def order_points(pts):
    # initialzie a list of coordinates that will be ordered
    # such that the first entry in the list is the top-left,
    # the second entry is the top-right, the third is the
    # bottom-right, and the fourth is the bottom-left
    rect = np.zeros((4, 2), dtype="float32")

    # the top-left point will have the smallest sum, whereas
    # the bottom-right point will have the largest sum
    s = pts.sum(axis=1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]

    # now, compute the difference between the points, the
    # top-right point will have the smallest difference,
    # whereas the bottom-left will have the largest difference
    diff = np.diff(pts, axis=1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]

    # return the ordered coordinates
    return rect


def four_point_transform(image, pts):
    # obtain a consistent order of the points and unpack them
    # individually
    rect = order_points(pts)
    (tl, tr, br, bl) = rect

    # compute the width of the new image, which will be the
    # maximum distance between bottom-right and bottom-left
    # x-coordiates or the top-right and top-left x-coordinates
    widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
    widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
    maxWidth = max(int(widthA), int(widthB))
    # maxWidth = int(widthA) - 500

    # compute the height of the new image, which will be the
    # maximum distance between the top-right and bottom-right
    # y-coordinates or the top-left and bottom-left y-coordinates
    heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
    heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
    maxHeight = max(int(heightA), int(heightB))

    # now that we have the dimensions of the new image, construct
    # the set of destination points to obtain a "birds eye view",
    # (i.e. top-down view) of the image, again specifying points
    # in the top-left, top-right, bottom-right, and bottom-left
    # order
    dst = np.array([
        [0, 0],
        [maxWidth - 1, 0],
        [maxWidth - 1, maxHeight - 1],
        [0, maxHeight - 1]], dtype="float32")

    # compute the perspective transform matrix and then apply it
    M = cv2.getPerspectiveTransform(rect, dst)
    warped = cv2.warpPerspective(image, M, (maxWidth, maxHeight))
    return warped


def image_binary(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur = cv2.blur(gray, (5, 5))
    ret, thresh1 = cv2.threshold(blur, 50, 255, cv2.THRESH_BINARY_INV)

    return thresh1


def map_value(x: float,  in_min: float,  in_max: float,  out_min: float,  out_max: float):
    return (x - in_min) * (out_max - out_min) / (in_max - in_min) + out_min

elapsed_time = 0
while True:
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
    steer_amount = -(cog - (width / 2)) / width
    calc_angle = map_value(steer_amount, -0.4, 0.4, 120, 60)
    angle = lerp(angle, calc_angle, elapsed_time*2)

    speed = map_value(abs(steer_amount), 0, 0.5, 220, 120)

    send_data_normal()

#    cv2.imshow("frame", frame_vis)
 #   cv2.imshow("warped", warped)
  #  cv2.imshow("binary", binary)
   # cv2.imshow("steer", steer)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
    
    elapsed_time = time.time()-start_time
    print(f'\rfps: {1/elapsed_time:>6.2f} _angle: {calc_angle:>5.2f} angle: {angle:>5.2f} speed: {speed:>6.2f}', end='')
print()

cv2.destroyAllWindows()
cap.release()
