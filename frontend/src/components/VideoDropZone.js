import React, { useState, useEffect, useRef, use } from "react";
import { Box, Typography, Button, Slider, IconButton } from "@mui/material";
import PauseIcon from '@mui/icons-material/Pause';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';

const VideoDropZone = ({ plates, onDetectedPlates }) => {
  const videoFrames = useRef([]);
  const [videoData, setVideoData] = useState({});
  const [currentFrame, setCurrentFrame] = useState(null);
  const frameIndex = useRef(0);
  const receivedFrameIndex = useRef(0);
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const isSliding = useRef(false);
  const wsRef = useRef(null);
  const reconnectAttempts = useRef(0);
  const maxReconnectAttempts = 5;
  const reconnectInterval = 5000;
  const [connected, setConnected] = useState(false);
  const isPlaying = useRef(true);
  const [playEnabled, setPlayEnabled] = useState(true);

  const connectWebSocket = () => {
    const ws = new WebSocket("ws://127.0.0.1:8000/ws");
    wsRef.current = ws;

    ws.onopen = () => {
      console.log("WebSocket connection established");
      setConnected(true);
      reconnectAttempts.current = 0; // Reset reconnection attempts on success
    };

    ws.onmessage = (event) => {
      console.log("WebSocket message received of type:", typeof event.data);

      if (event.data instanceof Blob) {
        const arrayBuffer = event.data;
        const blob = new Blob([arrayBuffer], { type: "image/jpeg" });
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
      setConnected(false);
    };

    ws.onclose = (event) => {
      console.log("WebSocket connection closed:", event.reason);
      setConnected(false);
      attemptReconnect();
    };
  };

  const attemptReconnect = () => {
    if (reconnectAttempts.current < maxReconnectAttempts) {
      reconnectAttempts.current += 1;
      console.log(
        `Attempting to reconnect (${reconnectAttempts.current}/${maxReconnectAttempts})...`
      );
      setTimeout(() => {
        connectWebSocket();
      }, reconnectInterval);
    } else {
      console.error("Max reconnection attempts reached. Could not reconnect.");
    }
  };

  useEffect(() => {
    connectWebSocket();

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
        !isSliding.current &&
        isPlaying.current &&
        frames[frameIndex.current] !== null &&
        frameIndex.current < videoData.frame_count
      ) {
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

  const handleSliderChange = (event, newValue) => {
    if (newValue >= receivedFrameIndex.current) return;
    frameIndex.current = newValue;
    setCurrentFrame(videoFrames.current[newValue]);
  };

  const handlePlayPause = () => {
    isPlaying.current = !isPlaying.current;
    const currentPlayEnabled = playEnabled;
    setPlayEnabled(!currentPlayEnabled);
  };

  const handleSliderStart = () => {
    console.log("Slider start");
    isSliding.current = true;
  };

  const handleSliderEnd = () => {
    console.log("Slider end");
    isSliding.current = false;
  };

  const calculateTime = () => {
    const currentSeconds = Math.floor(frameIndex.current / videoData.fps);
    const currentMinutes = Math.floor(currentSeconds / 60);
    
    const totalSeconds = Math.floor(videoData.frame_count / videoData.fps);
    const totalMinutes = Math.floor(totalSeconds / 60);

    const formatTime = (time) => time.toString().padStart(2, '0');
    return `${formatTime(currentMinutes)}:${formatTime(currentSeconds)} / ${formatTime(totalMinutes)}:${formatTime(totalSeconds)}`;
  };

  return (
    <>
      {currentFrame ? (
        <>
          <Box
            sx={{
              position: "relative",
              width: "100%",
              maxWidth: "100%",
              margin: "auto",
              aspectRatio: "16/9",
              overflow: "hidden",
            }}
          >
            {/* Background Image */}
            <img
              src={currentFrame}
              alt="video"
              style={{
                position: "absolute",
                top: 0,
                left: 0,
                width: "100%",
                height: "100%",
                objectFit: "cover",
                zIndex: 1,
              }}
            />

            {/* Slider Overlay */}
            <Box
              sx={{
                position: "absolute",
                bottom: 16,
                left: "50%",
                transform: "translateX(-50%)",
                zIndex: 2,
                width: "80%",
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
              }}
            >
              {/* Play/Pause Button */}
              <IconButton onClick={handlePlayPause} sx={{ color: "white" }}>
                {playEnabled ? <PauseIcon /> : <PlayArrowIcon />}
              </IconButton>

              {/* Load Bar Slider */}
              <Box sx={{ flex: 1, position: "relative", mx: 2 }}>
                <Slider
                  value={receivedFrameIndex.current}
                  min={0}
                  max={videoData.frame_count}
                  aria-labelledby="continuous-slider"
                  disabled
                  sx={{
                    color: "grey",
                    height: 3,
                    "& .MuiSlider-thumb": {
                      display: "none",
                    },
                  }}
                />

                {/* Interactive Slider */}
                <Slider
                  value={frameIndex.current}
                  min={0}
                  max={videoData.frame_count}
                  onChange={handleSliderChange}
                  onMouseDown={handleSliderStart}
                  onTouchStart={handleSliderStart}
                  onDragEnter={handleSliderStart}
                  onMouseUp={handleSliderEnd}
                  onTouchEnd={handleSliderEnd}
                  onDragLeave={handleSliderEnd}
                  aria-labelledby="continuous-slider"
                  sx={{
                    position: "absolute",
                    left: "50%",
                    top: "50%",
                    transform: "translate(-50%, -55%)",
                    "& .MuiSlider-track": {
                      color: "inherit",
                    },
                    "& .MuiSlider-rail": {
                      color: "transparent",
                    },
                  }}
                />
              </Box>

              {/* Time Display */}
              <Typography variant="body2" sx={{ color: "white" }}>
                {calculateTime()}
              </Typography>
            </Box>
          </Box>
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
            {dragging || uploading || !connected ? (
              <Typography
                variant="h6"
                mb={2}
                sx={{ color: "#565e6c", fontWeight: "bold" }}
              >
                {!connected
                  ? "Connecting to server..."
                  : uploading
                  ? "Uploading..."
                  : "Drop the video here"}
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
