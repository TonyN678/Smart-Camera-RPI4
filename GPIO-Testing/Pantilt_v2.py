import RPi.GPIO as GPIO
from time import sleep
import math

# Constants for SG90 micro servo
MIN_DUTY = 2.5
MAX_DUTY = 12.5
FREQ = 50  # Frequency of the PWM

# Camera FOV (adjust based on your camera's specification)
HORIZONTAL_FOV = 62.2  # PiCamera horizontal field of view in degrees
VERTICAL_FOV = 48.8  # PiCamera vertical field of view in degrees

# Servo pins
xpin = 16  # Pan servo
ypin = 8   # Tilt servo

# Setup GPIO
GPIO.setmode(GPIO.BOARD)
GPIO.setup(xpin, GPIO.OUT)
GPIO.setup(ypin, GPIO.OUT)

# Setup PWM
x = GPIO.PWM(xpin, FREQ)  # Pan servo
y = GPIO.PWM(ypin, FREQ)  # Tilt servo
x.start(7.5)  # Start at the center position (90 degrees)
y.start(7.5)  # Start at the center position (90 degrees)

class PanTiltCamera:
    def __init__(self, frame_width, frame_height):
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.current_pan_angle = 90  # Start at center (90 degrees)
        self.current_tilt_angle = 90  # Start at center (90 degrees)

    def calculate_angle(self, coord, frame_size, fov):
        """Calculate the angle based on object coordinates, frame size, and field of view."""
        normalized_coord = coord / frame_size - 0.5  # Normalize and center coordinate
        return normalized_coord * fov

    def angle_to_duty_cycle(self, angle):
        """Map an angle (0 to 180 degrees) to a servo duty cycle (2.5% to 12.5%)."""
        return MIN_DUTY + (angle / 180.0) * (MAX_DUTY - MIN_DUTY)

    def move_servo(self, servo, angle):
        """Move the servo to the specified angle by adjusting its duty cycle."""
        duty_cycle = self.angle_to_duty_cycle(angle)
        servo.ChangeDutyCycle(duty_cycle)
        sleep(0.5)  # Allow time for the servo to move
        servo.ChangeDutyCycle(0)  # Stop sending signal to prevent jittering

    def track_object(self, x_coord, y_coord):
        """Track an object based on its coordinates in the camera frame."""
        # Calculate pan angle (horizontal movement)
        pan_angle = self.calculate_angle(x_coord, self.frame_width, HORIZONTAL_FOV)
        self.current_pan_angle = 90 + pan_angle  # Adjust from center (90 degrees)

        # Calculate tilt angle (vertical movement)
        tilt_angle = self.calculate_angle(y_coord, self.frame_height, VERTICAL_FOV)
        self.current_tilt_angle = 90 - tilt_angle  # Adjust from center (90 degrees)

        # Ensure the angles are within the servo's range (0 to 180 degrees)
        self.current_pan_angle = max(0, min(180, self.current_pan_angle))
        self.current_tilt_angle = max(0, min(180, self.current_tilt_angle))

        # Move the servos to the calculated angles
        self.move_servo(x, self.current_pan_angle)
        self.move_servo(y, self.current_tilt_angle)

# Example usage
frame_width = 640  # Assuming a 640x480 resolution
frame_height = 480

# Create Pan-Tilt Camera instance
#camera_tracker = PanTiltCamera(frame_width, frame_height)

# Coordinates of the detected object (example)
x_coord = 320  # Middle of the frame horizontally
y_coord = 240  # Middle of the frame vertically

# Track object based on detected coordinates
#camera_tracker.track_object(x_coord, y_coord)
