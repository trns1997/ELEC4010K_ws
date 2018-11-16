#! /usr/bin/python

# OpenCV2 for saving an image
import cv2
import numpy as np
# rospy for the subscriber
import rospy
# ROS Image message -> OpenCV2 image converter
from cv_bridge import CvBridge, CvBridgeError
from geometry_msgs.msg import Twist
# ROS Image message
from sensor_msgs.msg import Image
from simple_pid import PID

pid_ang = PID(0.010, 0.002, 0.003, setpoint=256)
pid_spd = PID(0.015, 0.002, 0.01, setpoint=140)

# Instantiate CvBridge
bridge = CvBridge()


def image_callback(msg):
    global val_sim, cv2_img
    try:
        # Convert your ROS Image message to OpenCV2
        cv2_img = bridge.imgmsg_to_cv2(msg, "bgr8")
        # cv2.imwrite('ball.png', cv2_img)
    except CvBridgeError, e:
        print(e)

    pos = Twist()
    pub = rospy.Publisher('/vrep/cmd_vel', Twist, queue_size=10)

    lower_yellow = np.array([20, 150, 150])
    upper_yellow = np.array([30, 255, 255])

    hsv = cv2.cvtColor(cv2_img, cv2.COLOR_BGR2HSV)

    mask_yellow = cv2.inRange(hsv, lower_yellow, upper_yellow)
    contours_yellow = cv2.findContours(mask_yellow, cv2.RETR_EXTERNAL,
                                       cv2.CHAIN_APPROX_SIMPLE)[-2]

    if len(contours_yellow) > 0:
        res_yellow = cv2.bitwise_and(cv2_img, cv2_img, mask=mask_yellow)
        median_yellow = cv2.medianBlur(res_yellow, 15)

        for i in range(len(contours_yellow)):
            # gets parameters for circles
            c = contours_yellow[i]
            ((x, y), radius) = cv2.minEnclosingCircle(c)
            M = cv2.moments(c)

            # if statement to prevent small contours to crash the program
            if M["m00"] == 0:
                continue
            else:
                # computes centre
                center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))
                cv2.circle(median_yellow, center, 5, (0, 0, 255), -1)
		out_ang = pid_ang(x)
		out_spd = pid_spd(radius)
		print(str(out_ang) + " " + str(out_spd))
                speed = out_spd #(-0.0072 * radius) + 1.4545
		ang = -out_ang #(0.00390625 * x) - 1
		pos.linear.x = speed
		pos.angular.z = ang
            pub.publish(pos)

    # cv2.imshow('mask',mask)
    # cv2.imshow('Result', median_yellow)
    # cv2.waitKey(1)


def main():
    rospy.init_node('ball_tracker')
    # Define your image topic
    image_topic = "/vrep/image"
    # Set up your subscriber and define its callback
    rospy.Subscriber(image_topic, Image, image_callback)
    # Spin until ctrl + c
    rospy.spin()


if __name__ == '__main__':
    main()
