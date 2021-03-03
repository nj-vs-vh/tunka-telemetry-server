import React, { useState, useEffect }  from 'react';
import getFetchEffect from './fetchState'

import ClockIcon from './img/icons/clock.png'
import SunIcon from './img/icons/sun.png'
import MoonIcon from './img/icons/moon.png'
import TemperatureIcon from './img/icons/termometer.png'
import HumidityIcon from './img/icons/droplet.png'

import TextWithIcon from './components/shared/TextWithIcon'

import './ObservationConditionsBar.css'


function ObservationConditionsBar(props) {
    const [obsCond, setObsCond] = useState(null)
    const [localTime, setLocalTime] = useState(0)
    const [lastSyncLocalTime, setLastSyncLocalTime] = useState(0)

    function setConditionsAndSyncLocalTime(newObsCond) {
        let syncLocalTime = Date.parse(newObsCond.local_time).valueOf()
        setLocalTime(syncLocalTime)
        setLastSyncLocalTime(syncLocalTime)
        setObsCond(newObsCond)
    }
    
    // eslint-disable-next-line react-hooks/exhaustive-deps
    useEffect(getFetchEffect(setConditionsAndSyncLocalTime, "/api/observation-conditions", 30000), [])
    useEffect(() => {
        let interval = setInterval( () => {setLocalTime(localTime+1000)}, 1000);
        return () => clearInterval(interval);
    });

    if (obsCond === null) {
        return <div className="obscondbar">Loading...</div>
    }
    else {
        return <div className="obscondbar">
            <TextWithIcon icon={ClockIcon}>
                {`${new Date(localTime).toLocaleString('ru-RU')} Irkutsk time`}
            </TextWithIcon>
            <TextWithIcon icon={SunIcon}>
                {
                    !obsCond.is_night ? 'Day' : (obsCond.is_astronomical_night ? 'Night (astronomical)' : 'Night')
                    + ', sun' + (obsCond.is_night ? 'rise' : 'set') + ' at '
                    + new Date(obsCond.is_night ? obsCond.sunrise.next : obsCond.sunset.next).toLocaleTimeString('ru-RU')
                }
            </TextWithIcon>
            <TextWithIcon icon={MoonIcon}>
                {
                    obsCond.is_moonless ? 'Moonless' : 'Moonlit'
                    + ', ' + (obsCond.is_moonless ? 'rises' : 'sets') + ' at '
                    + new Date(obsCond.is_moonless ? obsCond.moonrise.next : obsCond.moonset.next).toLocaleTimeString('ru-RU')
                }
            </TextWithIcon>
            <TextWithIcon icon={TemperatureIcon}>
                {!('external_temperature' in obsCond) ? 'Unavailable' : `${obsCond.external_temperature} °C`}
            </TextWithIcon>
            <TextWithIcon icon={HumidityIcon}>
                {!('external_humidity' in obsCond) ? 'Unavailable' : `${obsCond.external_humidity} %`}
            </TextWithIcon>
            <span className="synced-s-ago-text">
                synchronized {(localTime - lastSyncLocalTime) / 1000}s ago
            </span>
        </div>
    }
}


export default ObservationConditionsBar;
