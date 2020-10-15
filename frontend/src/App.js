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
      current_shot_url: null,
      loading: true
    }
  }

  componentDidMount() {
    fetch('https://picsum.photos/192/108')
    .then(response => {
      if (!response.ok) {
        throw Error("Error fetching data from server!")
      }
      return response.url
    })
    .then(url => {
      this.setState(
        {
          current_shot_url: url,
          loading: false
        }
      )
    })
    .catch(err => {throw Error(err.message)});
  }

  render () {
    return <div className="camera-image-container">
      {
        this.state.loading ?
          (<div className="camera-image">Loading image...</div>)
        : (<img src={this.state.current_shot_url} alt="" className="camera-image"></img>)
      }
      <div className="metadata-string">Some image metadata...</div>
    </div>
  }
}

export default App;
