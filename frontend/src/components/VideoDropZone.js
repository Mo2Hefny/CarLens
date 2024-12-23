import React, { useState, useEffect, useRef } from "react";
import { Box, Typography, Button } from "@mui/material";

const VideoDropZone = ({ videoSrc, onDrop, onFileSelect, plates, onSocketRecieve }) => {
  const [dragging, setDragging] = useState(false);
  const canvasRef = useRef(null);
  const videoRef = useRef(null);
  const wsRef = useRef(null);

  useEffect(() => {
    const ws = new WebSocket("ws://127.0.0.1:8000/ws");
    wsRef.current = ws;

    ws.onopen = () => {
      console.log("WebSocket connection established");
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      console.log("License Plate Data:", JSON.parse(event.data));
      const video = videoRef.current;
      if (video) {
        onSocketRecieve(data.plates, video.currentTime);
      }
    };

    ws.onerror = (error) => {
      console.error("WebSocket error:", error);
    };

    ws.onclose = () => {
      console.log("WebSocket connection closed");
    };

    return () => {
      ws.close();
    };
  }, []);

  // Capture video frame and send it via WebSocket
  const captureFrameAndSend = () => {
    const video = videoRef.current;
    const canvas = canvasRef.current;

    if (video && canvas) {
      const context = canvas.getContext("2d");
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;

      // Draw video frame onto the canvas
      context.drawImage(video, 0, 0, canvas.width, canvas.height);

      // Send the canvas frame to the backend
      const imageData = canvas.toDataURL("image/jpeg");
      if (wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send(imageData);
      }

      // Draw rectangles for plates
      drawRectangles(context);
    }
  };

  const drawRectangles = (context) => {
    return;
    plates.forEach((plate) => {
      const { x, y, width, height } = plate;

      // Draw rectangle
      context.strokeStyle = "red";
      context.lineWidth = 2;
      context.strokeRect(x, y, width, height);

      // Label the plate
      context.fillStyle = "red";
      context.font = "16px Arial";
      context.fillText(plate.plate, x, y - 5); // Adjust label position above the rectangle
    });
  };

  // Start capturing frames when the video is playing
  useEffect(() => {
    if (videoSrc) {
      const interval = setInterval(() => {
        captureFrameAndSend();
      }, 5000); // Capture every 5 seconds

      return () => clearInterval(interval);
    }
  }, [videoSrc]);

  return (
    <>
      {videoSrc ? (
        <>
          <video
            ref={videoRef}
            style={{
              maxWidth: "100%", // Ensures it scales with the container width
              maxHeight: "100%", // Ensures it scales with the container height
              width: "100%",     // Make it responsive
              height: "auto",    // Maintain aspect ratio
            }}
            controls
            autoPlay
            controlsList="nodownload nofullscreen noremoteplayback"
            src={videoSrc}
          />
          <canvas ref={canvasRef} style={{ display: "None", position: "absolute", top: 0, left: 0 }}></canvas>
        </>
      ) : (
        <Box
          sx={{
            width: "98%",
            minHeight: "300px",
            height: "95%",
            backgroundColor: "#f5f5f5",
            display: "flex",
            justifyContent: "center",
            alignItems: "center",
            border: "2px dashed #ccc",
            borderRadius: "8px",
            position: "relative",
          }}
          onDrop={() => {
            setDragging(false);
            onDrop();
          }}
          onDragEnter={() => setDragging(true)}
          onDragLeave={() => setDragging(false)}
        >
          <Box textAlign="center">
            {dragging ? (
              <Typography
                variant="h6"
                mb={2}
                sx={{ color: "#565e6c", fontWeight: "bold" }}
              >
                Drop the video here
              </Typography>
            ) : (
              <>
                <Typography
                  variant="h6"
                  mb={2}
                  sx={{ color: "#565e6c", fontWeight: "bold" }}
                >
                  Drag & Drop a video here or
                </Typography>
                <Button
                  variant="contained"
                  component="label"
                  sx={{
                    backgroundColor: "#636AE8",
                    "&:hover": {
                      backgroundColor: "#303f9f",
                    },
                  }}
                >
                  Upload Video
                  <input
                    type="file"
                    accept="video/*"
                    hidden
                    onChange={onFileSelect}
                  />
                </Button>
              </>
            )}
          </Box>
        </Box>
      )}
    </>
  );
};

export default VideoDropZone;
