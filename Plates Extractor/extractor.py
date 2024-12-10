import cv2
import numpy as np
import imutils
import os
from skimage.morphology import binary_erosion, binary_dilation, binary_closing, skeletonize, thin, square, disk, closing, opening
import queue

def save_image(image, filename):
    cv2.imwrite(filename, image)

def process_frame(frame, frame_count, index):
    frame = frame[50:, :]

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    smoothed_image = cv2.bilateralFilter(gray, 35, 120, 120)

    edged_image = cv2.Canny(smoothed_image, 140, 190)


    kernel = np.ones((1, 20), np.uint8)
    dilated_image = cv2.dilate(edged_image, kernel, iterations=1)

    eroded_image = cv2.erode(dilated_image, kernel, iterations=1)


    keypoints = cv2.findContours(eroded_image.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    contours = imutils.grab_contours(keypoints)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)

    location = []
    # for contour in contours:
    #     approx = cv2.approxPolyDP(contour, 10, True)
    #     if len(approx) == 4:
    #         x, y, w, h = cv2.boundingRect(approx)
    #         if w >= 1.3 * h:
    #             location.append(approx)

    for contour in contours:
        approx = cv2.approxPolyDP(contour, 10, True)
        if len(approx) == 4:
            x, y, w, h = cv2.boundingRect(approx)
            if w >= 1.3 * h:
                roi = edged_image[y:y+h, x:x+w]  # Region of interest
                vertical_edges = cv2.Sobel(roi, cv2.CV_64F, 1, 0, ksize=3)
                vertical_edges = np.abs(vertical_edges)
                edge_density = np.sum(vertical_edges > 100) / (w * h)  # Normalize by area

                if edge_density > 0.1:  # Adjust the threshold as needed
                    location.append(approx)

    if not location:
        print("No rectangles found in the frame.")
        return

    isolated_plate  = np.zeros_like(frame)

    for idx, loc in enumerate(location):
        x, y, w, h = cv2.boundingRect(loc)
        margin = 5
        x_start = max(0, x - margin)
        y_start = max(0, y - margin)
        x_end = min(frame.shape[1], x + w + margin)
        y_end = min(frame.shape[0], y + h + margin)
        mask = np.zeros_like(gray)
        cv2.rectangle(mask, (x_start, y_start), (x_end, y_end), 255, thickness=cv2.FILLED)
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

def get_most_edged_area (frame, frame_count, index):
    frame = frame[50:, :]

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    smoothed_image = cv2.bilateralFilter(gray, 35, 120, 120)

    edged_image = cv2.Canny(smoothed_image, 140, 190)

    block_size = 50
    h, w = edged_image.shape
    max_density = 0
    best_region = None

    for y in range(0, h, block_size):
        for x in range(0, w, block_size):
            block = edged_image[y:y+block_size, x:x+block_size]
            total_pixels = block_size * block_size
            edge_pixels = cv2.countNonZero(block)
            edge_density = edge_pixels / total_pixels

            if edge_density > max_density:
                max_density = edge_density
                best_region = (x, y, block_size, block_size)

    if best_region is None:
        print("No region with significant edge density found.")
        return

    x, y, bw, bh = best_region
    texture = frame[y:y+bh, x:x+bw]

    output_dir = "processed_images"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    save_image(frame, os.path.join(output_dir, f"frame_{index}_{frame_count}_original.jpg"))
    save_image(edged_image, os.path.join(output_dir, f"frame_{index}_{frame_count}_edged.jpg"))
    save_image(texture, os.path.join(output_dir, f"frame_{index}_{frame_count}_highest_edge_texture.jpg"))

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
        except queue.Empty:
            print("Queue is empty, waiting for more frames.")
            break
        except Exception as e:
            print(f"Error processing frame: {e}")
