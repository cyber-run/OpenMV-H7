from servos import *
from camera import *
from pid import PID

class Robot(object):
    """
    This class contains robot functions for driving and tracking.
    """
    def __init__(self, p=0.22, i=0.0, d=0.0, imax=0.0):
        # Initialise servos and reset to zero positions
        self.servo = Servo()
        self.servo.soft_reset()

        # Initialise camera
        self.cam = Cam()

        # Tuning parameters
        self.PID = PID(p, i, d, imax)

        self.mid_line_id = 1
        self.l_line_id = 2
        self.r_line_id = 3
        self.obstacle_id = 4


    def follow_line(self) -> None:
        """
        Follows the line using the camera and drives towards it.
        """
        while True:
            # Track red line
            big_blob = self.track_blob(self.mid_line_id)

            if big_blob is not None and big_blob.code() == self.mid_line_id:
                # Get heading angle
                heading_angle = self.servo.gimbal_pos
                # Convert to angle correction weight (between -1 and 1)
                angle_correction = heading_angle/self.servo.max_deg
                # Drive towards line
                self.drive(0.5, angle_correction)
            else:
                self.drive(0, 0)
                print('No line found')


    def drive(self, drive: float, bias: float) -> None:
        """
        Differential drive function for the robot.

        Args:
            `drive` (float): Speed to set the robot to (-1~1) \n
            `bias` (float): Bias to set the robot to (-1~1)
        """
        # Apply limits
        bias = max(min(bias, 1), -1)
        drive = max(min(drive, 1), -1)

        # Calculate differential drive
        diff_drive = bias*drive

        # Calculate straight drive
        straight_drive = drive - abs(diff_drive)

        # Calculate left and right drive
        l_drive = straight_drive - diff_drive
        r_drive = straight_drive + diff_drive

        # Apply tuning coefficients
        self.servo.set_speed(l_drive, r_drive)


    def track_blob(self, blob_id) -> None:
        """
        Tracks a blob - changing the servo angle to
        track the blob passed into method.

        """
        # Get list of blobs and biggest blob
        blobs, img = self.cam.get_blobs()
        big_blob = self.cam.get_big_blob(blobs,img)

        # Check biggest blob is not None and is the defined ID
        if big_blob is not None and big_blob.code() == blob_id:

            # Error between camera angle and target in pixels
            pixel_error = big_blob.cx() - self.cam.w_centre

            # Convert error to angle
            angle_error = -(pixel_error/sensor.width()*self.cam.h_fov)

            pid_error = self.PID.get_pid(angle_error,1)

            # Error between camera angle and target in ([deg])
            gimbal_angle = self.servo.gimbal_pos + pid_error

            # Move gimbal servo to track block
            self.servo.set_angle(gimbal_angle)

        return big_blob


    def reset(self) -> None:
        """
        Function to reset servos to zero positions
        """
        self.servo.soft_reset()


    def test(self, int: float) -> None:
        return None
