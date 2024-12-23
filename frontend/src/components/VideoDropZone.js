import React, { useState, useEffect, useRef } from "react";
import { Box, Typography, Button } from "@mui/material";

const VideoDropZone = ({ plates, onDetectedPlates }) => {
  const videoFrames = useRef([]);
  const [videoData, setVideoData] = useState({});
  const [currentFrame, setCurrentFrame] = useState(null);
  const frameIndex = useRef(0);
  const receivedFrameIndex = useRef(0);
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const wsRef = useRef(null);

  useEffect(() => {
    const ws = new WebSocket("ws://127.0.0.1:8000/ws");
    wsRef.current = ws;

    ws.onopen = () => {
      console.log("WebSocket connection established");
    };

    ws.onmessage = (event) => {
      console.log("WebSocket message received of type:", typeof event.data);

      if (event.data instanceof Blob) {
        const arrayBuffer = event.data;
        const blob = new Blob([arrayBuffer], { type: 'image/jpeg' });
        const url = URL.createObjectURL(blob);
        videoFrames.current[receivedFrameIndex.current] = url;
        receivedFrameIndex.current += 1;
      } else {
        const data = JSON.parse(event.data);
        console.log("WebSocket message received:", data);

        if (data.type === "plate_detection") {
          onDetectedPlates(data);
        } else if (data.type === "UPLOAD_COMPLETED") {
          console.log("Upload complete to filename:", data.filename);
        } else if (data.type === "VIDEO_METADATA") {
          setVideoData(data);
        } else if (data.type === "VIDEO_FRAME") {
          const frameIndex = data.frame_count;
          const imageHex = data.image;
          const imageBuffer = new Uint8Array(
            imageHex.match(/.{1,2}/g).map((byte) => parseInt(byte, 16))
          );
          const img = new Blob([imageBuffer], { type: "image/jpeg" });
          const url = URL.createObjectURL(img);
          videoFrames.current[frameIndex] = url;
          if (uploading) {
            setUploading(false);
          }
        }
      }
    };

    ws.onerror = (error) => {
      console.error("WebSocket error:", error);
    };

    ws.onclose = () => {
      console.log("WebSocket connection closed");
    };

    return () => {
      if (wsRef.current) {
        wsRef.current.close(1000, "Component unmounted");
      }
    };
  }, []);

  useEffect(() => {
    console.log("videoData changed:", videoData);
    if (videoData && videoData.frame_count) {
      videoFrames.current = Array(videoData.frame_count).fill(null);
      frameIndex.current = 0;
    }

    const intervalId = setInterval(() => {
      const frames = videoFrames.current;
      if (
        frames[frameIndex.current] !== null &&
        frameIndex.current < videoData.frame_count
      ) {
        console.log("frameIndex.current", frameIndex.current);
        setCurrentFrame(frames[frameIndex.current]);
        frameIndex.current += 1;
      }
    }, (1000 / videoData.fps) * 2);

    return () => clearInterval(intervalId);
  }, [videoData]);

  const onDrop = (event) => {
    event.preventDefault();
    setDragging(false);
    const file = event.dataTransfer.files[0];
    if (file & file.type.startsWith("video/")) {
      handleVideoUpload(file);
    }
  };

  const onFileSelect = (event) => {
    const file = event.target.files[0];
    if (file && file.type.startsWith("video/")) {
      handleVideoUpload(file);
    }
  };

  const handleVideoUpload = (file) => {
    setUploading(true);

    const chunkSize = 1024 * 1024; // 1MB chunks
    let offset = 0;

    const sendChunk = () => {
      if (offset < file.size) {
        const chunk = file.slice(offset, offset + chunkSize);
        const reader = new FileReader();

        reader.onload = function (e) {
          const chunkData = e.target.result;
          if (wsRef.current.readyState === WebSocket.OPEN) {
            wsRef.current.send(
              JSON.stringify({
                type: "UPLOAD_CHUNK",
                chunk: Array.from(new Uint8Array(chunkData)),
                filename: file.name,
                offset,
              })
            );
          }

          offset += chunkSize;
          sendChunk();
        };

        reader.readAsArrayBuffer(chunk);
      } else {
        wsRef.current.send(
          JSON.stringify({
            type: "UPLOAD_COMPLETED",
            filename: file.name,
          })
        );
      }
    };

    sendChunk();
  };

  return (
    <>
      {currentFrame ? (
        <>
          {/* <video
            ref={videoRef}
            style={{
              maxWidth: "100%", // Ensures it scales with the container width
              maxHeight: "100%", // Ensures it scales with the container height
              width: "100%", // Make it responsive
              height: "auto", // Maintain aspect ratio
            }}
            controls
            autoPlay
            // controlsList="nodownload nofullscreen noremoteplayback"
            // src={videoSrc}
          /> */}
          <img
            src={currentFrame}
            alt="video"
            style={{
              maxWidth: "100%", // Ensures it scales with the container width
              maxHeight: "100%", // Ensures it scales with the container height
              width: "100%", // Make it responsive
              height: "auto", // Maintain aspect ratio
            }}
          />
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
          onDrop={onDrop}
          onDragEnter={() => setDragging(true)}
          onDragLeave={() => setDragging(false)}
        >
          <Box textAlign="center">
            {dragging || uploading ? (
              <Typography
                variant="h6"
                mb={2}
                sx={{ color: "#565e6c", fontWeight: "bold" }}
              >
                {uploading ? "Uploading..." : "Drop the video here"}
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
