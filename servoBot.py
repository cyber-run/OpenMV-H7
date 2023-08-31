import pca9685, math, time
from machine import SoftI2C, Pin

# nominal centre = 1500us
# nominal range = 700/2300us

# gimbal centre = 1650us
# microSec range = 850/2450

# wheel servos = 1,2 => centre = 1425us
# wheel range = 625/2325us

class Servos:
    def __init__(self):

        ###### EDIT THESE VALUES TO TUNE THE SERVOS ######
        self.pan_angle_corr = 10
        self.left_zero = -0.07
        self.right_zero = 0.10
        self.left_coeff = [[0, 0, 0], [0, 0, 0]]
        self.right_coeff = [[0, 0, 0], [0, 0, 0]]
        ###################################################

        self.freq = 50
        self.period = 1000000 / self.freq

        # Convert max/min us to duty cycle
        self.min_duty = self._us2duty(700)
        self.max_duty = self._us2duty(2300)
        self.mid_duty = (self.min_duty + self.max_duty) / 2
        self.span = (self.max_duty - self.min_duty) / 2

        self.degrees = 140
        self.min_deg = -self.degrees/2
        self.max_deg = self.degrees/2

        self.pca9685 = pca9685.PCA9685(SoftI2C(sda=Pin('P5'), scl=Pin('P4')), 0x40)
        self.pca9685.freq(self.freq)

        self.pan_id = 0
        self.right_id = 1
        self.left_id = 2


    # Convert microsecond to duty cycle
    def _us2duty(self, value):
        return int(4095 * value / self.period)


    def set_angle(self, angle):
        # Correct for off centre angle
        angle = self.pan_angle_corr + angle

        # Constraint angle to limits
        angle = max(min(angle, self.max_deg), self.min_deg)

        # Compute duty for pca PWM signal
        duty = self.mid_duty + ( self.span * (angle / self.degrees) )
        # Set duty and send PVM signal
        self.pca9685.duty(self.pan_id, int(duty) )

        return angle - self.pan_angle_corr


    def set_speed(self, left_speed, right_speed):
        # Constraint speeds to limits

        left_speed = max(min(left_speed, 1), -1)
        right_speed = max(min(right_speed, 1), -1)

        # Convert speed to duty
        l_duty = self.mid_duty + ( self.span * (left_speed + self.left_zero) )
        r_duty = self.mid_duty - ( self.span * (right_speed +  self.right_zero) )

        # Set duty and send PVM signal
        print(f"Right: {r_duty}, Left: {l_duty}")
        self.pca9685.duty(self.left_id, int(l_duty))
        self.pca9685.duty(self.right_id, int(r_duty))

        print('passed')

        return


    # Method for setting servo position, can use degree/radian or microSecond (us)
    # If degrees is input then convert to
    def position(self, index, degrees=None, radians=None, us=None, duty=None):
        span = self.max_duty - self.min_duty
        if degrees is not None:
            duty = self.min_duty + span * degrees / self.degrees
        elif radians is not None:
            duty = self.min_duty + span * radians / math.radians(self.degrees)
        elif us is not None:
            duty = self._us2duty(us)
        elif duty is not None:
            pass
        else:
            return self.pca9685.duty(index)
        duty = min(self.max_duty, max(self.min_duty, int(duty)))
        self.pca9685.duty(index, duty)


    # output            - none
    # speed             - list of desired wheel speeds (-1~1, list)
    def smoothSpeed(self, speed):
        graduation = 0.25 # max "acceleration"
        delay = 0.05 # resting time between jumps in speed
        sign = 0 # sign of acceleration
        for i in range(len(speed)):
            if abs(speed[i]-self[i].lastSpeed) > graduation: # check if acceleration is too great
                if (speed[i]-self[i].lastSpeed) > 0: # check acceleration sign
                    sign = 1
                else:
                    sign = -1
                self[i].lastSpeed = self[i].lastSpeed+sign*graduation # set interim speed
            else:
                self[i].lastSpeed = speed[i] # jump to final speed

            # if acceleration is too great, make a smaller jump in speed instead
            actualTurn = self[i].getTurnSpeeds(self[i].lastSpeed)

            # Convert speed to duty cycle
            duty = self.mid_duty + ( self.span / speed)
            # Set duty and send PVM signal
            self.pca9685.duty(self.pan_id, duty)

        # if acceleration is too great, wait between jumps in speed
        if sign != 0:
            t_start = time()
            t_end = t_start + delay

            while time() < t_end:
                pass
            # make another jump
            cServo.smoothSpeed(obj,speed)


    # output            - corrected speed setting for desired speed based on tuning coeffs (-1~1)
    # speed             - desired wheel speed (-1~1)
    def getTurnSpeeds(self, speed):
        if any(x != 0 for v in self.coeffs for x in v): # if tuning coeffs exist
        # work out what throttle is needed to achieve desired speed
            if speed > 0:
                shift = self.coeffs[0][0]
                xscale = self.coeffs[0][1]
                yscale = self.coeffs[0][2]
                # inverse the sine fit to find setting to match desired speed
                speed = xscale*asin(speed/yscale)+shift
                if speed > 1:
                    speed = 1

            elif speed < 0:
                shift = self.coeffs[1][0]
                xscale = self.coeffs[1][1]
                yscale = self.coeffs[1][2]
                # inverse the sine fit to find setting to match desired speed
                speed = xscale*asin(speed/yscale)+shift
                if speed < -1:
                    speed = -1

        return speed


    # Simple servo release method
    def release(self, index):
        self.pca9685.duty(index, 0)


    # Method to release the 3 servos and print a delay prompt
    def soft_reset(self):
        self.pca9685.duty(0, 0)
        self.pca9685.duty(1, 0)
        self.pca9685.duty(2, 0)

        for i in range(3, 0, -1):
            print(f"{i} seconds remaining.")
            time.sleep(1)

        print("___Running Code___")
