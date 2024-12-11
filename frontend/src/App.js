import React, { useState } from "react";
import {
  Box,
  Grid,
  Typography,
  Button,
  Divider,
  IconButton,
} from "@mui/material";
import CloudUploadIcon from "@mui/icons-material/CloudUpload";
import CloudDownloadIcon from "@mui/icons-material/CloudDownload";
import DetectedPlate from "./components/DetectedPlate";
import VideoDropZone from "./components/VideoDropZone";

const App = () => {
  const [detectedPlates, setDetectedPlates] = useState([
    { plate: "AEH65FR", timestamp: "01:33" },
    { plate: "AXQEF4R", timestamp: "01:30" },
    { plate: "HGK91LK", timestamp: "01:29" }
  ]);
  const [plateHistory, setPlateHistory] = useState([
    { plate: "AEH65FR", timestamp: "00:52" },
    { plate: "AETR6FR", timestamp: "00:20" },
  ]);

  const [videoSrc, setVideoSrc] = useState("");

  const handleVideoUpload = (event) => {
    event.preventDefault();
    const file = event.dataTransfer.files[0];
    if (file && file.type.startsWith("video/")) {
      const url = URL.createObjectURL(file);
      setVideoSrc(url);
    } else {
      alert("Please drop a valid video file.");
    }
  };

  const handleFileSelect = (event) => {
    const file = event.target.files[0];
    if (file && file.type.startsWith("video/")) {
      const url = URL.createObjectURL(file);
      setVideoSrc(url);
    }
  };

  return (
    <Box sx={{ p: 4 }}>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h5" fontWeight="bold">
          CarLens
        </Typography>
        <Typography variant="body1" color="primary">
          GitHub
        </Typography>
      </Box>

      {/* Main Content */}
      <Grid container spacing={3}>
        {/* Video Section */}
        <Grid item xs={12} md={9.8}>
          <Box
            sx={{
              width: "100%",
              height: "85vh",
              backgroundColor: "#f5f5f5",
              display: "flex",
              justifyContent: "center",
              alignItems: "center",
              mb: 3,
            }}
          >
            <VideoDropZone videoSrc={videoSrc} onDrop={handleVideoUpload} onFileSelect={handleFileSelect} />
          </Box>
        </Grid>

        {/* Side Panel */}
        <Grid item xs={12} md={2.2}>
          {/* Detected Plate Section */}
          <Box mb={4}>
            <Typography variant="h6" fontWeight="bold" gutterBottom>
              Detected Plate
            </Typography>
            <Box display="flex" flexDirection="column" gap={1} mb={2}>
              {
                detectedPlates.map((entry, index) => (
                  <DetectedPlate
                    key={index}
                    plateNumber={entry.plate}
                    timestamp={entry.timestamp}
                  />
                ))
              }
            </Box>
          </Box>

          <Divider sx={{ mb: 3 }} />

          {/* Plate History Section */}
          <Box>
            <Typography variant="h6" fontWeight="bold" gutterBottom>
              Plate History
            </Typography>
            <Box display="flex" flexDirection="column" gap={1} mb={2}>
              {plateHistory.map((entry, index) => (
                <DetectedPlate
                  key={index}
                  plateNumber={entry.plate}
                  timestamp={entry.timestamp}
                  />
              ))}
            </Box>
          </Box>
          {/* <Box display="flex" flexDirection="column" gap={2} alignItems="center" mt="auto">
            <Button
              variant="outlined"
              startIcon={<CloudUploadIcon />}
              size="small"
            >
              Upload
            </Button>
            <Button
              variant="contained"
              startIcon={<CloudDownloadIcon />}
              size="small"
            >
              Download
            </Button>
          </Box> */}
        </Grid>
      </Grid>
    </Box>
  );
};

export default App;