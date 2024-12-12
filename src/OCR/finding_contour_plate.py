import cv2
import logging


def findContour(img):
    """
        Identifies contour of potential licence plate of image 

        parameters:
            img : numpy.ndarray: image in BGR format
        returns:
            tuple of:
                numberPlateContour (numpy.ndarray): the contour of licence plate
                Region of Intrest (numpy.ndarray): the cropped licence plate image
    """

    logging.info("Converting image to grayscale.")
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    logging.info("Applying bilateral filter")
    gray = cv2.bilateralFilter(gray, 7, 17, 17)

    logging.info("Applying Canny edge detection")
    edged = cv2.Canny(gray, 170, 200)

    logging.info("Finding contours of the edges-only image")
    cnts = cv2.findContours(edged.copy(), cv2.RETR_LIST,
                            cv2.CHAIN_APPROX_SIMPLE)[0]

    logging.info("kgetiing the largest 30 contours")
    cnts = sorted(cnts, key=cv2.contourArea, reverse=True)[:30]
    NumberPlateContour = None
    logging.info(
        "finding first closed contour and applying a bounding rectange to it")

    for c in cnts:
        perimeter = cv2.arcLength(c, closed=True)
        approx = cv2.approxPolyDP(c, epsilon=0.02 * perimeter, closed=True)
        if len(approx) == 4:
            NumberPlateContour = approx
            x, y, w, h = cv2.boundingRect(c)
            ROI = img[y:y+h, x:x+w].copy()
            return (NumberPlateContour, ROI)

    logging.warning("No contour with 4 corners found.")
    return None, None
