import cv2
import numpy as np
import logging


def preprocess_license_plate(image):
    """
    Preprocess the input license plate image:
    - Resize to a fixed size
    - Convert to grayscale
    - Apply binary thresholding and morphological operations
    Parameters: 
        image (numpy.ndarray: a colored license plate image)
    Returns:
        binary image
    """
    logging.info("Resize the image for consistency")
    resized_img = cv2.resize(image, (333, 75))

    logging.info("Convert to grayscale")
    gray_img = cv2.cvtColor(resized_img, cv2.COLOR_BGR2GRAY)

    logging.info("Apply binary thresholding")
    _, binary_img = cv2.threshold(
        gray_img, 200, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    logging.info("Morphological operations to reduce noise")
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    binary_img = cv2.erode(binary_img, kernel, iterations=1)
    binary_img = cv2.dilate(binary_img, kernel, iterations=1)

    logging.info(
        "Make borders white to avoid detecting contours near the edges")
    binary_img[:3, :] = 255
    binary_img[-3:, :] = 255
    binary_img[:, :3] = 255
    binary_img[:, -3:] = 255
    return binary_img


def extract_character_contours(binary_img, numChars=6):
    """
    Extract contours from the binary image and filter them based on size.
        Parameters: 
            binary_image (np.ndarray): binary image
            numChars (int): expected number of chars in image
        Returns:
            character_contours (list(numpy.ndarray)): sorted array of characyer contours from left to right

    """
    logging.info("Define estimated dimensions for character contours")
    height, width = binary_img.shape
    dimensions = {
        "min_height": height / 3,
        "max_height": height / 1,
        "min_width": width / (numChars * 2),
        "max_width": width / 3
    }

    logging.info("Find contours in the binary image")
    contours, _ = cv2.findContours(
        binary_img, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    character_contours = []
    logging.info("Filter contours based on size")
    logging.info("Sort contours by x-coordinate to ensure left-to-right order")
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)

        if dimensions["min_width"] < w < dimensions["max_width"] and dimensions["min_height"] < h < dimensions["max_height"]:
            character_contours.append((x, y, w, h))

    character_contours = sorted(character_contours, key=lambda c: c[0])

    return character_contours


def sharpen_image(image):
    """
        remove gaussian blurring from extracted chars
        Parameters:
            image (numpy.ndarray): binary char image
        Returns: 
            sharpened image
    """
    kernel = np.array([[0, -1,  0],
                       [-1,  5, -1],
                       [0, -1,  0]])

    # Apply the kernel to the image using cv2.filter2D
    sharpened = cv2.filter2D(image, -1, kernel)

    return sharpened


def segment_characters(image):
    """
    Segment characters from the license plate image.
        Parameters:
            image (numpy.ndarray): colored image of license plate 
        returns: 
            tuple of:
                charaters (list(numpy.ndarray)): list of character images
                character_contours (list(numpy.ndarray)): list of sorted character contours
    """
    logging.info("Preprocess the image")
    binary_img = preprocess_license_plate(image)

    logging.info("Extract character contours")
    character_contours = extract_character_contours(binary_img)

    logging.info("Crop and resize individual characters")
    characters = []
    for (x, y, w, h) in character_contours:
        char_img = binary_img[y:y + h, x:x + w]
        char_img_resized = cv2.resize(
            char_img, (42, 28))  # Resize to standard size
        char_img_resized = sharpen_image(char_img_resized)
        characters.append(char_img_resized)

    return characters, character_contours
