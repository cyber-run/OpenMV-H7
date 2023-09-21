import sensor, time

class Cam(object):
    """
    The Cam class manages the camera sensor for image capturing, processing,
    and color tracking. It initializes the camera parameters and sets the color
    thresholds for blob detection.
    """

    def __init__(self):
        """
        Initialise the Cam object by setting up camera parameters and
        configuring color thresholds.
        """
        # Configure camera settings
        sensor.reset()
        sensor.set_pixformat(sensor.RGB565)
        sensor.set_framesize(sensor.QVGA)   # Set frame size to 320x140
        sensor.skip_frames(time=2000)   # Allow the camera to adjust to light levels
    
        # Both must be turned off for color tracking
        sensor.set_auto_gain(False)
        sensor.set_auto_whitebal(False)

        # Correct orientation of image for upside down camera mounting
        sensor.set_vflip(True)
        sensor.set_hmirror(True)

        # Initialise sensor properties
        self.w_centre = sensor.width()/2
        self.h_centre = sensor.height()/2
        self.h_fov = 70.8
        self.clock = time.clock()

        # Define color tracking thresholds for Red, Green, Blue, and Yellow colors
        # Thresholds are in the order of (L Min, L Max, A Min, A Max, B Min, B Max)
        self.thresholds = [
            (30, 50, 50, 70, 40, 60), # Red
            (30, 80, -90, -50, 40, 80), # Green
            (15, 60, 20, 60, -100, -50), # Blue
            (15, 60, 20, 60, -100, -50), # Yellow
        ]

        # Define IDs for various tracked objects
        self.mid_line_id = 1
        self.l_line_id = 2
        self.r_line_id = 3
        self.obstacle_id = 4


    def get_blobs(self) -> tuple:
        """
        Capture an image and detect color blobs based on predefined thresholds.

        Returns:
            blobs (list): List of detected blobs.\n
            img (image): Captured image used to find blobs.
        """
        img = sensor.snapshot()

        blobs = img.find_blobs(self.thresholds,pixels_threshold=100,area_threshold=100,merge=True,)

        return blobs, img


    def get_big_blob(self, blobs, img):
        """
        Identify and return the largest blob from a list of detected blobs.
        Additionally, draw bounding boxes and centers on the identified blobs.

        Args:
            blobs (list): List of detected blobs.\n
            img (image): Image to draw bounding box and cross on blobs.

        Returns:
            big_blob (blob): The biggest blob from list - see OpenMV docs for blob class.
        """
        max_pixels = 0
        big_blob = None

        for blob in blobs:
            # Drawing bounding box and blob centres
            img.draw_rectangle(blob.rect())
            img.draw_cross(blob.cx(), blob.cy())

            # Update the big blob if the current blob has more pixels
            if blob.pixels() > max_pixels:
                max_pixels = blob.pixels()
                big_blob = blob

        return big_blob
