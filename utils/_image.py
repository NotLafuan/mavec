import cv2
import numpy as np


def order_points(pts):
    # initialzie a list of coordinates that will be ordered
    # such that the first entry in the list is the top-left,
    # the second entry is the top-right, the third is the
    # bottom-right, and the fourth is the bottom-left
    rect = np.zeros((4, 2), dtype="float32")

    # the top-left point will have the smallest sum, whereas
    # the bottom-right point will have the largest sum
    s = pts.sum(axis=1)
    # rect[0] = pts[np.argmin(s)]
    # rect[2] = pts[np.argmax(s)]

    # now, compute the difference between the points, the
    # top-right point will have the smallest difference,
    # whereas the bottom-left will have the largest difference
    diff = np.diff(pts, axis=1)
    # rect[1] = pts[np.argmin(diff)]
    # rect[3] = pts[np.argmax(diff)]

    # return the ordered coordinates
    rect[0] = pts[0]
    rect[1] = pts[1]
    rect[2] = pts[2]
    rect[3] = pts[3]
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


def scale_contour(cnts, scale):
    new_cnts = []
    for cnt in cnts:
        M = cv2.moments(cnt)
        try:
            cx = int(M['m10']/M['m00'])
        except ZeroDivisionError:
            cx = 0
        try:
            cy = int(M['m01']/M['m00'])
        except ZeroDivisionError:
            cy = 0

        cnt_norm = cnt - [cx, cy]
        cnt_scaled = cnt_norm * scale
        cnt_scaled = cnt_scaled + [cx, cy]
        cnt_scaled = cnt_scaled.astype(np.int32)
        new_cnts.append(cnt_scaled)
    return new_cnts


def image_binary(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur = cv2.blur(gray, (10, 10))
    ret, thresh1 = cv2.threshold(blur,  70, 255, cv2.THRESH_BINARY_INV)
    edge = cv2.Canny(thresh1, 100, 200, 3)
    contours, hierarchy = cv2.findContours(edge,
                                           cv2.RETR_TREE,
                                           cv2.CHAIN_APPROX_SIMPLE)
    scale_cnts = scale_contour(contours, 20)

    # thresh1 = cv2.cvtColor(thresh1, cv2.COLOR_GRAY2BGR)
    for contour, scale_cnt in zip(contours, scale_cnts):
        mask = np.zeros_like(thresh1)
        cv2.fillPoly(mask, pts=[scale_cnt], color=255)
        cv2.fillPoly(mask, pts=[contour], color=0)
        average = cv2.mean(thresh1, mask=mask)[0]
        color = 0 if average < 255/2 else 255
        cv2.fillPoly(thresh1, pts=[contour], color=int(color))

    return thresh1
