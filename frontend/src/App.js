import React from 'react';
import './App.css';
import TaigaLogo from './img/TaigaLogo1Black.png'
import Octocat from './img/GitHub-Mark-64px.png'

import CameraFeed from './Camera'
import ObservationConditionsBar from './ObservationConditionsBar'

function App() {
  return (
    <div className="App">
      <div className="header">
        <a href="https://taiga-experiment.info">
          <img src={TaigaLogo} href="https://taiga-experiment.info/" alt='taiga logo' className="taiga-logo"></img>
        </a>
        <span className="sit-ser-name">SIT camera</span>
        <a href="https://github.com/nj-vs-vh/tunka-telemetry-server">
          <img src={Octocat} alt='link to GitHub repo with app source' className="github-logo"></img>
        </a>
      </div>
      <ObservationConditionsBar></ObservationConditionsBar>
      <main>
        <CameraFeed></CameraFeed>
      </main>
      <div className="footer">
        Camera interface and web app by <a className="footerlink" href="https://github.com/nj-vs-vh">Igor Vaiman </a>
        (<a className="footerlink" href="mailto:gosha.vaiman@gmail.com">contact</a>).
        Icons by <a className="footerlink" href="https://www.flaticon.com/authors/freepik">Freepik</a>.
      </div>
    </div>
  );
}

export default App;
