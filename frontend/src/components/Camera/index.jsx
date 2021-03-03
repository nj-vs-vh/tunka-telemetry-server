import React, { useState, useEffect } from 'react';

import '../../App.css'
import './index.css';
import './LoadingSpinner.css'

import TextWithIcon from '../shared/TextWithIcon'

import CameraIcon from '../../img/icons/camera.png'
import ClockIcon from '../../img/icons/clock.png'
import RecordingOnIcon from '../../img/icons/rec-on.png'
import RecordingOffIcon from '../../img/icons/rec-off.png'


export function CameraFeed() {
    const [metadata, setMetadata] = useState(null)
    const [imageUrl, setImageUrl] = useState(null)
    const [imageLoading, setImageLoading] = useState(false)

    useEffect(
        () => {
            let ws = new WebSocket('ws://' + document.domain + ':8000/ws-camera-feed');
            ws.onmessage = function (event) {
                let data = event.data;
                if (data instanceof Blob) {
                    setImageUrl(URL.createObjectURL(data));
                    setImageLoading(false);
                } else {
                    setMetadata(JSON.parse(data));
                    setImageLoading(true);  // backend sends metadata the image, so from now on we load image
                }
            };
            return () => ws.close();
        },
        []
    )

    if (metadata === null) {
        return <div className='data-page'><span>Loading...</span></div>
    }
    else {
        return (
            <div className='data-page'>
                <div className="camera-feed-column">
                    <div className="camera-feed-container">
                        <img src={imageUrl} className="camera-feed-img" alt="ZWO ASI camera feed" />
                    { imageLoading ? <div className="loader camera-feed-overlay">Loading...</div> : <div /> }
                    </div>
                    { metadata.gain ?
                        <span className="metadata-row">
                            <TextWithIcon icon={ClockIcon}>
                                shot at {new Date(metadata.shot_datetime).toLocaleTimeString('ru-RU')}, period {metadata.period} s
                            </TextWithIcon>
                            <TextWithIcon icon={CameraIcon}>
                                exposure = {metadata.exposure} s, gain = {metadata.gain}, camera T = {metadata.device_temperature}°C
                            </TextWithIcon>
                            <TextWithIcon icon={metadata.save_to_disk.enabled ? RecordingOnIcon : RecordingOffIcon}>
                                {metadata.save_to_disk.enabled ? `recording each ${metadata.save_to_disk.period} s` : 'not recording'}
                            </TextWithIcon>
                        </span>
                        :
                        <span className="metadata-row">Unavailable</span>
                    }
                </div>
            </div>
        )
    }
}


export default CameraFeed;
