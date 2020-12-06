import React, { Component, useState, useEffect } from 'react';
import getFetchEffect from './fetchState'

import './Camera.css';
import './App.css'


// var cameraConnected = false


export function CameraFeed() {
    const [metadata, setMetadata] = useState(null)
    
    useEffect(getFetchEffect(setMetadata, "/api/latest-camera-metadata", 3000), [])

    if (metadata === null) {
        return <div className='data-page'><span>Loading...</span></div>
    }
    else {
        return <div className='data-page'>
            <div className="camera-col">
                <img src="/api/camera-feed" alt="ZWO ASI camera feed" className="camera-feed"></img>
                { metadata.gain ?
                    <span className="metadata-line">
                        <span>exposure: {metadata.exposure}s</span>
                        <span>gain: {metadata.gain}</span>
                        <span>period: {metadata.period}s</span>
                        <span>camera temperature: {metadata.device_temperature}°C</span>
                        <span>shot at: {new Date(metadata.shot_datetime).toLocaleTimeString('ru-RU')}</span>
                    </span>
                    : <span className="metadata-line">No metadata available :(</span>
                }
            </div>
        </div>
    }
}


// export function CameraMetadataFeed() {
    

//     if (currentMetadata === null) {
//         return <div>Loading...</div>
//     }
//     else {
//         return <div className="metadata-block">
//             <table> <tbody>
//                 <tr><td>Exposure</td><td>{currentMetadata.exposure}</td></tr>
//                 <tr><td>Gain</td><td>{currentMetadata.gain}</td></tr>
//                 <tr><td>Device temperature</td><td>{currentMetadata.device_temperature}</td></tr>
//                 <tr>
//                     <td>Device datetime</td>
//                     <td>
//                         { new Date( Date.parse(currentMetadata.device_time) ).toLocaleString() }
//                     </td>
//                 </tr>
//             </tbody> </table>
//         </div>
//     }
// }


export default CameraFeed;
