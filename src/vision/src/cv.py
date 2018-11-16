#! /usr/bin/python
# Copyright (c) 2015, Rethink Robotics, Inc.

# Using this CvBridge Tutorial for converting
# ROS images to OpenCV2 images
# http://wiki.ros.org/cv_bridge/Tutorials/ConvertingBetweenROSImagesAndOpenCVImagesPython

# Using this OpenCV2 tutorial for saving Images:
# http://opencv-python-tutroals.readthedocs.org/en/latest/py_tutorials/py_gui/py_image_display/py_image_display.html

import math
# OpenCV2 for saving an image
import cv2
# rospy for the subscriber
import rospy
# ROS Image message -> OpenCV2 image converter
from cv_bridge import CvBridge, CvBridgeError
# ROS Image message
from sensor_msgs.msg import Image
from visualization_msgs.msg import Marker

# Instantiate CvBridge
bridge = CvBridge()
sift = cv2.xfeatures2d.SIFT_create()
template = []
names = ["No image", "Obama", "Avril", "Fuckboi_Chinese", "Levi", "White_Fgt"]
template.append(cv2.imread('/home/dank-engine/ELEC4010K_ws/src/obama.png', 0))
template.append(cv2.imread('/home/dank-engine/ELEC4010K_ws/src/avril.png', 0))
template.append(cv2.imread('/home/dank-engine/ELEC4010K_ws/src/fuckboii_chinese.png', 0))
template.append(cv2.imread('/home/dank-engine/ELEC4010K_ws/src/levi.png', 0))
template.append(cv2.imread('/home/dank-engine/ELEC4010K_ws/src/white_fgt.png', 0))
pub = rospy.Publisher('visualization_marker', Marker, queue_size=100)
mark_array = []

for i in range(len(template)):
    marker = Marker()
    marker.header.frame_id = "camera_link"
    marker.type = marker.TEXT_VIEW_FACING
    marker.action = marker.ADD
    marker.scale.x = 0.5
    marker.scale.y = 0.5
    marker.scale.z = 0.5
    marker.color.a = 1.0
    marker.color.r = 1.0
    marker.color.g = 1.0
    marker.color.b = 0.0
    marker.pose.orientation.w = 1.0
    marker.text = names[i + 1]
    marker.id = i
    mark_array.append(marker)


def image_callback(msg):
    global val_sim, cv2_img
    try:
        # Convert your ROS Image message to OpenCV2
        cv2_img = bridge.imgmsg_to_cv2(msg, "bgr8")
    # cv2.imshow('look', cv2_img)
    # cv2.waitKey(1)
    except CvBridgeError, e:
        print(e)

    gray = cv2.cvtColor(cv2_img, cv2.COLOR_BGR2GRAY)
    # blur = cv2.medianBlur(gray,15)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
    _, contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)

    val_sim = [115]
    compare(cv2_img, template)
    name = names[val_sim.index(max(val_sim))]

    if name != "No image" and len(contours) != 0:
        rviz_mark(contours, name)


def compare(input_im, temp):
    for i in range(len(temp)):
        cnt = 0
        img1 = temp[i]  # queryImage
        # find the keypoints and descriptors with SIFT
        _, des1 = sift.detectAndCompute(img1, None)
        _, des2 = sift.detectAndCompute(input_im, None)
        # FLANN parameters
        FLANN_INDEX_KDTREE = 0
        index_params = dict(algorithm=FLANN_INDEX_KDTREE, trees=5)
        search_params = dict(checks=50)  # or pass empty dictionary

        flann = cv2.FlannBasedMatcher(index_params, search_params)
        try:
            matches = flann.knnMatch(des1, des2, k=2)
            # Need to draw only good matches, so create a mask
            # matchesMask = [[0,0] for i in xrange(len(matches))]
            # ratio test as per Lowe's paper
            for i, (m, n) in enumerate(matches):
                if m.distance < 0.7 * n.distance:
                    # matchesMask[i]=[1,0]
                    cnt = cnt + 1
            val_sim.append(cnt)
            print(cnt)

        except cv2.error as e:
            continue


def rviz_mark(contours, name):
    # find the biggest area
    c = max(contours, key=cv2.contourArea)

    x, y, w, h = cv2.boundingRect(c)
    # draw the book contour (in green)
    # cv2.rectangle(cv2_img,(x,y),(x+w,y+h),(0,255,0),2)

    im_pix_h = h / 2
    im_theta = ((math.pi / 8) * h) / (512)
    dist_pix = (im_pix_h) / math.tan(im_theta)
    dist_x_real = ((dist_pix * 0.5) / im_pix_h)

    index = names.index(name) - 1

    mark_array[index].pose.position.x = dist_x_real
    mark_array[index].pose.position.y = ((x + w / 2) / 512)
    mark_array[index].pose.position.z = 0

    print(name + " " + str(dist_x_real))
    pub.publish(mark_array[index])


def main():
    rospy.init_node('vision')
    # Define your image topic
    image_topic = "/vrep/image"
    # Set up your subscriber and define its callback
    rospy.Subscriber(image_topic, Image, image_callback)
    # Spin until ctrl + c
    rospy.spin()


if __name__ == '__main__':
    main()
