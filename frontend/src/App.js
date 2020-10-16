import React from 'react';
import './App.css';
import TaigaLogo from './TaigaLogo1Black.png'

import { CameraFeed, CameraMetadataFeed } from './Camera'

function App() {
  return (
    <div className="App">
      <div className="App-header">
        <img src={TaigaLogo} alt='taiga logo' className="taiga-logo"></img>
        <div className="sit-ser-name">SIT onboard camera</div>
      </div>
      <div className="data-container">
        <CameraMetadataFeed></CameraMetadataFeed>
        <CameraFeed></CameraFeed>
      </div>
    </div>
  );
}

export default App;
