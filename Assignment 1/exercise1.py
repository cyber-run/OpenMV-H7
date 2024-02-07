from servos import *
from camera import *
from machine import LED

led = LED("LED_BLUE")
led.on()

servo = Servo()
servo.soft_reset()

thresholds = [
              (60, 70, -40, -15, 25, 55), # Light green
              (25, 35, -15, 10, -30, -10), # Blue
              (68, 80, -30, 0, 40, 60), # Yellow
              (45, 55, 40, 55, 15, 35), # Red
]
camera = Cam(thresholds)

# Test your assignment code here. Think about how you might want to adjust the steering based on the position of
# the colour targets in the image. What should the bot do if the next colour target is outside the field of view
# of the camera? What would your bot do if the colour target is lost for a single frame? Some helpful functions are:
# camera.get_blobs_bottom()
# camera.find_blobs()
# servos.set_differential_drive()

servo.soft_reset()
