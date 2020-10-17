import React, { Component, useState, useEffect } from 'react';

import './Camera.css';


// var cameraConnected = false


export class CameraFeed extends Component {
    constructor() {
        super();
        this.state = { cameraOk: true }
    }
    render () {
        if (this.state.cameraOk) { return <img src="/api/camera-feed" alt="" className="camera-feed"></img> }
        else { return <div className="camera-feed">Something's wrong with the camera...</div> }
    }
}


function fetchLatestMetadata (setNewMetadata) {
    try {
        fetch("/api/latest-camera-metadata")
        .then( response => {
            if (!response.ok) { console.log(response) }
            return response.json()
        })
        .then( json => {setNewMetadata(json)})
    } catch (err) {
      console.error(err.message);
    }
};


export function CameraMetadataFeed() {
    const [currentMetadata, setMetadata] = useState(null)
    
    useEffect( () => {
        let interval = setInterval(() => {fetchLatestMetadata(setMetadata)}, 3000)
        return function cleanup() {
            clearInterval(interval);
        }
    }, [])

    if (currentMetadata === null) {
        return <div>Loading...</div>
    }
    else {
        return <div className="metadata-block">
            <table>
                <tr><th>Exposure</th><th>{currentMetadata.exposure}</th></tr>
                <tr><th>Gain</th><th>{currentMetadata.gain}</th></tr>
                <tr><th>Device temperature</th><th>{currentMetadata.device_temperature}</th></tr>
                <tr>
                    <th>Device datetime</th>
                    <th>{
                        new Date( Date.parse(currentMetadata.device_time) ).toLocaleString()
                    }</th>
                </tr>
            </table>
        </div>
    }
}
