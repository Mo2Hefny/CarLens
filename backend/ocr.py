import skimage.io as io
from deskew_plate import deskew_img
from segment_characters import segment_characters
from finding_contour_plate import findContour
from predict_characters import predict_characters


def OCR(img):
    contours, ROI = findContour(img)
    img = deskew_img(ROI, contour=contours)
    try:
        chrs, _ = segment_characters(img)

        predictions = predict_characters(chrs)
    except Exception as e:
        print("Error in OCR", e)
    return predictions


# if __name__ == '__main__':
#     print("doing ocr on image ", )
#     main()
