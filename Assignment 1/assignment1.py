# This example demonstrates the servo shield. Please follow these steps:
#
#   1. Connect a servo to any PWM output.
#   2. Connect a 3.7v battery (or 5V source) to VIN and GND.
#   3. Copy pca9685.py and servo.py to OpenMV and reset it.
#   4. Connect and run this script in the IDE.

import time
from servoBot import *

servo = servos()

servo.soft_reset()

# while True:
#    servo.position(1, 0)
#    time.sleep_ms(2000)
#    servo.position(1, 86)
#    time.sleep_ms(2000)
#    servo.position(1, 180)
#    time.sleep_ms(2000)

# gimbal centre = 1650us
# microSec range = 850/2450

# wheel servos = 1,2 => centre = 1425us
# wheel range = 625/2325us

servo.set_angle(0)
time.sleep_ms(2000)
print('40')
servo.set_angle(40)
time.sleep_ms(2000)
print('-40')
servo.set_angle(-40)
time.sleep_ms(2000)
servo.set_angle(0)
time.sleep_ms(2000)

servo.set_speed(0,0)
print('0,0')
time.sleep_ms(5000)
servo.set_speed(0.2,0.2)
print('0.2,0.2')
time.sleep_ms(5000)
servo.set_speed(-0.2,-0.2)
time.sleep_ms(5000)

servo.soft_reset()

#servo.position(1, duty=300)
#time.sleep(500)
#servo.position(1, duty=400)
#time.sleep(500)
#servo.position(1, duty=500)
#time.sleep(500)

# Loop through the microsecond range
#for us in range(800, 2400, 50):  # 50 microseconds interval
#    servo.position(1, us=us)
#    print(us)
#    time.sleep_ms(500)
