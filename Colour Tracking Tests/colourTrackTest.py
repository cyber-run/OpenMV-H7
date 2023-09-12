import time
from servoBot import *
from RobotTuning import *

servo = servos()
servo.soft_reset()

tuning = RobotTuning(servo)

tuning.measure(0.1)
