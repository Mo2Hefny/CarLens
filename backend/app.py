from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import json
import concurrent.futures
import asyncio
import logging
import os
import numpy as np
import cv2
from io import BytesIO
from PIL import Image
from wrapper import process_frame
from collections import Counter

logging.basicConfig(level=logging.INFO)  # Set the desired log level
logger = logging.getLogger(__name__)

app = FastAPI()

# Folder to save uploaded video file
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Temporary storage for incoming video chunks
video_chunks = {}


def process_video_data(data):
    try:
        # Convert binary data to NumPy array
        np_arr = np.frombuffer(data, np.uint8)
        frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)  # Decode image to frame

        if frame is None:
            raise ValueError("Failed to decode the image.")

        # Process the frame
        processed_frame = process_frame(frame, 0)

        if processed_frame is not None:
            # Display the processed frame
            cv2.imshow('Processed Frame', processed_frame)
    except Exception as e:
        logger.error(f"Error processing video data: {e}")


def create_mp4_from_bytes(filename, data):
    with open(filename, "wb") as mp4_file:
        for offset, chunk in data:
            chunk_bytes = bytes(chunk)
            logger.info(
                f"Processing chunk at offset {offset}, size {len(chunk_bytes)} bytes")
            mp4_file.seek(offset)
            mp4_file.write(chunk_bytes)
        logger.info(f"MP4 file {filename} created successfully")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info("WebSocket connection established")
    try:
        while True:
            # Receive chunked data from the frontend
            # Receive JSON with chunk, filename, and offset
            data = await websocket.receive_json()

            message_type = data.get("type")

            if message_type == "UPLOAD_CHUNK":
                # Ensure that 'chunk' exists in the received data
                if 'chunk' not in data or 'filename' not in data or 'offset' not in data:
                    logger.error(
                        "Invalid data received: Missing 'chunk', 'filename' or 'offset'.")
                    continue  # Skip processing this message

                chunk = data['chunk']
                filename = data['filename']
                offset = data['offset']

                # Initialize the video data structure for the file if not already
                if filename not in video_chunks:
                    video_chunks[filename] = {
                        'chunks': [],
                        'size': 0
                    }

                # Append the chunk data
                video_chunks[filename]['chunks'].append((offset, chunk))
                video_chunks[filename]['size'] += len(chunk)

                logger.info(
                    f"Received chunk for {filename}, offset {offset}, total size {video_chunks[filename]['size']} bytes")

                # Acknowledge the chunk receipt
                await websocket.send_json({'type': 'RECEIVED_CHUNK', 'offset': offset})

            # Check if the upload is complete (we can send a signal from the frontend when all chunks are uploaded)
            elif message_type == 'UPLOAD_COMPLETED':
                logger.info(
                    f"Upload complete for {filename}, total size {video_chunks[filename]['size']} bytes")
                # Sort chunks by offset and write the file
                video_chunks[filename]['chunks'].sort(
                    key=lambda x: x[0])  # Sort by offset
                video_file_path = os.path.join(UPLOAD_FOLDER, filename)

                # Open the file in write-binary mode
                create_mp4_from_bytes(
                    video_file_path, video_chunks[filename]['chunks'])

                # Clear stored data
                del video_chunks[filename]

                # Notify frontend of completion using "UPLOAD_COMPLETED" event
                await websocket.send_json({'type': 'UPLOAD_COMPLETED', 'filename': filename})
                # Optionally, process the video after upload
                # You can use OpenCV or other libraries here to process the video file
                await process_video_data_from_file(websocket, video_file_path)

    except WebSocketDisconnect:
        logger.info("WebSocket connection closed")
    except Exception as e:
        logger.error(f"Error in WebSocket: {e}")


async def process_frame_in_thread(websocket, thread_frames, frame_count, predictions_list):
    """Process a frame in a separate thread."""
    # Your frame processing logic goes here
    # Process the frame (if needed)
    frame = thread_frames[0]
    processed_frame, predictions = process_frame(frame, frame_count)
    predictions_list.extend(predictions)
    # Send all frames to the frontend
    await send_frame(websocket, processed_frame, frame_count)
    for index, frame in enumerate(thread_frames[1:], start=1):
        frame = frame[50:, :]
        # for (x, y, w, h) in location:
        #     cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        await send_frame(websocket, frame, frame_count + index)


