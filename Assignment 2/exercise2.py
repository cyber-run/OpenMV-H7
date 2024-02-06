from tuning import *
from machine import LED

led = LED("LED_BLUE")
led.on()

thresholds = [
    (45, 55, 40, 55, 15, 35), # Red
    (25, 35, -15, 10, -30, -10), # Blue
]

tuning = PanTuning(thresholds, p=0.2, i=0, d=0)

tuning.measure(0.1)
