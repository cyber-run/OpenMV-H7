from servos import *
import time

servo = Servo()
servo.soft_reset()

# Servo speed test
servo.set_speed(0,0)
print('0,0')
time.sleep_ms(2000)

servo.set_speed(0.2,0.2)
print('0.2,0.2')
time.sleep_ms(2000)

print('-0.2,-0.2')
servo.set_speed(-0.2,-0.2)
time.sleep_ms(2000)

servo.soft_reset()
