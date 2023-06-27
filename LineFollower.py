import ImageHandling as imgHandler
import cv2 as cv
import rclpy
from geometry_msgs.msg import Twist
from http.server import HTTPServer, SimpleHTTPRequestHandler
from multiprocessing import Process

rclpy.init()
node = rclpy.create_node('line_follower')
pub = node.create_publisher(Twist, 'cmd_vel', 10)
twist = Twist()

lastTurn = 'right'

moveBindings = {
    'driveForward': (1, 0, 0, 0),
    'driveLeft': (1, 0, 0, 1),
    'driveRight': (1, 0, 0, -1),
    'turnLeft': (0, 0, 0, 2),
    'turnRight': (0, 0, 0, -2)
}


def gstreamer_pipeline(
        capture_width=1280,
        capture_height=720,
        display_width=820,
        display_height=616,
        framerate=10,
        flip_method=0,
):
    """
    Generates a GStreamer pipeline string for capturing video using the NVIDIA Jetson platform.
    :param capture_width: Width of the captured video.
    :param capture_height: Height of the captured video.
    :param display_width: Width of the displayed video.
    :param display_height: Height of the displayed video.
    :param framerate: Frame rate of the captured video.
    :param flip_method: Flip method for the captured video.
    :return: GStreamer pipeline string.
    """
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
    """
    Processes camera input by capturing video and passing each frame to the `follow` function.
    :return: none
    """
    cap = cv.VideoCapture(gstreamer_pipeline(), cv.CAP_GSTREAMER)
    while cap.isOpened():
        ret, img = cap.read()
        follow(img)


def start_server():
    """
    Starts an HTTP server that serves requests forever.
    """
    httpd.serve_forever()
    print("Server started")


# turn 45° and check again
def find_line():
    """
    Finds the line to follow based on the value of the `lastTurn` variable.
    :return: No return, only publish to the ROS2 topic
    """
    global lastTurn
    print(f"Finding line to the {lastTurn}")
    if lastTurn == 'right':
        x = moveBindings['turnRight'][0]
        y = moveBindings['turnRight'][1]
        z = moveBindings['turnRight'][2]
        th = moveBindings['turnRight'][3]
    else:
        x = moveBindings['turnLeft'][0]
        y = moveBindings['turnLeft'][1]
        z = moveBindings['turnLeft'][2]
        th = moveBindings['turnLeft'][3]


    twist = Twist()
    twist.linear.x = x * 0.1
    twist.linear.y = y * 0.1
    twist.linear.z = z * 0.1
    twist.angular.x = 0.0
    twist.angular.y = 0.0
    twist.angular.z = th * 0.2
    pub.publish(twist)


def follow(image):
    """
    Processes the image and determines the movement commands for the robot to follow a line.
    :param image: The input image to process.
    :return: No return, only publish to the ROS2 topic
    """
    global lastTurn
    x = 0
    y = 0
    z = 0
    th = 0

    try:
        angle, shift = imgHandler.handle_pic(image)
        if angle is None or angle is 0:
            # try to find a line
            find_line()
            return
        elif 95 < angle <= 105:
            print(f"Driving right, Angle: {angle}")
            lastTurn = 'right'
            x = moveBindings['driveRight'][0]
            y = moveBindings['driveRight'][1]
            z = moveBindings['driveRight'][2]
            th = moveBindings['driveRight'][3]
        elif 75 <= angle < 85:
            print(f"Driving left, Angle: {angle}")
            lastTurn = 'left'
            x = moveBindings['driveLeft'][0]
            y = moveBindings['driveLeft'][1]
            z = moveBindings['driveLeft'][2]
            th = moveBindings['driveLeft'][3]
        elif 85 <= angle <= 95:
            print(f"Driving forward, Angle: {angle}")
            x = moveBindings['driveForward'][0]
            y = moveBindings['driveForward'][1]
            z = moveBindings['driveForward'][2]
            th = moveBindings['driveForward'][3]
        elif angle < 75:
            print(f"Turning left, Angle: {angle}")
            lastTurn = 'left'
            x = moveBindings['turnLeft'][0]
            y = moveBindings['turnLeft'][1]
            z = moveBindings['turnLeft'][2]
            th = moveBindings['turnLeft'][3]
        elif angle > 105:
            print(f"Turning right, Angle: {angle}")
            lastTurn = 'right'
            x = moveBindings['turnRight'][0]
            y = moveBindings['turnRight'][1]
            z = moveBindings['turnRight'][2]
            th = moveBindings['turnRight'][3]

    finally:
        twist = Twist()
        twist.linear.x = x * 0.1
        twist.linear.y = y * 0.1
        twist.linear.z = z * 0.1
        twist.angular.x = 0.0
        twist.angular.y = 0.0
        twist.angular.z = th * 0.2
        pub.publish(twist)


def run_in_parallel(*fns):
    """
    Runs the given functions in parallel using separate processes.
    :param fns: Variable-length argument list of functions to execute.
    :return: none
    """
    proc = []
    for fn in fns:
        p = Process(target=fn)
        p.start()
        proc.append(p)
    for p in proc:
        p.join()


if __name__ == '__main__':
    httpd = HTTPServer(('0.0.0.0', 80), SimpleHTTPRequestHandler)
    run_in_parallel(start_server, process_camera_input)
