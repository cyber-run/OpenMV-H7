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


    def calibrate(self):
        print("Please start the target tracking video")
        self.max_angle = 0
        self.min_angle = 0
        self.servoBot.set_angle(0)

        while True:
            self.clock.tick()
            img = sensor.snapshot()

            # Loop through all the blobs found - set thesholds and merge nearby blobs
            for blob in img.find_blobs(
                self.thresholds,
                pixels_threshold=100,
                area_threshold=100,
                merge=True,
            ):
                # Drawing bounding box and blob centres
                img.draw_rectangle(blob.rect())
                img.draw_cross(blob.cx(), blob.cy())

                t_lost = time()                


                while t_lost < time:
                    if blob.code() == 4:
                        print('-----Calibration begun-----')

                        # track the calibration target
                        error, target_angle = self.update_gimbal(blob)

                        # Update tuning curve parameters
                        if error < 20:
                            if target_angle < self.targetmin_angle:
                                self.targetmin_angle = target_angle
                                print('New min angle: ', self.targetmin_angle)
                            if target_angle > self.targetmax_angle:
                                self.targetmax_angle = target_angle
                                print('New max angle: ', self.targetmax_angle)

                        t_lost = time()


                self.update_gimbal(blob)

                # Print info for debug
                print('Block ID:     ',blob.code())
                # print('X-value:      ',blob.cx())
                # print('Blob angle:   ',blob_angle)
                # print('Output:       ',output)
                # print('Angle error:  ',error)
                # print('Gimbal angle: ',self.servoBot.gimbal_pos)
                # print('FPS:          ',self.clock.fps())


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

