import cv2
import logging
import numpy as np
from skimage.feature import hog
from skimage.morphology import skeletonize


import numpy as np
import os


def calculate_hu_moments(image):
    """Calculate Hu Moments from image."""

    moments = cv2.moments(image)

    hu_moments = cv2.HuMoments(moments)
    hu_moments = np.where(hu_moments == 0, 1e-10, hu_moments)

    return np.log(np.abs(hu_moments)).flatten()


def extract_hog_features(image):
    features = hog(image, orientations=9, pixels_per_cell=(8, 8),
                   cells_per_block=(2, 2), channel_axis=None)
    return features


def extract_zoning_features(image, grid_size=(3, 3)):
    """
    Extract zoning features from an image.

    Parameters:
    - image: Grayscale image (2D array).
    - grid_size: Tuple indicating the grid size (rows, cols).

    Returns:
    - features: 1D numpy array of zoning features.
    """

    zone_height = image.shape[0] // grid_size[0]
    zone_width = image.shape[1] // grid_size[1]

    features = []

    for i in range(grid_size[0]):
        for j in range(grid_size[1]):
            zone = image[
                i * zone_height:(i + 1) * zone_height,
                j * zone_width:(j + 1) * zone_width
            ]
            zone_feature = np.sum(zone) / (zone_height * zone_width)
            features.append(zone_feature)

    return np.array(features)


def extract_edge_direction_features(image):

    grad_x = cv2.Sobel(image, cv2.CV_64F, 1, 0, ksize=3)
    grad_y = cv2.Sobel(image, cv2.CV_64F, 0, 1, ksize=3)

    magnitude, direction = cv2.cartToPolar(grad_x, grad_y, angleInDegrees=True)

    direction = direction / 360

    direction_features = direction.flatten()

    return direction_features


def extract_combined_features(image):
    binary_bool = image.astype(bool)

    skeleton = skeletonize(binary_bool)

    skeleton_uint8 = (skeleton * 255).astype(np.uint8)

    hu_moments = calculate_hu_moments(skeleton_uint8)
    hog_features = extract_hog_features(image)
    edge_dirs = extract_edge_direction_features(image)
    zoning = extract_zoning_features(image)
    combined_features = np.hstack(
        [hog_features, hu_moments, edge_dirs, zoning])  # Combine
    return combined_features
