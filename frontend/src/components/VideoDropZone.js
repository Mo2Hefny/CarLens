import React, { useState } from "react";
import { Box, Typography, Button } from "@mui/material";

const VideoDropZone = ({ videoSrc, onDrop, onFileSelect }) => {
  const [dragging, setDragging] = useState(false);

  const handleDragOver = (event) => {
    event.preventDefault();
    if (!dragging) {
      setDragging(true);
    }
  };


  return (
    <>
      {videoSrc ? (
        <video
            style={{ maxWidth: "100%", height: "100%" }}
            controls
            src={videoSrc}
          />
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
              <Typography variant="h6" mb={2} sx={{ color: '#565e6c', fontWeight: 'bold' }}>
                Drop the video here
              </Typography>
            ) : (
              <>
              <Typography variant="h6" mb={2} sx={{ color: '#565e6c', fontWeight: 'bold' }}>
                Drag & Drop a video here or
              </Typography>
              <Button
                variant="contained"
                component="label"
                sx={{
                  backgroundColor: '#636AE8',
                  "&:hover": {
                    backgroundColor: '#303f9f',
                  }
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
