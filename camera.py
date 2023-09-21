import sensor, time

class Cam(object):
    """
    This class contains sensor settings and thresholds.
    """
    def __init__(self):
        """
        Initialises the camera object:
        Sets the camera params and thresholds for color tracking.
        """
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
            (15, 60, 20, 60, -100, -50), # Yellow
        ]

        self.mid_line_id = 1
        self.l_line_id = 2
        self.r_line_id = 3
        self.obstacle_id = 4


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
