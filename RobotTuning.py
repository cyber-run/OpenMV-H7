import sensor, time, math
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
        sensor.skip_frames(time=500) # Skip frames on script load
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
        self.targetmax_angle = 30
        self.targetmin_angle = -self.targetmin_angle


    def measure(self, freq):
        # Track 10 periods of oscillations
        t_run = 10/freq
        file_n = 0

        times = [], errors = [], angles = []
        times.append('time')
        errors.append('error')
        angles.append('angle')
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

        while flag == True:
            blobs, big_blob = self.get_blobs()

            if big_blob.code() == 1:
                flag == False

        # Setup times for freq test                
        t_start = time()
        t_end =  t_start + t_run

        while time() < t_end:
            # Get new image and blocks
            blobs = self.get_blobs()
            big_blob = self.get_biggest_blob(blobs)

            error, target_angle = self.update_gimbal(big_blob)

            times.append(time()-t_start)
            errors.append(error)
            angles.append(target_angle)

        data = [times,errors,target_angle]
        
        print('Testing finished - writing .csv')
        file_name = "Curve" + str(freq) + "Hz_" + str(file_n) + ".csv"
        with open(file_name, 'w') as file:
            for i in data:
                for j in i:
                    file.write(str(j) + ',')
                file.write('\n')
            

    def calibrate(self):
        print('Please start the target tracking video')
        self.max_angle = 0
        self.min_angle = 0
        self.servoBot.set_angle(0)

        #  Set up clock for FPS and time tracking
        self.clock.tick()
        t_lost = time() + 2

        # Loop until target is lost
        while time() < t_lost:

            # Get list of blobs and biggest blob
            blobs, big_blob = self.get_blobs()
       
            # Check if blob is the blue for calibration
            if big_blob.code() == 4:

                # track the calibration target
                error, target_angle = self.update_gimbal(big_blob)

                # Update tuning curve parameters
                if error < 20:
                    if target_angle < self.targetmin_angle:
                        self.targetmin_angle = target_angle
                        print('New min angle: ', self.targetmin_angle)
                    if target_angle > self.targetmax_angle:
                        self.targetmax_angle = target_angle
                        print('New max angle: ', self.targetmax_angle)

                t_lost = time()

            # Print info for debug
            print('Block ID:      ',big_blob.code())
            print('Target angle:  ',target_angle)
            print('Gimbal angle:  ',self.servoBot.gimbal_pos)
            print('FPS:           ',self.clock.fps())


    # output        - tracking error in ([deg]) and new camera angle in ([deg]) (tuple)
    def update_gimbal(self,blob):
        # Error between camera angle and target in pixels
        pixel_error = blob.cx() - self.w_centre

        # Convert error to angle
        angle_error = -(pixel_error/sensor.width()*self.h_fov)

        pid_error = self.PID.get_pid(angle_error,1)

        # Error between camera angle and target in ([deg])
        target_angle = self.servoBot.gimbal_pos + pid_error

        # Move gimbal servo to track block
        self.servoBot.set_angle(target_angle)

        return (angle_error, target_angle)


    def get_blobs(self):
        pixel = 0
        big_blob = blobs[0]

        img = sensor.snapshot()
        # Drawing bounding box and blob centres
        blobs = img.find_blobs(
                    self.thresholds,
                    pixels_threshold=100,
                    area_threshold=100,
                    merge=True,
                )
        
        # Find largest blob by pixels
        # Could do area, but this is more likely accurate
        
        for blob in blobs:
            img.draw_rectangle(blob.rect())
            img.draw_cross(blob.cx(), blob.cy()) 
            if blob.pixels() > pixel:  
                pixel = blob.pixels()
                big_blob = blob
        
        return blobs, big_blob
    