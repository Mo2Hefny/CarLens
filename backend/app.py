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

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


video_chunks = {}


def process_video_data(data):
    try:
        np_arr = np.frombuffer(data, np.uint8)
        frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)  # Decode image to frame

        if frame is None:
            raise ValueError("Failed to decode the image.")

        processed_frame = process_frame(frame, 0)

        if processed_frame is not None:
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
            data = await websocket.receive_json()

            message_type = data.get("type")

            if message_type == "UPLOAD_CHUNK":

                if 'chunk' not in data or 'filename' not in data or 'offset' not in data:
                    logger.error(
                        "Invalid data received: Missing 'chunk', 'filename' or 'offset'.")
                    continue

                chunk = data['chunk']
                filename = data['filename']
                offset = data['offset']

                if filename not in video_chunks:
                    video_chunks[filename] = {
                        'chunks': [],
                        'size': 0
                    }

                video_chunks[filename]['chunks'].append((offset, chunk))
                video_chunks[filename]['size'] += len(chunk)

                logger.info(
                    f"Received chunk for {filename}, offset {offset}, total size {video_chunks[filename]['size']} bytes")

                await websocket.send_json({'type': 'RECEIVED_CHUNK', 'offset': offset})

            elif message_type == 'UPLOAD_COMPLETED':
                logger.info(
                    f"Upload complete for {filename}, total size {video_chunks[filename]['size']} bytes")

                video_chunks[filename]['chunks'].sort(
                    key=lambda x: x[0])
                video_file_path = os.path.join(UPLOAD_FOLDER, filename)

                create_mp4_from_bytes(
                    video_file_path, video_chunks[filename]['chunks'])

                del video_chunks[filename]

                await websocket.send_json({'type': 'UPLOAD_COMPLETED', 'filename': filename})
                await process_video_data_from_file(websocket, video_file_path)

    except WebSocketDisconnect:
        logger.info("WebSocket connection closed")
    except Exception as e:
        logger.error(f"Error in WebSocket: {e}")


async def process_frame_in_thread(websocket, thread_frames, frame_count, predictions_list):
    """Process a frame in a separate thread."""
    frame = thread_frames[0]
    processed_frame, predictions = process_frame(frame, frame_count)
    predictions_list.extend(predictions)
    await send_frame(websocket, processed_frame, frame_count)
    for index, frame in enumerate(thread_frames[1:], start=1):
        frame = frame[50:, :]
        # for (x, y, w, h) in location:
        #     cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        await send_frame(websocket, frame, frame_count + index)


def vote_for_correct_string(strings):
    valid_first = set("123456789")
    valid_middle = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnoprstuvwxyz")
    valid_last = set("123456789")

    voted_string = []

    for i in range(6):

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

        char_count = Counter(valid_chars)
        print(valid_chars)

        if char_count:
            most_common_char = char_count.most_common(1)[0][0]
        else:
            most_common_char = ''
        voted_string.append(most_common_char)

    return ''.join(voted_string)


async def process_video_data_from_file(websocket, video_file_path):
    """Process the video file and stream it as encoded video to the frontend."""
    try:
        cap = cv2.VideoCapture(video_file_path)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        fps = cap.get(cv2.CAP_PROP_FPS) or 30
        MAX_FRAMES_LEN = cap.get(cv2.CAP_PROP_FRAME_COUNT)
        await websocket.send_json({
            "type": "VIDEO_METADATA",
            "width": width,
            "height": height,
            "fps": fps,
            "frame_count": MAX_FRAMES_LEN
        })

        import time
        start_time = time.time()
        frames_per_thread = 1
        frame_count = 0
        threads = []
        frames = []

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
        result = vote_for_correct_string(predictions_list)
        end_time = time.time()
        logger.info(
            f"Video processing completed in {end_time - start_time:.2f} seconds")
        if predictions_list:
            result = vote_for_correct_string(predictions_list)
            await websocket.send_json({
            "type": "PREDICTIONS",
            "predictions": [result]
            })

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
