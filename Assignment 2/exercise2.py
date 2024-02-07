from tuning import *
from machine import LED

led = LED("LED_BLUE")
led.on()

thresholds = [
      (20, 50, 40, 80, 25, 65), # Red
      (15, 45, 25, 65, -100, -50), # Blue
]

tuning = PanTuning(thresholds, gain = 5, p=0.2, i=0, d=0.005)

tuning.measure(0.1)
