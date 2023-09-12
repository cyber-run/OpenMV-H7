import pca9685, math, time
from machine import SoftI2C, Pin

# nominal centre = 1500us
# nominal range = 700/2300us

# gimbal centre = 1650us
# microSec range = 850/2450

# wheel servos = 1,2 => centre = 1425us
# wheel range = 625/2325us

class servos:
    def __init__(self):

        ###### EDIT THESE VALUES TO TUNE THE SERVOS ######
        self.pan_angle_corr = 0
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
        self.span = (self.max_duty - self.min_duty)

        self.degrees = 120
        self.min_deg = -self.degrees/2
        self.max_deg = self.degrees/2

        self.last_right_speed = 0
        self.last_left_speed = 0
        self.gimbal_pos = 0

        # Initialise PCA9685 (I2C bus for sending PWM signal to servos)
        self.pca9685 = pca9685.PCA9685(SoftI2C(sda=Pin('P5'), scl=Pin('P4')), 0x40)
        self.pca9685.freq(self.freq)

        # Initialise servo pins on the servo shield
        self.pan_id = 7
        self.right_id = 4
        self.left_id = 5


    def set_angle(self, angle):
        # Correct for off centre angle
        angle = self.pan_angle_corr + angle

        # Constraint angle to limits
        angle = max(min(angle, self.max_deg), self.min_deg)

        self.gimbal_pos = angle

        # Compute duty for pca PWM signal
        duty = self.mid_duty + ( self.span * (angle / self.degrees) )
        # Set duty and send PVM signal
        # print('Duty: ', int(duty))
        self.pca9685.duty(self.pan_id, int(duty) )

        return angle - self.pan_angle_corr


    def set_speed(self, target_left_speed, target_right_speed):
        # Initialize signs for acceleration or deceleration
        left_sign = 0
        right_sign = 0
        graduation = 0.25  # max "acceleration"
        delay = 0.05  # resting time between jumps in speed

        # Constraint speeds to limits
        target_left_speed = max(min(target_left_speed, 1), -1)
        target_right_speed = max(min(target_right_speed, 1), -1)

        # Smoothing for left speed
        if abs(target_left_speed - self.last_left_speed) > graduation:
            if target_left_speed - self.last_left_speed > 0:
                left_sign = 1
            else:
                left_sign = -1
            self.last_left_speed += graduation * left_sign
        else:
            self.last_left_speed = target_left_speed

        # Smoothing for right speed
        if abs(target_right_speed - self.last_right_speed) > graduation:
            if target_right_speed - self.last_right_speed > 0:
                right_sign = 1
            else:
                right_sign = -1
            self.last_right_speed += graduation * right_sign
        else:
            self.last_right_speed = target_right_speed

        # Convert smoothed speed to duty
        l_duty = self.mid_duty + (self.span * (self.last_left_speed + self.left_zero))
        r_duty = self.mid_duty - (self.span * (self.last_right_speed + self.right_zero))

        # Set duty and send PWM signal
        self.pca9685.duty(self.left_id, int(l_duty))
        self.pca9685.duty(self.right_id, int(r_duty))

        if left_sign != 0 or right_sign != 0:
            time.sleep(delay)  # Wait for a short period before the next iteration
            self.set_speed(target_left_speed, target_right_speed, delay)  # Recursive call

        return


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


    # Convert duty cycle to microsecond
    def _duty2us(self, value):
        return int(value * self.period / 4095)


    # Convert microsecond to duty cycle
    def _us2duty(self, value):
        return int(4095 * value / self.period)


    # Simple servo release method
    def release(self, index):
        self.pca9685.duty(index, 0)

    def get_gimbal(self):
        return self.gimabl_pos


    # Method to release the 3 servos and print a delay prompt for reset
    def soft_reset(self):
        # Reset all servo shield pins
        for i in range(0, 7, 1):
            self.pca9685.duty(i, 0)

        # Reset gimbal to centre
        self.set_angle(0)

        # Print delay prompt
        for i in range(3, 0, -1):
            print(f"{i} seconds remaining.")
            time.sleep(1)

        print("___Running Code___")
