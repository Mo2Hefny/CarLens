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
  const [detectedPlates, setDetectedPlates] = useState([]);
  const [plateHistory, setPlateHistory] = useState([]);
  const [videoSrc, setVideoSrc] = useState("");

  const addDetectedPlates = (plate, videoTime) => {
    setPlateHistory((prevHistory) => {
      // Filter new plates based on the previous history
      const newPlates = plate.filter((entry) => {
        const isDuplicate = prevHistory.some((oldPlate) => {
          console.log("Comparing:", oldPlate.plate, entry.plate);
          return oldPlate.plate === entry.plate; // Use strict equality
        });
        return !isDuplicate;
      });
  
      // Add timestamps to new plates
      newPlates.forEach((entry) => {
        entry.timestamp = videoTime;
      });
  
      // Update detected plates for immediate UI display
      setDetectedPlates(plate);
  
      // Return the updated history
      return [...prevHistory, ...newPlates];
    });
  }

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
      <Box display="flex" flexDirection="row" justifyContent="center">
        {/* Video Section */}
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
          <VideoDropZone
            plates={detectedPlates}
            onDetectedPlates={addDetectedPlates} 
            />
        </Box>

        {/* Side Panel */}
        <Box sx={{
          boxSizing: "border-box",
          maxWidth: 300,
          width: "100%",
          display: "flex",
          flexDirection: "column",
          alignItems: "stretch",
          padding: 2,
          gap: 1,
        }}>
          {/* Detected Plate Section */}
          <Box>
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

          <Divider />

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
        </Box>
      </Box>
    </Box>
  );
};

export default App;