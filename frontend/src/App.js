import React, { Component } from 'react';
import './App.css';

function App() {
  return (
    <div className="App">
      <div className="App-header">
        <h1>SIT server telemetry page</h1>
      </div>
        <CameraImage></CameraImage>
      </div>
  );
}

class CameraImage extends Component {
  constructor() {
    super();
    this.state = {
      latest_shot_base64: null,
      loading: false,
    }
  }

  componentDidMount () {
    this.setState({loading: true})
    var intervalId = setInterval(this.fetchLatestShotInBase64.bind(this), 100);
    this.setState({intervalId: intervalId});
  }

  componentWillUnmount () {
    clearInterval(this.state.intervalId);
  }

  fetchLatestShotInBase64() {
    fetch('/api/latest-shot')
    .then(response => {
      if (!response.ok) { console.log(response) }
      return response.text()
    })
    .then(base64 => {
      this.setState({latest_shot_base64: base64, loading: false
    })})
    .catch(err => {
      clearInterval(this.state.intervalId);
      throw Error(err.message)
    });
  }

  render () {
    return <div className="camera-image-container">
      {
        this.state.loading ?
          (<div className="camera-image">Loading...</div>)
        : (<img src={`data:image/jpeg;base64,${this.state.latest_shot_base64}`} alt="" className="camera-image"></img>)
      }
      <div className="metadata-string">Some image metadata...</div>
    </div>
  }
}

export default App;
