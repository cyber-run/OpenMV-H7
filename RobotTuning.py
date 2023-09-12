import sensor, time, os
from servoBot import *
from pid import PID

class RobotTuning(object):
    def __init__(self, servoBot):
        self.servoBot = servoBot
        self.servoBot.set_angle(0)
        self.PID = PID(p=0.15, i=0, d=0, imax=0)

        # Set up camera sensor for capture
        sensor.reset()
        sensor.set_pixformat(sensor.RGB565)
        sensor.set_framesize(sensor.QVGA) # 320x140
        sensor.skip_frames(time=1000) # Skip frames on script load
        sensor.set_auto_gain(False)  # must be turned off for color tracking
        sensor.set_auto_whitebal(False)  # must be turned off for color tracking

        # Orientation of image for upside down camera mounting
        sensor.set_vflip(True)
        sensor.set_hmirror(True)
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
        self.servoBot.set_angle(self.max_angle)

        while flag is True:
            # Get list of blobs and biggest blob
            blobs, img = self.get_blobs()
            big_blob = self.get_big_blob(blobs,img)

            # Check biggest blob is not None and is red for target then pass
            if big_blob is not None and big_blob.code() == 1:
                flag = False

        # Setup times for freq test
        t_start = time.time()
        t_end =  t_start + t_run

        while time.time() < t_end:
            # Get new image and blocks
            # Get list of blobs and biggest blob
            blobs, img = self.get_blobs()
            big_blob = self.get_big_blob(blobs,img)

            if big_blob is not None and big_blob.code() == 1:
                error, target_angle = self.update_gimbal(big_blob)
            else:
                print('Target lost')

            times.append(time.time()-t_start)
            errors.append(error)
            angles.append(target_angle)

        data = [times,errors,angles]

        print('Testing finished - writing .csv')

        try:
           os.mkdir("./CSV")
        except OSError as e:
           print("Directory exists")

        file_name = "./CSV/Curve" + str(freq) + "Hz_" + str(file_n) + ".csv"

        while self.file_exists(file_name):
            file_n += 1
            file_name = "./CSV/Curve" + str(freq) + "Hz_" + str(file_n) + ".csv"

        with open(file_name, 'w') as file:
            for i in data:
                for j in i:
                    file.write(str(j) + ',')
                file.write('\n')

        file.close()


    def calibrate(self):
        print('Please start the target tracking video')
        self.max_angle = 0
        self.min_angle = 0
        self.servoBot.set_angle(0)

        #  Set up clock for FPS and time tracking
        t_run = time.time()
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
                print('Target', gimbal_angle)

                # Update tuning curve parameters
                if error < 20:
                    if gimbal_angle < self.min_angle:
                        self.min_angle = gimbal_angle
                        print('New min angle: ', self.min_angle)
                    if gimbal_angle > self.max_angle:
                        self.max_angle = gimbal_angle
                        print('New max angle: ', self.max_angle)

                # As block was found reset lost timer
                t_lost = t_run + 3

            # Update run timer
            t_run = time.time()

            # print('FPS:           ',self.clock.fps())


    # output        - tracking error in ([deg]) and new camera angle in ([deg]) (tuple)
    def update_gimbal(self,blob):
        # Error between camera angle and target in pixels
        pixel_error = blob.cx() - self.w_centre

        # Convert error to angle
        angle_error = -(pixel_error/sensor.width()*self.h_fov)

        pid_error = self.PID.get_pid(angle_error,1)

        # Error between camera angle and target in ([deg])
        gimbal_angle = self.servoBot.gimbal_pos + pid_error

        # Move gimbal servo to track block
        self.servoBot.set_angle(gimbal_angle)

        return angle_error, gimbal_angle


    def get_blobs(self):
        img = sensor.snapshot()

        blobs = img.find_blobs(self.thresholds,pixels_threshold=100,area_threshold=100,merge=True,)

        return blobs, img


    def get_big_blob(self,blobs,img):
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


    # Check if file exists and return True or False
    def file_exists(self, filename):
        try:
            with open(filename, 'r'):
                pass
            return True
        except OSError:
            return False
