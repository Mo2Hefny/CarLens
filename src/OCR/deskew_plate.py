import math
import cv2
import numpy as np
import logging


def distance(point1, point2):
    """Calculate Euclidean distance between two points."""
    return math.sqrt((point2[0] - point1[0]) ** 2 + (point2[1] - point1[1]) ** 2)


def calculate_left_right_points(corner_points):
    """
        Determines the bottom most left and right points
        Parameters:
            corner_points:  A list of four (x, y) tuples representing the corner points.
        Returns:
        tuple: A tuple containing:
            - left_idx (int): Index of the left point.
            - right_idx (int): Index of the right point.

    """

    bottom_most_idx = 0
    max_y = 0
    logging.info("finding the bottom most point")
    for idx, point in enumerate(corner_points):
        x, y = point
        if y > max_y:
            bottom_most_idx = idx
            max_y = y

    prev_idx = bottom_most_idx - 1 if bottom_most_idx > 0 else 3
    next_idx = bottom_most_idx + 1 if bottom_most_idx < 3 else 0

    logging.info("finding the width points of the rectangle")
    distance_to_prev = distance(
        corner_points[bottom_most_idx], corner_points[prev_idx])
    distance_to_next = distance(
        corner_points[bottom_most_idx], corner_points[next_idx])

    logging.info("finding the left/right point of the width")
    if distance_to_prev > distance_to_next:

        if corner_points[prev_idx][0] < corner_points[bottom_most_idx][0]:
            left_idx, right_idx = prev_idx, bottom_most_idx
        else:
            left_idx, right_idx = bottom_most_idx, prev_idx
    else:
        if corner_points[next_idx][0] < corner_points[bottom_most_idx][0]:
            left_idx, right_idx = next_idx, bottom_most_idx
        else:
            left_idx, right_idx = bottom_most_idx, next_idx

    return left_idx, right_idx


def find_rotation_angle(left_x, right_x, left_y, right_y):
    """
    find rotation angle 
      Args:
        left_x (float): The x-coordinate of the first point.
        right_x (float): The x-coordinate of the second point.
        left_y (float): The y-coordinate of the first point.
        right_y (float): The y-coordinate of the second point.

    Returns:
        float: The angle in degrees, calculated using the sine of the angle.
    """
    opp = right_y - left_y
    hyp = ((left_x - right_x) ** 2 + (left_y - right_y) ** 2) ** 0.5
    sin = opp / hyp
    theta = math.asin(sin) * (180 / math.pi)
    return theta


def deskew_img(cropped_img, contour):
    """
        Deskewing the licence plateimage by using Affine transformation 
        Parameters:
            cropped_img (numpy.ndarray): the cropped image of the exact licence plate
            contour (numpy.ndarray): set of four pivot contour points 
        Returns:
            Deskewd image of plate
    """

    if contour is None:
        logging.warning("No contour was found")
        return cropped_img
    logging.info("finding bottom most left and right points")
    contour = [item for sublist in contour for item in sublist]
    left, right = calculate_left_right_points(corner_points=contour)
    left_x = contour[left][0]
    left_y = contour[left][1]
    right_x = contour[right][0]
    right_y = contour[right][1]

    logging.info("finding the rotation angle")
    angle = find_rotation_angle(left_x, right_x, left_y, right_y)
    if angle > 20:
        return cropped_img
    # width and height (-1) in reverse order
    logging.info("Get center of image as (width/2)& (height/2)")
    image_center = tuple(np.array(cropped_img.shape[1::-1]) / 2)
    logging.info("Rotate image")
    rot_mat = cv2.getRotationMatrix2D(image_center, angle, 1.0)
    result = cv2.warpAffine(cropped_img, rot_mat,
                            cropped_img.shape[1::-1], flags=cv2.INTER_LINEAR)
    return result
