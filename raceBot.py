# raceBot.py - By: charlie - Tue Aug 29 2023

import time
import pca9685
from servo import Servos
from machine import SoftI2C, Pin

def soft_reset(self):
    self.pca9685.duty(0, 0)
    self.pca9685.duty(1, 0)
    self.pca9685.duty(2, 0)

    for i in range(5, 0, -1):
        print(f"{i} seconds remaining.")
        time.sleep(1)

    print("___Running Code___")
