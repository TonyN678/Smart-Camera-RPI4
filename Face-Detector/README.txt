Author: Tien Nguyen, 2024

This folder includes code for face recognition using Pi Camera with Raspberry Pi 4!

The main file is face-detection.py while the other are for reference from @justsaumit (https://github.com/justsaumit/opencv-face-recognition-rpi4/blob/main/face-detection/03_face_recogition.py)

Python Modules Needed:
    - flask: to host camera's output on a local network
    - picamera2: output frame or image from Pi Camera Module
    - opencv2: face recognition and image manipulation
    - libcamera: just to flip the camera upside down from default

Also need a HaarCascade file for face patterns(algorithm for computer to recognise face)!
https://github.com/opencv/opencv/tree/master/data/haarcascades

But according to Adrian Rosebrock, "Face detection with OpenCV and Haar cascades" is the worst, trading accuracy with speed! 
Explore more on the article below:
https://pyimagesearch.com/2021/04/26/face-detection-tips-suggestions-and-best-practices/
