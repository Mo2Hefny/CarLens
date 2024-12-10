import cv2
import os
import argparse

def sample_video(image_queue, video_source=0, rate=0.1):
    cap = cv2.VideoCapture(video_source)
    frame_rate = cap.get(cv2.CAP_PROP_FPS)
    frame_count = 0

    if not cap.isOpened():
        print("Error opening video file.")
        return
    
    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Failed to capture frame.")
            break
        
        if frame_count % int(frame_rate * rate) == 0:
            image_queue.put(frame)
            print(f"Saved: {frame_count}")
        
        frame_count += 1
    
    cap.release()
    print("Sampling complete.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sample frames from a video.")
    
    parser.add_argument("video", type=str, help="Path to the video file.")
    parser.add_argument("--value", type=float, default=1.0,
                        help="Value for the sampling mode: seconds")
    
    args = parser.parse_args()
    
    sample_video(args.video, args.value)