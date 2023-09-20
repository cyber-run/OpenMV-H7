import sensor, time, os, pyb
from servos import *
from pid import PID

class Cam(object):
    """
    This class contains sensor settings and PID initialisation
    for tuning the robot gimbal to track a target.
    """
    def __init__(self, Servo):
        """
        Initialises the camera object.

        Args:
            `servo` (servo): Servo object required object to control gimbal
        """
        self.servo = Servo
        self.servo.set_angle(0)
        self.PID = PID(p=0.22, i=0, d=0, imax=0)

        # Set up camera sensor for capture
        sensor.reset()
        sensor.set_pixformat(sensor.RGB565)
        sensor.set_framesize(sensor.QVGA) # 320x140
        sensor.skip_frames(time=2000) # Skip frames on script load
        # Both must be turned off for color tracking
        sensor.set_auto_gain(False)
        sensor.set_auto_whitebal(False)

        # Correct orientation of image for upside down camera mounting
        sensor.set_vflip(True)
        sensor.set_hmirror(True)

        # Init sensor dims, FOV and clock
        self.w_centre = sensor.width()/2
        self.h_centre = sensor.height()/2
        self.h_fov = 70.8
        self.clock = time.clock()

        # Color Tracking Thresholds (L Min, L Max, A Min, A Max, B Min, B Max)
        # The below thresholds track red/green/blue
        self.thresholds = [
            (15, 60, 70, 85, 55, 70), # Red
            (30, 80, -90, -50, 40, 80), # Green
            (15, 60, 20, 60, -100, -50), # Blue
        ]

        # tuning curve parameters
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
            blobs, img = self.get_blobs()
            big_blob = self.get_big_blob(blobs,img)

            # Check biggest blob is not None and is red for target then pass
            if big_blob is not None and big_blob.code() == 1:
                flag = False

        # Setup times for freq test
        t_start = self.get_time()
        t_end =  t_start + t_run

        while self.get_time() < t_end:
            # Get new image and blocks
            # Get list of blobs and biggest blob
            blobs, img = self.get_blobs()
            big_blob = self.get_big_blob(blobs,img)

            if big_blob is not None and big_blob.code() == 1:
                error, target_angle = self.update_gimbal(big_blob)

            times.append(self.get_time()-t_start)
            errors.append(error)
            angles.append(target_angle)

        data = [times,errors,angles]

        self.write_csv(data, freq)


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
        t_run = self.get_time()
        t_lost = t_run + 3

        # Loop until target is lost
        while t_run < t_lost:

            # Get list of blobs and biggest blob
            blobs, img = self.get_blobs()
            big_blob = self.get_big_blob(blobs,img)

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
            t_run = self.get_time()

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
        pixel_error = blob.cx() - self.w_centre

        # Convert error to angle
        angle_error = -(pixel_error/sensor.width()*self.h_fov)

        pid_error = self.PID.get_pid(angle_error,1)

        # Error between camera angle and target in ([deg])
        gimbal_angle = self.servo.gimbal_pos + pid_error

        # Move gimbal servo to track block
        self.servo.set_angle(gimbal_angle)

        return angle_error, gimbal_angle


    def get_blobs(self):
        """
        Gets blobs from image snapshot.

        Returns:
            `blobs` (list): list of blobs \n
            `img` (image): image from snapshot used to find blobs
        """
        img = sensor.snapshot()

        blobs = img.find_blobs(self.thresholds,pixels_threshold=100,area_threshold=100,merge=True,)

        return blobs, img


    def get_big_blob(self, blobs, img):
        """
        Get the biggest blob from a list of blobs.

        Args:
            `blobs` (list): list of blobs \n
            `img` (image): image to draw bounding box and cross on blobs

        Returns:
            `big_blob` (blob): the biggest blob from list - see OpenMV docs for blob class
        """
        pixel = 0
        big_blob = None
        for blob in blobs:
            # Drawing bounding box and blob centres
            img.draw_rectangle(blob.rect())
            img.draw_cross(blob.cx(), blob.cy())
            if blob.pixels() > pixel:
                pixel = blob.pixels()
                big_blob = blob

        return big_blob


    def write_csv(self, data: tuple, freq: int) -> None:
        """
        Write tracking data to a csv file. \n

        Args:
            `data` (tuple): lists of data to write to csv file.\n
            `freq` (int): frequency data for naming the file.
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


    def get_time(self) -> float:
        """
        Gets the time in seconds - since the OpenMV was last reset.
        """
        return pyb.millis()/1000
