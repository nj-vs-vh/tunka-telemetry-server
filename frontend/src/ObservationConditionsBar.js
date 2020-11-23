import React, { useState, useEffect }  from 'react';
import getFetchEffect from './fetchState'

import ClockIcon from './clock-icon.png'
import SunIcon from './sun-icon.png'
import MoonIcon from './moon-icon.png'

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
    
    useEffect(getFetchEffect(setConditionsAndSyncLocalTime, "/api/observation-conditions", 30000), [])
    useEffect(() => {
        let interval = setInterval( () => {setLocalTime(localTime+1000)}, 1000);
        return () => clearInterval(interval);
        }
    );

    if (obsCond === null) {
        return <div className="obscondbar">Loading...</div>
    }
    else {
        return <div className="obscondbar">
            <img src={ClockIcon} className="baricon" alt=""></img>
            <span className="bartext">
                {new Date(localTime).toLocaleString('ru-RU')} Irkutsk time (sync {(localTime - lastSyncLocalTime) / 1000} s ago)
            </span>
            <img src={SunIcon} className="baricon" alt=""></img>
            <span className="bartext">
                {!obsCond.is_night ? 'Day' : (obsCond.is_astronomical_night ? 'Night (astronomical)' : 'Night')}
                {
                    ', sun' + (obsCond.is_night ? 'rise' : 'set') + ' at '
                    + new Date(obsCond.is_night ? obsCond.sunrise.next : obsCond.sunset.next).toLocaleTimeString('ru-RU')
                }
            </span>
            <img src={MoonIcon} className="baricon" alt=""></img>
            <span className="bartext">
                {obsCond.is_moonless ? 'Moonless' : 'Moonlit'}
                {
                    ', ' + (obsCond.is_moonless ? 'rises' : 'sets') + ' at '
                    + new Date(obsCond.is_moonless ? obsCond.moonrise.next : obsCond.moonset.next).toLocaleTimeString('ru-RU')
                }
            </span>
        </div>
    }
}


export default ObservationConditionsBar;