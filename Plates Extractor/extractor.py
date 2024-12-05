import cv2
import numpy as np
import imutils
import os
from skimage.morphology import binary_erosion, binary_dilation, binary_closing, skeletonize, thin, square, disk, closing, opening

def save_image(image, filename):
    cv2.imwrite(filename, image)

def process_frame(frame, frame_count, index):
    frame = frame[50:, :]

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    smoothed_image = cv2.bilateralFilter(gray, 25, 95, 95)

    edged_image = cv2.Canny(smoothed_image, 80, 190)


    kernel = np.ones((1, 20), np.uint8)
    dilated_image = cv2.dilate(edged_image, kernel, iterations=1)

    eroded_image = cv2.erode(dilated_image, kernel, iterations=1)


    keypoints = cv2.findContours(eroded_image.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    contours = imutils.grab_contours(keypoints)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)

    location = []
    for contour in contours:
        approx = cv2.approxPolyDP(contour, 10, True)
        if len(approx) == 4:
            location.append(approx)

    if not location:
        print("No rectangles found in the frame.")
        return

    isolated_plate  = np.zeros_like(frame)

    for idx, loc in enumerate(location):
        mask = np.zeros_like(gray)
        cv2.drawContours(mask, [loc], -1, 255, thickness=cv2.FILLED)

        isolated_plate[mask == 255] = frame[mask == 255]

    isolated_plate_gray = cv2.cvtColor(isolated_plate, cv2.COLOR_BGR2GRAY)

    output_dir = "processed_images"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    save_image(frame, os.path.join(output_dir, f"frame_{index}_{frame_count}_original.jpg"))
    save_image(edged_image, os.path.join(output_dir, f"frame_{index}_{frame_count}edged.jpg"))
    save_image(isolated_plate_gray, os.path.join(output_dir, f"frame_{index}_{frame_count}_isolated_plate_gray.jpg"))
    save_image(dilated_image, os.path.join(output_dir, f"frame_{index}_{frame_count}_dilated.jpg"))

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
        except image_queue.empty:
            print("Queue is empty, waiting for more frames.")
        except Exception as e:
            print(f"Error processing frame: {e}")
