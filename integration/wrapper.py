import cv2
import os
import numpy as np
import imutils
from tkinter import Tk, filedialog, Button, Label, StringVar
from threading import Thread

def process_frame(frame, frame_count, index):
    try:
        print(f"Starting processing for frame {frame_count}...")
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

        for contour in contours:
            approx = cv2.approxPolyDP(contour, 10, True)
            if len(approx) == 4:
                x, y, w, h = cv2.boundingRect(approx)
                if w >= 1.3 * h:
                    roi = edged_image[y:y + h, x:x + w]
                    vertical_edges = cv2.Sobel(roi, cv2.CV_64F, 1, 0, ksize=3)
                    edge_density = np.sum(np.abs(vertical_edges) > 100) / (w * h)
                    if edge_density > 0.1:
                        location.append((x, y, w, h))

        for (x, y, w, h) in location:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

        print(f"Completed processing for frame {frame_count}.")
        return frame
    except Exception as e:
        print(f"Error processing frame {frame_count}: {e}")
        return None


def process_video(video_path, output_path, label_status):
    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            label_status.set("Error: Unable to open video.")
            return

        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)

        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        out = cv2.VideoWriter(output_path, fourcc, fps, (frame_width, frame_height))

        frame_count = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            processed_frame = process_frame(frame, frame_count, index=1)

            if processed_frame is not None:
                out.write(processed_frame) 

                cv2.imshow('Processed Video', processed_frame)

            frame_count += 1

            if cv2.waitKey(1) & 0xFF == ord('q'):  # Press 'q' to exit
                break

        cap.release()
        out.release()
        cv2.destroyAllWindows() 
        label_status.set(f"Processing complete! Video saved to {output_path}.")
    except Exception as e:
        label_status.set(f"Error: {e}")
        cv2.destroyAllWindows()


def select_video():
    global video_path
    video_path = filedialog.askopenfilename(filetypes=[("Video Files", "*.mp4 *.avi *.mkv")])
    if video_path:
        label_status.set(f"Selected: {os.path.basename(video_path)}")


def start_processing():
    global video_path
    if not video_path:
        label_status.set("Please select a video first!")
        return

    output_path = filedialog.asksaveasfilename(defaultextension=".avi", filetypes=[("AVI Video", "*.avi")])
    if not output_path:
        label_status.set("Processing canceled.")
        return

    label_status.set("Processing...")
    Thread(target=process_video, args=(video_path, output_path, label_status)).start()


video_path = None
root = Tk()
root.title("Car Plate Detection")
root.geometry("400x250")

label_status = StringVar()
label_status.set("Please select a video to process.")

Label(root, text="Car Plate Detection", font=("Arial", 16)).pack(pady=10)
Button(root, text="Select Video", command=select_video, width=20).pack(pady=5)
Button(root, text="Start Processing", command=start_processing, width=20).pack(pady=5)
Label(root, textvariable=label_status, wraplength=300, font=("Arial", 12)).pack(pady=10)

root.mainloop()
