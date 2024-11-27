import cv2
import numpy as np
import imutils
import os
from skimage.morphology import binary_erosion, binary_dilation, binary_closing, skeletonize, thin, square, disk, closing, opening

def save_image(image, filename):
    cv2.imwrite(filename, image)

def process_frame(frame, frame_count, index):
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    smoothed_image = cv2.bilateralFilter(gray, 3, 40, 40)
    edged_image = cv2.Canny(smoothed_image, 85, 200)

    keypoints = cv2.findContours(edged_image.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    contours = imutils.grab_contours(keypoints)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:10]

    location = None
    for contour in contours:
        approx = cv2.approxPolyDP(contour, 10, True)
        if len(approx) == 4:
            location = approx
            break

    if location is None:
        print("No rectangles found in the frame.")
        return

    mask = np.zeros(gray.shape, np.uint8)
    isolated_plate = cv2.drawContours(mask, [location], 0, 255, -1)
    isolated_plate = cv2.bitwise_and(frame, frame, mask=mask)

    (x, y) = np.where(mask == 255)
    (x1, y1) = (np.min(x), np.min(y))
    (x2, y2) = (np.max(x), np.max(y))
    cropped_image = gray[x1:x2 + 1, y1:y2 + 1]

    # Save the images with unique filenames
    output_dir = "processed_images"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    save_image(gray, os.path.join(output_dir, f"frame_{index}_{frame_count}_gray.jpg"))
    save_image(cropped_image, os.path.join(output_dir, f"frame_{index}_{frame_count}_cropped.jpg"))

    print(f"Saved images for frame {frame_count}")

def image_consumer(image_queue, index):
    frame_count = 0

    while True:
        try:
            frame = image_queue.get(timeout=10)  # Adjust timeout as needed
            if frame is None:
                print("No frame to process, exiting.")
                break

            frame_count += 1
            print(f"Processing frame {frame_count}...")
            process_frame(frame, frame_count,index)
            print(f"Frame {frame_count} processed and saved.")
        except image_queue.Empty:
            print("Queue is empty, waiting for more frames.")
        except Exception as e:
            print(f"Error processing frame: {e}")
