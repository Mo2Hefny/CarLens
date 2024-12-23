import skimage.io as io
from deskew_plate import deskew_img
from segment_characters import segment_characters
from finding_contour_plate import findContour
from predict_characters import predict_characters
from commonfunctions import show_images


def main():
    img = io.imread("plate.webp")
    contours, ROI = findContour(img)
    img = deskew_img(ROI, contour=contours)
    chrs, _ = segment_characters(img)
    show_images(chrs)

    predictions = predict_characters(chrs)
    print(predictions)
    return predictions


if __name__ == '__main__':
    print("doing ocr on image ", )
    main()
