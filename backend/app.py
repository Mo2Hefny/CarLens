from fastapi import FastAPI, WebSocket
import base64
import cv2
import numpy as np
from io import BytesIO
from PIL import Image

app = FastAPI()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    print("WebSocket connection established")
    try:
        while True:
            # Receive image data from the client
            data = await websocket.receive_text()  # Receive base64 image as text
            header, encoded = data.split(",", 1)  # Split the data to extract base64
            decoded = base64.b64decode(encoded)   # Decode the base64 string

            # Convert to OpenCV image
            image = Image.open(BytesIO(decoded))  # Convert bytes to PIL Image
            cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)  # PIL to OpenCV

            # Process the image (Replace this with your license plate detection logic)
            # For now, let's simulate with dummy data
            dummy_coordinates = [
                {"plate": "ABC123", "x": 50, "y": 100, "width": 200, "height": 50}
            ]

            # Send the processed data back to the client
            await websocket.send_json({"plates": dummy_coordinates})

    except Exception as e:
        print(f"WebSocket error: {e}")  # Handle exceptions gracefully
    finally:
        print("WebSocket connection closed")
