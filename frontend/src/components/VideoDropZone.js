import React, { useState, useEffect, useRef } from "react";
import { Box, Typography, Button } from "@mui/material";

const VideoDropZone = ({ plates, onDetectedPlates }) => {
  const [videoSrc, setVideoSrc] = useState("");
  const [dragging, setDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const videoRef = useRef(null);
  const wsRef = useRef(null);
  const mediaSourceRef = useRef(new MediaSource());
  const sourceBufferRef = useRef(null);
  const bufferQueue = useRef([]);

  useEffect(() => {
    const ws = new WebSocket("ws://127.0.0.1:8000/ws");
    wsRef.current = ws;

    ws.onopen = () => {
      console.log("WebSocket connection established");
    };

    ws.onmessage = (event) => {
      console.log("WebSocket message received of type:", typeof event.data);
      if (event.data instanceof Blob) {
        console.log("Received video frame as Blob");
        event.data.arrayBuffer().then((arrayBuffer) => {
          const mediaSource = mediaSourceRef.current;
          const sourceBuffer = sourceBufferRef.current;
      
          console.log("MediaSource state:", mediaSource.readyState);
          console.log("SourceBuffer status - updating:", sourceBuffer?.updating);
      
          // Check if the MediaSource is ready and the SourceBuffer can accept data
          if (mediaSource.readyState === "open" && sourceBuffer) {
            try {
              // Log for debugging
              console.log(
                "Appending buffer of size:", arrayBuffer.byteLength,
                "First 50 bytes:", new Uint8Array(arrayBuffer).slice(0, 50)
              );
              bufferQueue.current.push(arrayBuffer);
              appendBuffer();
              // Append buffer
            } catch (error) {
              console.error("Error appending buffer:", error);
      
              // Handle MediaSource errors (e.g., invalid MIME type or buffer overflow)
              if (error.name === "QuotaExceededError") {
                console.warn("QuotaExceededError: Clearing SourceBuffer");
                try {
                  sourceBuffer.abort(); // Reset buffer operations
                  sourceBuffer.remove(0, sourceBuffer.buffered.end(0)); // Remove old data
                } catch (removeError) {
                  console.error("Error removing SourceBuffer data:", removeError);
                }
              }
            }
          } else {
            console.warn(
              "Cannot append buffer. MediaSource state:",
              mediaSource.readyState,
              "SourceBuffer status - updating:", sourceBuffer?.updating
            );
          }
        }).catch((error) => {
          console.error("Error reading Blob as ArrayBuffer:", error);
        });
      } else {
        const data = JSON.parse(event.data);
        console.log("WebSocket message received:", data);

        if (data.type === "plate_detection") {
          onDetectedPlates(data);
        } else if (data.type === "UPLOAD_COMPLETED") {
          console.log("Upload complete to filename:", data.filename);
          setUploading(false);
          setVideoSrc(`/media/${data.filename}`);
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
    if (videoSrc) {
      const mediaSource = mediaSourceRef.current;
      const videoElement = videoRef.current;
      console.log("Setting up MediaSource object");
  
      // Log the MIME type to make sure it's correct
      const mimeType = 'video/mp4; codecs="avc1.42E01E"';  // Replace with your actual MIME type
      console.log("Using MIME type:", mimeType);
  
      try {
        // Set the video source to the MediaSource object
        videoElement.src = URL.createObjectURL(mediaSource);
  
        mediaSource.addEventListener("sourceopen", () => {
          // Adding a SourceBuffer for video (vp8 or h264 depending on your backend format)
          sourceBufferRef.current = mediaSource.addSourceBuffer(mimeType);
          console.log("SourceBuffer created:", sourceBufferRef.current);
          sourceBufferRef.current.addEventListener("updateend", appendBuffer);
        });
  
        mediaSource.addEventListener("sourceended", () => {
          console.log("MediaSource has ended. Recreating...");
          // recreateMediaSource(); // Handle the closed MediaSource by recreating it
        });
  
      } catch (error) {
        console.error("Error setting up MediaSource:", error);
      }
    }
  }, [videoSrc]);

  const appendBuffer = () => {
    const sourceBuffer = sourceBufferRef.current;

    if (bufferQueue.current.length > 0 && sourceBuffer && !sourceBuffer.updating) {
      const buffer = bufferQueue.current.shift();
      try {
        console.log("Appending buffer of size:", buffer.byteLength);
        sourceBuffer.appendBuffer(buffer);
      } catch (error) {
        console.error("Error appending buffer:", error);
      }
    }

    if (bufferQueue.current.length === 0 && mediaSourceRef.current.readyState === "open") {
      console.log("End of buffer queue. Ending stream.");
      mediaSourceRef.current.endOfStream();
    }
  };

  const recreateMediaSource = () => {
    const videoElement = videoRef.current;
    const newMediaSource = new MediaSource();
    mediaSourceRef.current = newMediaSource;
  
    videoElement.src = URL.createObjectURL(newMediaSource);
  
    newMediaSource.addEventListener("sourceopen", () => {
      try {
        const newSourceBuffer = newMediaSource.addSourceBuffer('video/mp4; codecs="avc1.42E01E"');
        sourceBufferRef.current = newSourceBuffer;
        console.log("New SourceBuffer created:", newSourceBuffer);
      } catch (error) {
        console.error("Error creating SourceBuffer:", error);
      }
    });
  };

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
      {videoSrc ? (
        <>
          <video
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
          />
          {/* <img
            src={videoSrc}
            alt="video"
            style={{
              maxWidth: "100%", // Ensures it scales with the container width
              maxHeight: "100%", // Ensures it scales with the container height
              width: "100%", // Make it responsive
              height: "auto", // Maintain aspect ratio
            }}
          /> */}
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
