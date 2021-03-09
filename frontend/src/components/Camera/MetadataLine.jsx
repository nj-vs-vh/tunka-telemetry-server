import React, { useContext } from 'react';

import TextWithIcon from '../shared/TextWithIcon';
import localtimeContext from '../../context/localtimeContext';

import CameraIcon from '../../img/icons/camera.png';
import ClockIcon from '../../img/icons/clock.png';
import RecordingOnIcon from '../../img/icons/rec-on.png';
import RecordingOffIcon from '../../img/icons/rec-off.png';


const MetadataLine = ({ metadata }) => {

  const localtime = useContext(localtimeContext);
  const nextShotExpectedIn = Math.round(
    (new Date(metadata.shot_datetime).getTime() + metadata.period * 1000 - new Date(localtime).getTime()) / 1000
  )

  if (metadata.gain)  // TODO: proper error handling and more meaningful test here
  {
    return (
      <span className="metadata-row">
        <TextWithIcon icon={ClockIcon}>
          {
            (nextShotExpectedIn > -3)
            ? `next shot in ${nextShotExpectedIn}s, period ${metadata.period}s`
            : (
              <span style={ {color:'red'} }>
                shot is {Math.abs(nextShotExpectedIn)}s late, network problems?
              </span>
            )
          }
        </TextWithIcon>
        <TextWithIcon icon={CameraIcon}>
          exposure = {metadata.exposure}s, gain = {metadata.gain}, camera T = {metadata.device_temperature}°C
        </TextWithIcon>
        <TextWithIcon icon={metadata.save_to_disk.enabled ? RecordingOnIcon : RecordingOffIcon}>
          {metadata.save_to_disk.enabled ? `recording each ${metadata.save_to_disk.period} s` : 'not recording'}
        </TextWithIcon>
      </span>
    )
  }
  return <span className="metadata-row">Unavailable</span>
}

export default MetadataLine;