def vote_for_correct_string(strings):
    # Constraints for each position
    valid_first = set("123456789")
    valid_middle = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnoprstuvwxyz")
    valid_last = set("123456789")

    # Initialize a list to store the most common character for each position
    voted_string = []

    # Iterate over each character position (6 positions in total)
    for i in range(6):
        # Create a list of valid characters for this position
        valid_chars = []

        for string in strings:
            if i == 0:  # First position: 1-9
                if string[i] in valid_first:
                    valid_chars.append(string[i])
            elif 1 <= i <= 3:  # Next 3 positions: A-Z
                if string[i] in valid_middle:
                    valid_chars.append(string[i])
            elif 4 <= i <= 5:  # Last 2 positions: 1-9
                if string[i] in valid_last:
                    valid_chars.append(string[i])

        # Count the frequency of valid characters in this position
        char_count = Counter(valid_chars)
        print(valid_chars)
        # If no valid character is found, pick an empty string or a fallback value
        if char_count:
            most_common_char = char_count.most_common(1)[0][0]
        else:
            most_common_char = ''  # Default to empty string if no valid character

        # Append the result to the voted string
        voted_string.append(most_common_char)

    # Join the list into a string and return
    return ''.join(voted_string)


async def process_video_data_from_file(websocket, video_file_path):
    """Process the video file and stream it as encoded video to the frontend."""
    try:
        # Open the video file using OpenCV
        cap = cv2.VideoCapture(video_file_path)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        # Default to 30 FPS if not available
        fps = cap.get(cv2.CAP_PROP_FPS) or 30
        MAX_FRAMES_LEN = cap.get(cv2.CAP_PROP_FRAME_COUNT)
        await websocket.send_json({
            "type": "VIDEO_METADATA",
            "width": width,
            "height": height,
            "fps": fps,
            "frame_count": MAX_FRAMES_LEN
        })

        # Create a ThreadPoolExecutor
        import time
        start_time = time.time()
        frames_per_thread = 1
        frame_count = 0
        threads = []
        frames = []

        # Asynchronously process the video frames
        frames_collector_threads = asyncio.create_task(
            get_video_frames(cap, frames))

        MAX_THREADS = 10
        predictions_list = []
        while len(frames) > 0 or frame_count < MAX_FRAMES_LEN:
            try:
                if len(threads) < MAX_THREADS and len(frames) > 0:
                    thread_frames = frames[:frames_per_thread]
                    frames = frames[frames_per_thread:]
                    thread = asyncio.create_task(process_frame_in_thread(
                        websocket, thread_frames, frame_count, predictions_list=predictions_list))
                    threads.append(thread)
                    frame_count += len(thread_frames)
                else:
                    await asyncio.sleep(0.01)
                    threads = [
                        thread for thread in threads if not thread.done()]
            except WebSocketDisconnect:
                logger.info("WebSocket connection closed")
                break
            except Exception as e:
                logger.error(f"Error processing video frames: {e}")

        if not frames_collector_threads.done():
            frames_collector_threads.cancel()
        print("Combined Predictions", predictions_list)
        end_time = time.time()
        logger.info(
            f"Video processing completed in {end_time - start_time:.2f} seconds")

    except Exception as e:
        logger.error(f"Error processing video file {video_file_path}: {e}")
    finally:
        cap.release()


async def get_video_frames(cap, frames):
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frames.append(frame)


async def send_frame(websocket, frame, frame_count):
    """Encode and send the frame to the frontend."""
    try:
        if frame is not None:
            _, buffer = cv2.imencode('.jpg', frame)
            img_str = buffer.tobytes()
            await websocket.send_bytes(img_str)
    except WebSocketDisconnect:
        logger.info("WebSocket connection closed")
        raise e
    except Exception as e:
        print(f"Error sending frame: {e}")
