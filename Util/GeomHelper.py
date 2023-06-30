import numpy as np
import math


def calc_line(x1, y1, x2, y2):
    """
    Calculates the slope (a) and y-intercept (b) of a line passing through two points.
    :param x1: First coordinate of the first point
    :param y1: First coordinate of the second point
    :param x2: Second coordinate of the first point
    :param y2: Second coordinate of the second point
    :return: A tuple (a, b) containing the slope and y-intercept of the line.
    """
    a = float(y2 - y1) / (x2 - x1) if x2 != x1 else 0
    b = y1 - a * x1
    return a, b


def calc_line_length(p1, p2):
    """
    Length between two vectors
    :param p1: vector point 1
    :param p2: vector point 2
    :return: length between both points
    """
    dx = p1[0] - p2[0]
    dy = p1[1] - p2[1]
    return math.sqrt(dx * dx + dy * dy)


def get_horz_shift(x, w):
    """
    Calculates the horizontal shift as a percentage based on a given value and width.
    :param x: The value representing the current horizontal position.
    :param w: The total width or range of values.
    :return: The percentage of the horizontal shift, relative to the center of the range.

    """
    hw = w / 2
    return 100 * (x - hw) / hw


def calc_rect_area(rect_points):
    """
    Calculates the area of a rectangle based on the given coordinates of its points.
    :param rect_points: A list of four points defining the rectangle in the following order:
                   [top-left, top-right, bottom-right, bottom-left]
    :return: The area of the rectangle.
    """
    a = calc_line_length(rect_points[0], rect_points[1])
    b = calc_line_length(rect_points[1], rect_points[2])
    return a * b


def get_vert_angle(p1, p2, w, h):
    """
    Calculates the vertical angle between two points in a coordinate system.

    :param p1: The coordinates of the first point as (x1, y1).
    :param p2: The coordinates of the second point as (x2, y2).
    :param w: The total width of the coordinate system.
    :param h: The total height of the coordinate system.
    :return: The vertical angle between the two points in degrees.
    """
    px1 = p1[0] - w / 2
    px2 = p2[0] - w / 2

    py1 = h - p1[1]
    py2 = h - p2[1]

    angle = 90
    if px1 != px2:
        a, b = calc_line(px1, py1, px2, py2)
        angle = 0
        if a != 0:
            x0 = -b / a
            y1 = 1.0
            x1 = (y1 - b) / a
            dx = x1 - x0
            tg = y1 * y1 / dx / dx
            angle = 180 * np.arctan(tg) / np.pi
            if a < 0:
                angle = 180 - angle
    return angle


def order_box(box):
    """
    Reorders the vertices of a box based on their y-coordinate values.

    :param box: box (numpy.ndarray): An array representing the box vertices. Shape: (4, 2)
    :return: An array with the reordered box vertices. Shape: (4, 2)
    """
    srt = np.argsort(box[:, 1])
    btm1 = box[srt[0]]
    btm2 = box[srt[1]]

    top1 = box[srt[2]]
    top2 = box[srt[3]]

    bc = btm1[0] < btm2[0]
    btm_l = btm1 if bc else btm2
    btm_r = btm2 if bc else btm1

    tc = top1[0] < top2[0]
    top_l = top1 if tc else top2
    top_r = top2 if tc else top1

    return np.array([top_l, top_r, btm_r, btm_l])


def shift_box(box, w, h):
    """
    Shifts the vertices of a box by a given width and height.
    :param box: An array representing the box vertices. Shape: (4, 2)
    :param w: The width shift value.
    :param h: The height shift value.
    :return: An array with the shifted box vertices. Shape: (4, 2)
    """
    return np.array([[box[0][0] + w, box[0][1] + h], [box[1][0] + w, box[1][1] + h], [box[2][0] + w, box[2][1] + h],
                     [box[3][0] + w, box[3][1] + h]])


def calc_box_vector(box):
    """
    Calculate a box based on a bunch of vectors

    :param box: vectors that we can calculate the box on
    :return: tuple(float, float) that forms a box
    """
    vertical = calc_line_length(box[0], box[3])
    horizontal = calc_line_length(box[0], box[1])
    indices = [0, 1, 2, 3]
    if vertical < horizontal:
        indices = [0, 3, 1, 2]
    return ((box[indices[0]][0] + box[indices[1]][0]) / 2,
            (box[indices[0]][1] + box[indices[1]][1]) / 2), (
            (box[indices[2]][0] + box[indices[3]][0]) / 2,
            (box[indices[2]][1] + box[indices[3]][1]) / 2)
