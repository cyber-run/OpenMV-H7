import pca9685, pyb
from machine import SoftI2C, Pin
from math import asin


class servos:
    """
    Class for controlling servos through OpenMV board.
    """
    def __init__(self):
        """
        Initialises the servo object and sets the tuning coefficients.
        """
        ###### EDIT THESE VALUES TO TUNE THE SERVOS ######
        self.pan_angle_corr = 0
        self.left_zero = -0.07
        self.right_zero = 0.10
        self.left_coeff = [[0, 0, 0], [0, 0, 0]]
        self.right_coeff = [[0, 0, 0], [0, 0, 0]]
        ###################################################

        # IDs for servo pins on the servo shield
        self.pan_id = 7
        self.left_id = 5
        self.right_id = 4

        # Set up servo angle limits
        self.degrees = 120
        self.min_deg = -self.degrees/2
        self.max_deg = self.degrees/2

        self.curr_l_speed = 0
        self.curr_r_speed = 0
        self.gimbal_pos = 0

        self.freq = 50
        self.period = 1000000 / self.freq

        # Convert max/min us to duty cycle
        self.min_duty = self._us2duty(700)
        self.max_duty = self._us2duty(2300)
        self.mid_duty = (self.min_duty + self.max_duty) / 2
        self.span = (self.max_duty - self.min_duty)

        # Initialise PCA9685 (I2C bus for sending PWM signal to servos)
        self.pca9685 = pca9685.PCA9685(SoftI2C(sda=Pin('P5'), scl=Pin('P4')), 0x40)
        self.pca9685.freq(self.freq)


    def set_angle(self, angle: float) -> float:
        """
        Sets the angle of gimbal servo.

        Args:
            `angle` (float): Angle to set servo to in degrees
        """
        # Correct for off centre angle
        angle = self.pan_angle_corr + angle

        # Constraint angle to limits
        angle = max(min(angle, self.max_deg), self.min_deg)

        self.gimbal_pos = angle

        # Compute duty for pca PWM signal
        duty = self.mid_duty + ( self.span * (angle / self.degrees) )

        # Set duty and send PVM signal
        self.pca9685.duty(self.pan_id, int(duty) )

        return angle - self.pan_angle_corr


    def set_speed(self, l_speed: float, r_speed: float) -> None:
        """
        Sets the speed of the left and right wheel servos.

        Args:
            `l_speed` (float): Speed to set left wheel servo to (-1~1) \n
            `r_speed` (float): Speed to set right wheel servo to (-1~1)
        """
        # Initialize signs for acceleration or deceleration
        left_sign = 0
        right_sign = 0
        graduation = 0.25  # max "acceleration"
        delay = 50  # ms resting time between jumps in speed

        # Constraint speeds to limits
        l_speed = max(min(l_speed, 1), -1)
        r_speed = max(min(r_speed, 1), -1)

        # Smoothing for left speed
        if abs(l_speed - self.curr_l_speed) > graduation:
            if l_speed - self.curr_l_speed > 0:
                left_sign = 1
            else:
                left_sign = -1
            self.curr_l_speed += graduation * left_sign
        else:
            self.curr_l_speed = l_speed

        # Smoothing for right speed
        if abs(r_speed - self.curr_r_speed) > graduation:
            if r_speed - self.curr_r_speed > 0:
                right_sign = 1
            else:
                right_sign = -1
            self.curr_r_speed += graduation * right_sign
        else:
            self.curr_r_speed = r_speed

        # Convert smoothed speed to duty
        l_duty = self.mid_duty + (self.span * (self.curr_l_speed + self.left_zero))
        r_duty = self.mid_duty - (self.span * (self.curr_r_speed + self.right_zero))

        # Set duty and send PWM signal
        self.pca9685.duty(self.left_id, int(l_duty))
        self.pca9685.duty(self.right_id, int(r_duty))

        if left_sign != 0 or right_sign != 0:
            pyb.delay(delay)  # Wait for a short period before the next iteration
            self.set_speed(l_speed, r_speed, delay)  # Recursive call

        return


    #TODO: Implement tuning coefficients
    def calc_speed(self, speed: float) -> float:
        """
        Returns the corrected speed setting for desired speed based on tuning coeffs.

        Args:
            `speed` (float): Desired wheel speed (-1~1)
        """
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


    def _duty2us(self, value: float) -> int:
        """
        Convert duty cycle to microsecond.
        """
        return int(value * self.period / 4095)


    def _us2duty(self, value: float) -> int:
        """
        Convert microsecond to duty cycle.
        """
        return int(4095 * value / self.period)


    def release(self, index: int) -> None:
        """
        Simple servo release method
        """
        self.pca9685.duty(index, 0)


    def get_gimbal(self) -> float:
        """
        Returns the current angle of the gimbal servo.
        """
        return self.gimabl_pos


    def soft_reset(self) -> None:
        """
        Method to reset the servos to default and print a delay prompt.
        """
        # Reset all servo shield pins
        for i in range(0, 7, 1):
            self.pca9685.duty(i, 0)

        # Reset gimbal to centre
        self.set_angle(0)

        # Print delay prompt
        for i in range(3, 0, -1):
            print(f"{i} seconds remaining.")
            pyb.delay(1000)

        print("___Running Code___")
