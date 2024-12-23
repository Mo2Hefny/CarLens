import React from 'react';
import PropTypes from 'prop-types';
import { Box, Typography } from '@mui/material';

const DetectedPlate = ({ plateNumber, timestamp }) => {
  return (
    <Box
      sx={{
        display: 'flex',
        flexDirection: 'row',
        justifyContent: 'space-between',
        alignItems: 'center',
        gap: '16px',
        padding: '6px 8px',
      }}
    >
      <Typography variant="body1" sx={{ color: '#565e6c', fontWeight: 'bold' }}>
        {plateNumber}
      </Typography>
      <Typography
        variant="caption"
        sx={{ color: '#666', fontSize: '12px' }}
      >
        {timestamp}
      </Typography>
    </Box>
  );
};

DetectedPlate.propTypes = {
  plateNumber: PropTypes.string.isRequired,
  timestamp: PropTypes.string.isRequired,
};

export default DetectedPlate;
