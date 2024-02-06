from tuning import *
import pyb

led = pyb.LED(1)
led.on()

tuning = PanTuning(0.2, 0, 0)

tuning.measure(0.1)
