from segment_characters import segment_characters
from finding_contour_plate import findContour
from predict_characters import predict_characters
from deskew_plate import deskew_img
from skimage import io
import sys
import os
sys.path.append(os.path.join)


def OCR(img):
    contours, ROI = findContour(img)
    img = deskew_img(ROI, contour=contours)
    try:
        chrs, _ = segment_characters(img)

        predictions = predict_characters(chrs)
    except Exception as e:
        print("Error in OCR", e)
    return predictions


if __name__ == '__main__':
    print("doing ocr on image ", )
    image_path = input("Enter image path: ")
    img = io.imread(image_path)
    OCR(img)
