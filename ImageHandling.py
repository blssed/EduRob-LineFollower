import cv2 as cv
import numpy as np
import GeomHelper as geom
import ROI
import config as conf

Roi = ROI.ROI()

imgWritecounter = 0


def write_img(image, name):
    global imgWritecounter
    if imgWritecounter % 30 == 0:
        imgWritecounter = 0
        written = cv.imwrite("/linefollower" + name + ".jpeg", image)
        if written:
            print("Wrote image")
        else:
            print("Error writing image")


def balance_pic(image):
    global T
    ret = None
    direction = 0
    for i in range(0, conf.iterations):

        rc, gray = cv.threshold(image, T, 255, 0)
        crop = Roi.crop_roi(gray)

        non_white = cv.countNonZero(crop)
        perc = int(100 * non_white / Roi.get_area())

        if perc > conf.maxWhite:
            if T > conf.maxThreshold:
                break
            if direction == -1:
                ret = crop
                break
            T += 10
            direction = 1
        elif perc < conf.minWhite:
            if T < conf.minThreshold:
                break
            if direction == 1:
                ret = crop
                break

            T -= 10
            direction = -1
        else:
            ret = crop
            break
    return ret


def adjust_brightness(img, level):
    hsv = cv.cvtColor(img, cv.COLOR_BGR2HSV)
    b = np.mean(img[:, :, 2])
    if b == 0:
        return img
    r = level / b
    c = img.copy()
    c[:, :, 2] = c[:, :, 2] * r
    return cv.cvtColor(c, cv.COLOR_HSV2BGR)


def prepare_pic(image):
    global Roi
    global T
    height, width = image.shape[:2]

    gray = cv.cvtColor(image, cv.COLOR_BGR2GRAY)
    blurred = cv.GaussianBlur(gray, (9, 9), 0)

    write_img(blurred, "grayed")

    if Roi.get_area() == 0:
        Roi.init_roi(width, height)

    return balance_pic(blurred), width, height


def find_main_countour(image):
    im2, cnts, hierarchy = cv.findContours(image, cv.RETR_CCOMP, cv.CHAIN_APPROX_SIMPLE)
    contour = None
    if cnts is not None and len(cnts) > 0:
        contour = max(cnts, key=cv.contourArea)

    if contour is None:
        return None, None

    rect = cv.minAreaRect(contour)
    box = cv.boxPoints(rect)
    box = np.int0(box)
    box = geom.order_box(box)
    return contour, box


def handle_pic(image):
    global imgWritecounter
    write_img(image, "unhandled")
    imgWritecounter += 1
    if image is None:
        print("Image is empty")
        return None, None
    cropped, w, h = prepare_pic(image)
    write_img(cropped, "cropped")
    if cropped is None:
        return None, None
    cont, box = find_main_countour(cropped)
    if cont is None:
        return None, None

    p1, p2 = geom.calc_box_vector(box)
    if p1 is None:
        return None, None

    angle = geom.get_vert_angle(p1, p2, w, h)
    shift = geom.get_horz_shift(p1[0], w)

    cv.drawContours(image, [cont], -1, (0, 0, 255), 3)
    cv.drawContours(image, [box], 0, (255, 0, 0), 2)
    cv.line(image, p1, p2, (0, 255, 0), 3)
    msg_a = "Angle {0}".format(int(angle))
    msg_s = "Shift {0}".format(int(shift))

    cv.putText(image, msg_a, (10, 20), cv.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    cv.putText(image, msg_s, (10, 40), cv.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    write_img(image, "detailed")

    return angle, shift
