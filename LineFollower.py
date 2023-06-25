import ImageHandling as imgHandler
import time
import numpy as np
import cv2 as cv
import config as conf
from http.server import HTTPServer, SimpleHTTPRequestHandler
from multiprocessing import Process


def gstreamer_pipeline(
        capture_width=1920,
        capture_height=1080,
        display_width=820,
        display_height=616,
        framerate=21,
        flip_method=2,
):
    return (
            "nvarguscamerasrc ! "
            "video/x-raw(memory:NVMM), "
            "width=(int)%d, height=(int)%d, "
            "format=(string)NV12, framerate=(fraction)%d/1 ! "
            "nvvidconv flip-method=%d ! "
            "video/x-raw, width=(int)%d, height=(int)%d, format=(string)BGRx ! "
            "videoconvert ! "
            "video/x-raw, format=(string)BGR ! appsink"
            % (
                capture_width,
                capture_height,
                framerate,
                flip_method,
                display_width,
                display_height,
            )
    )


def process_camera_input():
    cap = cv.VideoCapture(gstreamer_pipeline(), cv.CAP_GSTREAMER)
    while cap.isOpened():
        ret, img = cap.read()
        follow(img)
        print("Handling image")


def start_server():
    httpd.serve_forever()
    print("Server started")


def find_line(side):
    print("Finding line")
    if side == 0:
        return None, None

    for i in range(0, conf.findTurnAttempts):
        turn(side, conf.findTurnStep)
        angle, shift = imgHandler.handle_pic()
        if angle is not None:
            return angle, shift

    return None, None


def turn(r, t):
    print("Turning, r: " + r + " t: " + t)
    # todo: do a turn based on r and t


def check_shift_turn(angle, shift):
    turn_state = 0
    if angle < conf.turnAngle or angle > 180 - conf.turnAngle:
        turn_state = np.sign(90 - angle)

    shift_state = 0
    if abs(shift) > conf.maxShift:
        shift_state = np.sign(shift)
    return turn_state, shift_state


def get_turn(turn_state, shift_state):
    turn_dir = 0
    turn_val = 0
    if shift_state != 0:
        turn_dir = shift_state
        turn_val = conf.shiftStep if shift_state != turn_state else conf.turnStep
    elif turn_state != 0:
        turn_dir = turn_state
        turn_val = conf.turnStep
    return turn_dir, turn_val


def follow(image):
    # todo: drive forward
    print("Driving forward")

    try:
        last_turn = 0
        last_angle = 0

        for i in range(0, conf.iterations):
            a, shift = imgHandler.handle_pic(image)
            if a is None:
                if last_turn != 0:
                    a, shift = find_line(last_turn)
                    if a is None:
                        break
                elif last_angle != 0:
                    turn(np.sign(90 - last_angle), conf.turnStep)
                    continue
                else:
                    break

            turn_state, shift_state = check_shift_turn(a, shift)

            turn_dir, turn_val = get_turn(turn_state, shift_state)

            if turn_dir != 0:
                turn(turn_dir, turn_val)
                last_turn = turn_dir
            else:
                time.sleep(conf.runStraight)
                last_turn = 0
            last_angle = a

    finally:
        print("Standing still")
        # todo: stay still


def run_in_parallel(*fns):
    proc = []
    for fn in fns:
        p = Process(target=fn)
        p.start()
        proc.append(p)
    for p in proc:
        p.join()


if __name__ == '__main__':
    httpd = HTTPServer(('localhost', 80), SimpleHTTPRequestHandler)
    run_in_parallel(start_server, process_camera_input)
