import React, { useState } from "react";
import {
  Box,
  Grid,
  Typography,
  Button,
  Divider,
  IconButton,
} from "@mui/material";
import DeleteIcon from "@mui/icons-material/Delete";
import DetectedPlate from "./components/DetectedPlate";
import VideoDropZone from "./components/VideoDropZone";

const App = () => {
  const [detectedPlates, setDetectedPlates] = useState([]);
  const [videoKey, setVideoKey] = useState(0);

  const addDetectedPlates = (plates) => {
    setDetectedPlates([...detectedPlates, ...plates]);
  };

  const handleClear = () => {
    setDetectedPlates([]);
    setVideoKey((prevKey) => prevKey + 1);
  };

  return (
    <Box sx={{ p: 4 }}>
      {/* Header */}
      <Box
        display="flex"
        justifyContent="space-between"
        alignItems="center"
        mb={2}
      >
        <Typography variant="h5" fontWeight="bold">
          CarLens
        </Typography>
        <Button
          variant="contained"
          sx={{
            backgroundColor: "#636AE8",
            "&:hover": {
              backgroundColor: "#303f9f",
            },
          }}
          onClick={() =>
            window.open("https://github.com/Mo2Hefny/CarLens", "_blank")
          }
        >
          GitHub
        </Button>
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
            key={videoKey}
            plates={detectedPlates}
            onDetectedPlates={addDetectedPlates}
          />
        </Box>

        {/* Side Panel */}
        <Box
          sx={{
            boxSizing: "border-box",
            maxWidth: 300,
            width: "100%",
            display: "flex",
            flexDirection: "column",
            alignItems: "stretch",
            padding: 2,
            gap: 1,
          }}
        >
          {/* Detected Plate Section */}
          <Box>
            <Typography variant="h6" fontWeight="bold" gutterBottom>
              Detected Plate
            </Typography>
            <Box display="flex" flexDirection="column" gap={1} mb={2}>
              {detectedPlates.map((entry, index) => (
                <DetectedPlate
                  key={index}
                  plateNumber={entry}
                  timestamp={""}
                />
              ))}
            </Box>
          </Box>

          <Divider />

          {/* Plate History Section */}
          <Box
            display="flex"
            flexDirection="column"
            gap={2}
            alignItems="center"
            mt="auto"
            mb={3}
          >
            <Button
              variant="contained"
              color="error"
              startIcon={<DeleteIcon />}
              size="large"
              sx={{
                padding: "10px 20px",
                borderRadius: 1,
                "&:hover": {
                  backgroundColor: "rgba(255, 0, 0, 0.7)",
                },
              }}
              onClick={handleClear}
            >
              Clear
            </Button>
          </Box>
        </Box>
      </Box>
    </Box>
  );
};

export default App;
