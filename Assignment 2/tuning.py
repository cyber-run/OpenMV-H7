from servos import *
from camera import *
from pid import PID
import os, time

class PanTuning(object):
    """
    A class for managing PID tuning, servo calibration, and camera adjustments.
    """

    def __init__(self, thresholds, gain = 25, p=0.22, i=0.0, d=0.0, imax=0.0):
        """
        Initialise the Tuning object with given PID parameters.

        Args:
            p (float): Proportional gain.
            i (float): Integral gain.
            d (float): Derivative gain.
            imax (float): Maximum Integral error.
        """
        self.servo = Servo()
        self.servo.soft_reset()
        self.cam = Cam(thresholds, gain)
        self.PID = PID(p, i, d, imax)

        self.min_angle = 0
        self.max_angle = 0
        self.targetmax_angle = 25
        self.targetmin_angle = -self.targetmax_angle


    def measure(self, freq):
        """
        Measures the tracking error and pan angle of the
        red square target for a specified frequency of oscillation.

        Args:
            freq (int): Frequency of oscillation in (Hz).
        """
        # Track 10 periods of oscillations
        t_run = 10/freq
        file_n = 0

        # Set up lists for data
        times = []
        errors = []
        angles = []
        times.append('time')
        errors.append('error')
        angles.append('angle')

        # Set up flag for searching for target
        flag = True

        # Check if calibration has been done
        self.calibrate()
        while ((self.min_angle > self.targetmin_angle) or
               (self.max_angle < self.targetmax_angle)):
            print('Calibration failed')
            print('Make sure you have calibrated thresholds')
            print('If you have, please put the robot closer to the screen!')
            self.calibrate()

        print('Calibration complete')
        # reset pan to max angle
        self.servo.set_angle(self.max_angle)

        while flag is True:
            # Get list of blobs and biggest blob
            blobs, img = self.cam.get_blobs()
            big_blob = self.cam.get_biggest_blob(blobs)

            # Check biggest blob is not None and is red for target then pass
            if big_blob is not None and self.cam.find_blob(big_blob, 0):
                flag = False

        # Setup times for freq test
        t_start = time.time()
        t_end =  t_start + t_run

        while time.time() < t_end:
            # Get new image and blocks
            # Get list of blobs and biggest blob
            blobs, img = self.cam.get_blobs()
            big_blob = self.cam.get_biggest_blob(blobs)

            if big_blob is not None and self.cam.find_blob(big_blob, 0):
                error, target_angle = self.update_pan(big_blob)

            times.append(time.time()-t_start)
            errors.append(error)
            angles.append(target_angle)

        data = [times,errors,angles]

        write_csv(data, freq)


    def calibrate(self):
        """
        Calibrate the pan positioning by setting max and min angles.
        Provides feedback during the process.
        """
        print('Please start the target tracking video')
        self.max_angle = 0
        self.min_angle = 0
        self.servo.set_angle(0)

        #  Set up clock for FPS and time tracking
        t_run = time.time()
        t_lost = t_run + 3

        # Loop until target is lost
        while t_run < t_lost:

            # Get list of blobs and biggest blob
            blobs, img = self.cam.get_blobs()
            big_blob = self.cam.get_biggest_blob(blobs)

            # Check biggest blob is not None and is blue for calibration
            if big_blob is not None and self.cam.find_blob(big_blob, 1):

                # track the calibration target
                error, pan_angle = self.update_pan(big_blob)

                # Update tuning curve parameters
                if error < 20:
                    if pan_angle < self.min_angle:
                        self.min_angle = pan_angle
                        print('New min angle: ', self.min_angle)
                    if pan_angle > self.max_angle:
                        self.max_angle = pan_angle
                        print('New max angle: ', self.max_angle)

                # As block was found reset lost timer
                t_lost = t_run + 1.5

            # Update run timer
            t_run = time.time()

            # print('FPS:           ',self.clock.fps())


    def update_pan(self, blob) -> tuple:
        """
        Adjust the camera pan by changing the servo angle based on the given blob's position.

        Args:
            blob (blob): Object retrieved from find_blobs - see OpenMV docs

        Returns:
            angle_error (float): The difference in angle between the blob and pan servo \n
            pan_angle (float): Angle of the pan wrt. heading

        """
        # Error between camera angle and target in pixels
        pixel_error = blob.cx() - self.cam.w_centre

        # Convert error to angle
        angle_error = -(pixel_error/sensor.width()*self.cam.h_fov)

        pid_error = self.PID.get_pid(angle_error,1)

        # Error between camera angle and target in ([deg])
        pan_angle = self.servo.pan_pos + pid_error

        # Move pan servo to track block
        self.servo.set_angle(pan_angle)

        return angle_error, pan_angle


def write_csv(data: tuple, freq: int) -> None:
    """
    Write tracking data to a CSV file.

    Args:
        data (tuple): Tuple containing lists of data to write to CSV file.\n
        freq (int): Frequency (Hz) for naming the file.
    """
    # Set file ext counter to 0
    file_n = 0

    print("Testing Finished")

    # Try making ./CSV directory if it doesn't exist
    try:
        os.mkdir("./CSV")
    except OSError as e:
        pass

    # Generate initial file name
    filename = "./CSV/Curve" + str(freq) + "Hz_" + str(file_n) + ".csv"

    # Check if file already exists and increment counter if it does
    while True:
        try:
            with open(filename, 'r'):
                pass
            # If file exists, increment the counter and try again
            file_n += 1
            filename = "./CSV/Curve" + str(freq) + "Hz_" + str(file_n) + ".csv"
        except OSError:
            # If file doesn't exist, break out of loop
            break

    print("Saving to:", filename)

    # HACK: Flushing buffer seems to fix file handling bugs - but test
    # Write data to csv file
    with open(filename, 'w') as file:
        file.flush() # Flush buffer

        # Transpose data for row-wise writing debug trailing comma
        for row in zip(*data):
            file.write(','.join(map(str, row)))
            file.write('\n')

        file.flush() # Flush buffer

    time.sleep_ms(1000)
    print("__Closing file__")
    print("Reset OpenMV camera in tools dropdown to load CSV")
