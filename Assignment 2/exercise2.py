from servos import *
from camera import *

servo = Servo()
servo.soft_reset()

tuning = Cam(servo)

tuning.measure(0.8)
