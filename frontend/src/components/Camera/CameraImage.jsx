import React from 'react';

const CameraImage = ({ imageUrl, imageLoading }) => (
  <div className="camera-feed-container">
    <img src={imageUrl} className="camera-feed-img" alt="ZWO ASI camera feed" />
    {imageLoading ? <div className="loader camera-feed-overlay" /> : <div />}
  </div>
)

export default CameraImage;
