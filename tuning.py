from servos import *
from camera import *
from pid import PID
import os

class Tuning(object):
    """
    This class contains PID initialisation, servo tuning and camera tuning
    """
    def __init__(self, p=0.22, i=0.0, d=0.0, imax=0.0):
        # Initialise servos and reset to zero positions
        self.servo = Servo()
        self.servo.soft_reset()

        # Initialise camera
        self.cam = Cam()

        # Tuning parameters
        self.PID = PID(p, i, d, imax)

        self.min_angle = 0
        self.max_angle = 0
        self.targetmax_angle = 25
        self.targetmin_angle = -self.targetmax_angle


    def measure(self, freq):
        """
        This function measures the tracking error and gimbal angle of the
        red square target for a given frequency of oscillation.

        Args:
            `freq` (int): frequency of oscillation in [Hz]
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
        # reset gimbal to max angle
        self.servo.set_angle(self.max_angle)

        while flag is True:
            # Get list of blobs and biggest blob
            blobs, img = self.cam.get_blobs()
            big_blob = self.cam.get_big_blob(blobs,img)

            # Check biggest blob is not None and is red for target then pass
            if big_blob is not None and big_blob.code() == 1:
                flag = False

        # Setup times for freq test
        t_start = get_time()
        t_end =  t_start + t_run

        while get_time() < t_end:
            # Get new image and blocks
            # Get list of blobs and biggest blob
            blobs, img = self.cam.get_blobs()
            big_blob = self.cam.get_big_blob(blobs,img)

            if big_blob is not None and big_blob.code() == 1:
                error, target_angle = self.update_gimbal(big_blob)

            times.append(get_time()-t_start)
            errors.append(error)
            angles.append(target_angle)

        data = [times,errors,angles]

        write_csv(data, freq)


    def calibrate(self):
        """
        Method to calibrate the gimbal for position - sets the max and min
        angles in cam object and makes sure they're sufficient
        """
        print('Please start the target tracking video')
        self.max_angle = 0
        self.min_angle = 0
        self.servo.set_angle(0)

        #  Set up clock for FPS and time tracking
        t_run = get_time()
        t_lost = t_run + 3

        # Loop until target is lost
        while t_run < t_lost:

            # Get list of blobs and biggest blob
            blobs, img = self.cam.get_blobs()
            big_blob = self.cam.get_big_blob(blobs,img)

            # Check biggest blob is not None and is the blue for calibration
            if big_blob is not None and big_blob.code() == 4:

                # track the calibration target
                error, gimbal_angle = self.update_gimbal(big_blob)

                # Update tuning curve parameters
                if error < 20:
                    if gimbal_angle < self.min_angle:
                        self.min_angle = gimbal_angle
                        print('New min angle: ', self.min_angle)
                    if gimbal_angle > self.max_angle:
                        self.max_angle = gimbal_angle
                        print('New max angle: ', self.max_angle)

                # As block was found reset lost timer
                t_lost = t_run + 1.5

            # Update run timer
            t_run = get_time()

            # print('FPS:           ',self.clock.fps())


    def update_gimbal(self, blob):
        """
        Updates the camera gimbal - changing the servo angle to
        track the blob passed into method.

        Args:
            `blob` (blob): object retrieved from find_blobs - see OpenMV docs

        Returns:
            `angle_error` (float): The differnce in angle between the blob
            and gimbal heading \n
            `gimbal_angle` (float): Angle of the gimbal wrt. heading

        """
        # Error between camera angle and target in pixels
        pixel_error = blob.cx() - self.cam.w_centre

        # Convert error to angle
        angle_error = -(pixel_error/sensor.width()*self.cam.h_fov)

        pid_error = self.PID.get_pid(angle_error,1)

        # Error between camera angle and target in ([deg])
        gimbal_angle = self.servo.gimbal_pos + pid_error

        # Move gimbal servo to track block
        self.servo.set_angle(gimbal_angle)

        return angle_error, gimbal_angle


def write_csv(data: tuple, freq: int) -> None:
    """
    Write tracking data to a csv file. \n

    Args:
        `data` (tuple): lists of data to write to csv file.\n
        `freq` (int): frequency (Hz) for naming the file.
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

    pyb.delay(1000)
    print("__Closing file__")
    print("Reset OpenMV camera in tools dropdown to load CSV")
