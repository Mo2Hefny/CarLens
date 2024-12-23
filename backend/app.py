from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import asyncio
import ffmpeg
print(ffmpeg.__file__)
import logging
import os
import numpy as np
from pymp4.parser import Box
from pymp4.exceptions import BoxNotFound
import cv2
from io import BytesIO
from PIL import Image
from wrapper import process_frame

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
        np_arr = np.frombuffer(data, np.uint8)  # Convert binary data to NumPy array
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
            try:
                chunk_bytes = bytes(chunk)
                logger.info(f"Processing chunk at offset {offset}, size {len(chunk_bytes)} bytes")
                mp4_file.seek(offset)
                mp4_file.write(chunk_bytes)
            except BoxNotFound:
                logger.error(f"Invalid box at offset {offset}")
        logger.info(f"MP4 file {filename} created successfully")
                
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info("WebSocket connection established")
    try:
        while True:
            # Receive chunked data from the frontend
            data = await websocket.receive_json()  # Receive JSON with chunk, filename, and offset

            message_type = data.get("type")
            
            if message_type == "UPLOAD_CHUNK":
                # Ensure that 'chunk' exists in the received data
                if 'chunk' not in data or 'filename' not in data or 'offset' not in data:
                    logger.error("Invalid data received: Missing 'chunk', 'filename' or 'offset'.")
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
                
                logger.info(f"Received chunk for {filename}, offset {offset}, total size {video_chunks[filename]['size']} bytes")
                
                # Acknowledge the chunk receipt
                await websocket.send_json({'type': 'RECEIVED_CHUNK', 'offset': offset})
            
            # Check if the upload is complete (we can send a signal from the frontend when all chunks are uploaded)
            elif message_type == 'UPLOAD_COMPLETED':
                logger.info(f"Upload complete for {filename}, total size {video_chunks[filename]['size']} bytes")
                # Sort chunks by offset and write the file
                video_chunks[filename]['chunks'].sort(key=lambda x: x[0])  # Sort by offset
                video_file_path = os.path.join(UPLOAD_FOLDER, filename)

                # Open the file in write-binary mode
                create_mp4_from_bytes(video_file_path, video_chunks[filename]['chunks'])
                
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

async def process_video_data_from_file(websocket: WebSocket, video_file_path: str):
    """Process the video file and stream it as encoded video to the frontend."""
    try:
        # Open the video file using OpenCV
        cap = cv2.VideoCapture(video_file_path)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS) or 30  # Default to 30 FPS if not available
        logger.info(f"Processing video file {video_file_path}, {width}x{height}, {fps} FPS")
        # Set up FFmpeg for video encoding
        process = (
            ffmpeg
            .input('pipe:0', format='rawvideo', pix_fmt='bgr24', s=f'{width}x{height}', framerate=fps)
            .output('pipe:1', format='mp4', codec='libx264', pix_fmt='yuv420p', movflags='frag_keyframe+empty_moov', preset='ultrafast')
            .global_args('-loglevel', 'error', '-fflags', 'nobuffer')
            .run_async(pipe_stdin=True, pipe_stdout=True, pipe_stderr=True)
        )

        logger.info("FFmpeg process started")

        async def read_ffmpeg_output():
            logger.info("Reading FFmpeg output")
            try:
                while True:
                    chunk = await asyncio.get_event_loop().run_in_executor(None, process.stdout.read, 1024 * 1024)
                    if not chunk:
                        break
                    logger.info(f"Sending chunk of size {len(chunk)} bytes")
                    await websocket.send_bytes(chunk)
            except Exception as e:
                logger.error(f"Error reading FFmpeg output: {e}")
        
        asyncio.create_task(read_ffmpeg_output())

        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break

            # Process the frame (if needed)
            # processed_frame = process_frame(frame, 0)
            # Write the frame to FFmpeg for encoding
            process.stdin.write(frame.tobytes())
            # Simulate real-time streaming
            await asyncio.sleep(1 / fps)

        cap.release()
        process.stdin.close()
        await process.wait()
    except Exception as e:
        print(f"Error processing video file {video_file_path}: {e}")

