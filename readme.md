
# EduRob-LineFollower

This project utilizes the [EduRob](https://github.com/IDiAL-IMSL/Edurob) and combines it with an NVIDIA Jetson Nano to create 
a line-following robot, based on computer vision algorithms written in Python.

Since the setup of several components on the Jetson Nano proved rather difficult, we created a docker container for it which is publicly
available on docker hub: [blssed/ros2robotik](https://hub.docker.com/repository/docker/blssed/ros2robotik/general)


## Hardware
- EduRob (4x90° Omni-Wheel version)
- NVIDIA Jetson Nano
- Infrared camera
- Wifi-stick
- 2x Power-bank


## Setup
#### EduRob with ROS 2 (Humble)

Make sure to follow the [Getting Started](https://github.com/IDiAL-IMSL/Edurob/blob/main/Doc/README.md) guide to
prepare your EduRob's ROS interface. 
Your EduRob and Jetson Nano will communicate via Wifi, so make sure to setup the connection with `set_microros_wifi_transports("APNAME", "WIFIKEY", "MICRO_ROS_IP", 8888)`.
Our tests showed that a 5 GHz network works better than 2.4 GHz. It's probably a good idea to assign static IPv4 addresses if your network uses a DHCP server.

<br>

#### Jetson Nano with our [docker container](https://hub.docker.com/repository/docker/blssed/ros2robotik/general)

- Setup your Jetson's Wifi and forward any port you need
- Adjust the call to `gstreamer_pipeline()` according to your camera. Keep the fps between 10-25
- Adjust your Region of Interest in `Util/ROI.py` if your camera's aspect ratio differs from 16:9
- Adjust the thresholds for `balance_pic(image)` in `ImageHandling.py` according to your use-case. <br> 
We used white tape on a dark floor. If your setup differs you need to play around with `minWhite` and `maxWhite` inside your `Util/config.py`.

<br>

## How it works

### TL:DR
- Jetson Nano grabs the current frame from the camera
- Convert image to grayscale and apply gaussian blurr to remove artifacts
- Initialize ROI and balance the image to find the configured amount of white pixels representing the line
- Find contours using OpenCV's `cv.findContours(...)`, minimize the area and generate a box of vectors
- Find the angle of your line by analyzing the box
- Find the line's offset from your robot's middle point
- Make driving decisions based off the angle and offset
- Publish message of type `Twist` to the ROS interface

<br>

### Grabbing the current frame

The NVIDIA Jetson Nano platform offers a pipeline granting access to the camera feed. 
We utilize this pipeline calling `gstreamer_pipeline(...)` with the desired setup. You can adjust your framerate
to allow for a smoother drive, although you should make sure to benchmark your Jetson's performance. We found that 
ours was able to handle approx. 28 frames per second before being bottlenecked by its CPU. 

```
def gstreamer_pipeline(
        capture_width=1280,
        capture_height=720,
        display_width=820,
        display_height=616,
        framerate=10,
        flip_method=0,
): /* ... */    
```

<br>

### Debugging info

To make our life a bit easier, we are hosting a simple web service when starting the line follower, which provides
a simplistic view of images at certain stages within our decision-making. The site is available at your Jetson's IP 
address and listens to port 80 by default.

<br>

### Preparing the image

The images received from the gstreamer pipeline had a noticeable red/purple shift due to our usage of an infrared camera.
Converting the image to grayscale proved highly effective in increasing the accuracy of detecting lines. 

Additionally, we applied a gaussian blurr algorithm to remove any artifacts from the camera and smooth it a bit.

We did this using OpenCV: `cv.GaussianBlur(cv.cvtColor(image, cv.COLOR_BGR2GRAY), (9, 9), 0)`

<br>

### Region of Interest (ROI)

Since our goal was to follow a line directly in front of the EduRob, we obviously didn't care about possible line detections 
far ahead or even at walls around us. To restrict the following algorithms to only care about this area, we declare our ROI 
in `ROI.init_roi(...)` and define it by 4 vertices:

```
vertices = [(0, height), (width / 4, height / 2), (3 * width / 4, height / 2), (width, height), ]
```

To better visualize what those vertices mean, see the following sketch:
<div style="text-align: center;">
<img src="https://cdn.discordapp.com/attachments/359406828603572225/1123700459199275079/image.png" alt="Region of Interest (ROI) visualized" style="max-width: 50%">
</div>

The area of the picture outside our region of interest ist masked with black pixels so that it will be ignored in later steps.

You should adjust these settings based on the width of your line and your camera input, especially when using other aspect ratios than 16:9.

<br>

### Finding contours

The main workload of getting a set of vertices representing found contours is provided by OpenCV's `findCountours(...)` method.
Since this returns <i>any</i> contour found in the image, we first need to prepare it using our `balance_pic(...)` algorithm, which
is basically an iterative threshold adjustment algorithm to balance the amount of white pixels which will then represent our line.

To actually be able to work with those vertices we must now build a box with them and find the smallest area surrounding it and order
the points making this box to later adjust for horizontal stretching. We decided on starting at the top left point 
and work in a clockwise order from there on.

<br>

### Determine angle and offset

Using our box, we can now calculate the center of the detected line. Setting this in relation to our screen resolution enables us
to obtain two important values:
- Angle `alpha` (in degrees), indicating which way we need to turn
- An `offset` to the center, indicating 'how hard' we need to turn

<div style="text-align: center;">
<img src="https://cdn.discordapp.com/attachments/359406828603572225/1123703032924884992/image.png" alt="" style="max-width: 40%">
</div>

<br>

### Make a decision

We are using some basic decision-making here, sorely based on the angle. If `alpha` is less than 85° we turn right,
if its greater than 95° we turn left. In case `alpha` lies between 85° and 95° we chose to drive straight ahead to avoid
any unnecessary 'wobbling'.

In case the angle is `None`, meaning no line has been detected, we call `find_line()`, which turns the EduRob into the direction
of the last known line until it 'finds it' again. 

As a side note: We didn't implement a usage for the offset yet. Feel free to create your own, followed by a pull request :)

<br>

### Communicate decision

All that's left to do, is telling the EduRob where/how to drive now. To do so, we utilize our `moveBindings` to publish messages
of type `geometry_msgs.msg.Twist` to the `cmd_vel` topic of our EduRob's ROS interface.




