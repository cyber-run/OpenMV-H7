from servos import *
import time

servo = Servo()
servo.soft_reset()

# Servo speed test
print('\n0,0')
servo.set_speed(0,0)
time.sleep_ms(1000)

print('\n0.2,0.2')
servo.set_speed(0.2,0.2)
time.sleep_ms(3000)

print('\n0.5, 0.5')
servo.set_speed(0.5, 0.5)
time.sleep_ms(3000)

print('\n0, 0')
servo.set_speed(0.8, 0.8)
time.sleep_ms(3000)

print('\n1, 1')
servo.set_speed(0.8, 0.8)
time.sleep_ms(3000)

servo.soft_reset()
