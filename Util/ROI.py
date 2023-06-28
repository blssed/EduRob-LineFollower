import numpy as np
import cv2 as cv


class ROI:
    area = 0
    vertices = None

    def init_roi(self, width, height):
        """
        Initialise the region of interest
        :param width: width of the analysed image
        :param height: height of the analysed image
        :return: none
        """
        vertices = [(0, height), (width / 4, height / 2), (3 * width / 4, height / 2), (width, height), ]
        self.vertices = np.array([vertices], np.int32)

        blank = np.zeros((height, width, 3), np.uint8)
        blank[:] = (255, 255, 255)
        blank_gray = cv.cvtColor(blank, cv.COLOR_BGR2GRAY)
        blank_cropped = self.crop_roi(blank_gray)
        self.area = cv.countNonZero(blank_cropped)

    def crop_roi(self, img):
        """
        :param img: input image to crop the region of interest on
        :return: filled roi image
        """
        mask = np.zeros_like(img)
        match_mask_color = 255

        cv.fillPoly(mask, self.vertices, match_mask_color)
        masked_image = cv.bitwise_and(img, mask)
        return masked_image

    def get_area(self):
        """
        :return: returns the area
        """
        return self.area

    def get_vertices(self):
        """
        :return: returns the vertices
        """
        return self.vertices
