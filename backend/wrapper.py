from collections import Counter
import cv2
import os
import numpy as np
import imutils
from tkinter import Tk, filedialog, Button, Label, StringVar
from threading import Thread
from ocr import OCR
import skimage.io as io
KERNEL = np.ones((1, 20), np.uint8)
MIN_AREA = 500
output_dir = "processed_images"


def process_frame(frame, frame_count):
    try:
        frame = frame[50:, :]
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        smoothed_image = cv2.bilateralFilter(gray, 15, 50, 50)
        edged_image = cv2.Canny(smoothed_image, 130, 210)
        dilated_image = cv2.dilate(edged_image, KERNEL, iterations=1)

        keypoints = cv2.findContours(
            dilated_image.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours = imutils.grab_contours(keypoints)
        predictions_strs = []
        locations = []
        for contour in contours:
            if cv2.contourArea(contour) < MIN_AREA:
                continue
            approx = cv2.approxPolyDP(contour, 10, True)
            if len(approx) == 4:
                x, y, w, h = cv2.boundingRect(approx)
                if w >= 1.3 * h and w > 80 and h > 20:
                    roi = edged_image[y:y + h, x:x + w]
                    vertical_edges = cv2.Sobel(roi, cv2.CV_64F, 1, 0, ksize=3)
                    edge_density = np.sum(
                        np.abs(vertical_edges) > 100) / (w * h)
                    if edge_density > 0.2:
                        locations.append((x, y, w, h))

        for i, (x, y, w, h) in enumerate(locations):

            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 0), 2)
            cropped_image = frame[y:y + h, x:x + w]
            try:
                predictions = OCR(cropped_image)
                predictions_str = "".join(predictions)
                if len(predictions_str) == 6:
                    predictions_strs.append(predictions_str)
                    cv2.imwrite(f"output{predictions_str}.png", cropped_image)
                    print("found predictions", predictions_str)
            except:
                print("Error in frame prediction")
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            # output_path = os.path.join(
            #     output_dir, f"frame_{frame_count}_{w}_{h}_contour_{i}.png")
            # cv2.imwrite(output_path, cropped_image)
        return frame, predictions_strs
    except Exception as e:
        print(f"Error processing frame {frame_count}: {e}")
        return None, None


def process_video_stream(video_path, label_status):
    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            label_status.set("Error: Unable to open video.")
            return

        frame_count = 0
        skip_frames = 1
        combined_predictions = []
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            if frame_count % skip_frames == 0:
                processed_frame, predictions = process_frame(
                    frame, frame_count)
                combined_predictions.extend(predictions)
                if processed_frame is not None:
                    cv2.imshow('Processed Video Stream', processed_frame)

            frame_count += 1

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        cap.release()
        cv2.destroyAllWindows()
        label_status.set("Streaming complete.")
    except Exception as e:
        label_status.set(f"Error: {e}")
        cv2.destroyAllWindows()


def select_video():
    global video_path
    video_path = filedialog.askopenfilename(
        filetypes=[("Video Files", "*.mp4 *.avi *.mkv")])
    if video_path:
        label_status.set(f"Selected: {os.path.basename(video_path)}")


def start_processing():
    global video_path
    if not video_path:
        label_status.set("Please select a video first!")
        return
    label_status.set("Streaming...")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    Thread(target=process_video_stream, args=(
        video_path, label_status)).start()


if __name__ == "__main__":
    video_path = None
    root = Tk()
    root.title("Car Plate Detection")
    root.geometry("400x250")

    label_status = StringVar()
    label_status.set("Please select a video to process.")

    Label(root, text="Car Plate Detection", font=("Arial", 16)).pack(pady=10)
    Button(root, text="Select Video",
           command=select_video, width=20).pack(pady=5)
    Button(root, text="Start Processing",
           command=start_processing, width=20).pack(pady=5)
    Label(root, textvariable=label_status, wraplength=300,
          font=("Arial", 12)).pack(pady=10)

    root.mainloop()
