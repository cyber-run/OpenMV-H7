from servos import *
from camera import *
from pid import PID
import sensor

class Robot(object):
    """
    A class to manage the functions of a robot for driving and tracking purposes using a camera and servos.
    """

    def __init__(self, thresholds, gain = 25, p=0.22, i=0.0, d=0.0, imax=0.0):
        """
        Initializes the Robot object with given PID parameters.

        Args:
            p (float): Proportional gain for the PID.
            i (float): Integral gain for the PID.
            d (float): Derivative gain for the PID.
            imax (float): Maximum Integral error for the PID.
        """

        self.servo = Servo()
        self.servo.soft_reset()
        self.cam = Cam(thresholds, gain)
        self.PID = PID(p, i, d, imax)


    def follow_blob(self, speed: float, threshold_idx: int) -> None:
        """
        Follows a blob using the camera and drives towards it.
        """
        while True:
            # Track red line
            big_blob = self.track_blob(threshold_idx)

            if big_blob is not None:
                # Get heading angle
                heading_angle = self.servo.pan_pos

                # Convert to angle correction weight (between -1 and 1)
                angle_correction = heading_angle/self.servo.max_deg

                # Drive towards line
                self.drive(speed, angle_correction)
            else:
                self.drive(0, 0)
                print('Correct blob not found')


    def track_blob(self, threshold_idx: int):
        """
        Adjust the camera pan angle to track a specified blob based on its ID.

        Args:
            blob_id (int): The ID of the blob to track.

        Returns:
            blob: The blob object tracked, if found. Otherwise, returns None.
        """
        # Get list of blobs and biggest blob
        blobs, img = self.cam.get_blobs()
        big_blob = self.cam.get_biggest_blob(blobs)

        # Check biggest blob is not None and is the defined ID
        if big_blob is not None and self.cam.find_blob(big_blob, threshold_idx):

            # Error between camera angle and target in pixels
            pixel_error = big_blob.cx() - self.cam.w_centre

            # Convert error to angle
            angle_error = -(pixel_error/sensor.width()*self.cam.h_fov)

            pid_error = self.PID.get_pid(angle_error,1)

            # Error between camera angle and target in ([deg])
            pan_angle = self.servo.pan_pos + pid_error

            # Move pan servo to track block
            self.servo.set_angle(pan_angle)

            return big_blob
        else:
            print('Correct blob not found')
            return None


    def drive(self, speed: float, bias: float) -> None:
        """
        Resets the servo positions to their default states.
        """
        self.servo.set_differential_drive(speed, bias)


    def reset(self) -> None:
        """
        Resets the servo positions to their default states.
        """
        self.servo.soft_reset()


    def test(self, int: float) -> None:
        """
        A test function for the Robot. Currently not implemented.
        
        Args:
            int (float): A sample input parameter for the test function.
        """
        pass
