import React, { useState, useEffect } from 'react';

import CameraImage from './CameraImage';
import MetadataLine from './MetadataLine';

import '../../App.css';
import './index.css';
import './LoadingSpinner.css';


const OVERRIDE_PORT = undefined;


export function CameraFeed() {
  const [metadata, setMetadata] = useState(null);
  const [imageUrl, setImageUrl] = useState(null);
  const [imageLoading, setImageLoading] = useState(false);

  useEffect(
    () => {
      let host = OVERRIDE_PORT ? `${document.location.hostname}:${OVERRIDE_PORT}` : document.location.host
      let wsUrl = `ws://${host}/ws/camera-feed`;
      let ws = new WebSocket(wsUrl);
      ws.onmessage = function (event) {
        let data = event.data;
        if (data instanceof Blob) {
          setImageUrl(URL.createObjectURL(data));
          setImageLoading(false);
        } else {
          setMetadata(JSON.parse(data));
          setImageLoading(true);  // backend sends metadata before image, so from now on we are loading image
        }
      };
      return () => ws.close();
    },
    []
  );

  if (metadata === null) {
    return <div className='data-page'><span>Loading...</span></div>
  }
  else {
    return (
      <div className='data-page'>
        <div className="camera-feed-column">
          <CameraImage imageUrl={imageUrl} imageLoading={imageLoading} />
          <MetadataLine metadata={metadata} />
        </div>
      </div>
    )
  }
}


export default CameraFeed;
