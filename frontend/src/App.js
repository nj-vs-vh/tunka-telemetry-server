import React from 'react';
import './App.css';
import TaigaLogo from './TaigaLogo1Black.png'

import { CameraFeed, CameraMetadataFeed } from './Camera'

function App() {
  return (
    <div className="App">
      <div className="header">
        <img src={TaigaLogo} alt='taiga logo' className="taiga-logo"></img>
        <div className="sit-ser-name">SIT camera (тестовый режим)</div>
      </div>
      <content>
        <div className="data-container">
          <CameraFeed></CameraFeed>
        </div>
        <div className="data-container">
          <CameraMetadataFeed></CameraMetadataFeed>
        </div>
      </content>
    </div>
  );
}

export default App;
