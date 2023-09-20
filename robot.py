from servos import *
from camera import *

class Robot():
    def __init__(self, servos, Cam):
        # Initialise servos and reset to zero positions
        self.servo = Servo()
        self.servo.soft_reset()

        # Initialise camera
        self.cam = Cam(self.servo)

        self.mid_line_id = 1
        self.l_line_id = 2
        self.r_line_id = 3
        self.obstacle_id = 4


    def drive(self, drive: float, bias: float) -> None:
        """
        Differntial drive function for the robot.
        
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


    def track_block(self) -> None:
        """
        Tracks the block using the camera and drives towards it.
        """
        # Get list of blobs and biggest blob
        blobs, img = self.cam.get_blobs()
        big_blob = self.cam.get_big_blob(blobs,img)

        # Check biggest blob is not None and is the blue for calibration
        if big_blob is not None and big_blob.code() == 4:
            # Check there is big_blob and for ID
            print('FPS:           ',self.clock.fps())


    def reset(self) -> None:
        """
        Function to reset servos to zero positions
        """
        self.servo.soft_reset()


    def test(self, int: float) -> None:
        return None