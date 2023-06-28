import cv2 as cv
import numpy as np
from Util import GeomHelper as geom, ROI, config as conf

Roi = ROI.ROI()

imgWritecounter = 0


def write_img(image, name):
    """
    Writes an image to disk with a given name.
    :param image: An array representing the image.
    :param name: The name of the image file.
    :return: none
    """
    global imgWritecounter
    if imgWritecounter % 30 == 0:
        imgWritecounter = 0
        if image is not None:
            cv.imwrite("/linefollower/" + name + ".jpeg", image)
        else:
            print("Error writing image")


def balance_pic(image):
    """
    Balances the picture by adjusting the threshold value to optimize the percentage of white pixels.
    :param image: An array representing the input image.
    :return: The processed image after balancing or None if no balance is achieved.
    """
    threshold = conf.threshold
    processed_image = None
    direction = 0

    for i in range(conf.iterations):
        i, gray = cv.threshold(image, threshold, 255, 0)
        crop = Roi.crop_roi(gray)

        non_white = cv.countNonZero(crop)
        percentage_white = int(100 * non_white / Roi.get_area())

        if percentage_white > conf.maxWhite:
            if threshold > conf.maxThreshold:
                break
            if direction == -1:
                processed_image = crop
                break
            threshold += 10
            direction = 1
        elif percentage_white < conf.minWhite:
            if threshold < conf.minThreshold:
                break
            if direction == 1:
                processed_image = crop
                break
            threshold -= 10
            direction = -1
        else:
            processed_image = crop
            break

    return processed_image


def prepare_pic(image):
    """
    Prepares the input image by converting it to grayscale, applying Gaussian blur, and performing image balancing.
    :param image: An array representing the input image.
    :return: A tuple containing the processed image after balancing (or None if no balance is achieved), width, and height of the image.
    """
    global Roi
    height, width = image.shape[:2]

    # gray and blurr chained
    blurred = cv.GaussianBlur(cv.cvtColor(image, cv.COLOR_BGR2GRAY), (9, 9), 0)

    write_img(blurred, "grayed")

    if Roi.get_area() == 0:
        Roi.init_roi(width, height)

    return balance_pic(blurred), width, height


def find_main_countour(image):
    """
    Finds the main contour in the input image and returns the contour and the ordered bounding box.
    :param image: An array representing the input image.
    :return:  A tuple containing the main contour (or None if not found)
        and the ordered bounding box (or None if contour is None).
    """
    conts, hierarchy = cv.findContours(image, cv.RETR_CCOMP, cv.CHAIN_APPROX_SIMPLE)
    contour = None
    if conts is not None and len(conts) > 0:
        contour = max(conts, key=cv.contourArea)

    if contour is None:
        return None, None

    rect = cv.minAreaRect(contour)
    box = cv.boxPoints(rect)
    box = np.int0(box)
    box = geom.order_box(box)
    return contour, box


def handle_pic(image):
    """
    Handles the input image by performing various operations, including writing images, cropping, finding contours,
    calculating angles and shifts, and drawing visualizations.
    :param image: An array representing the input image.
    :return: A tuple containing the calculated angle (or None if not available)
        and the calculated shift (or None if not available).
    """
    global imgWritecounter
    imgWritecounter += 1
    write_img(image, "unhandled")
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
    ip1 = *[int(_) for _ in p1],
    ip2 = *[int(_) for _ in p2],
    cv.line(image, ip1, ip2, (0, 255, 0), 3)
    msg_a = "Angle {0}".format(int(angle))
    msg_s = "Shift {0}".format(int(shift))

    cv.putText(image, msg_a, (10, 20), cv.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    cv.putText(image, msg_s, (10, 40), cv.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    write_img(image, "detailed")

    return angle, shift
