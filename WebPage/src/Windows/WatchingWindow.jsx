import React, { useEffect } from "react";
import "./Windows.css";
import CustomizationMenu from './Customization.jsx'
import { scoreRed, scoreBlue, timer, car1PlayerName, car2PlayerName, car3PlayerName, car4PlayerName } from '../App.js';

const WatchingWindow = (props) => {
  useEffect(() => {
    const interval = setInterval(() => {
      // Update the score
      try {
        document.getElementById('score-red').innerHTML = scoreRed;
        document.getElementById('score-blue').innerHTML = scoreBlue;
      } catch(err) {
        console.log("could not update score");
      }

      // Update the timer
      try {
        document.getElementById('time-left').innerHTML = timer;
      } catch(err) {
        console.log("could not update time left");
      }

      // Update who is driving what car
      try {
        for(var i = 1; i <=4; i++) {
          const carName = window['car' + i + 'PlayerName'];
          document.getElementById('car-' + i + '-player-name').innerHTML
            = carName.length > 10 ? carName.slice(0, 10) + '...' : carName;
        }
      } catch(err) {
        console.log("could not update player names", err);
      }
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  return (
    <div>
      <div className="red-half"/>
      <div className="blue-half"/>
      <div className="main-window">
        <div className="screen-wrapper">
          <iframe src="https://viewer.millicast.com/v2?streamId=hrFywT/kgplc3ye"
          allowFullScreen className="room-video"/>
          <h1 className="car-window-name" id="car-1-player-name"
          style={{top: '200px', left: '20px', transform: 'rotate(-90deg)'}}/>
          <h1 className="car-window-name" id="car-2-player-name"
          style={{bottom: '100px', left: '20px', transform: 'rotate(-90deg)'}}/>
          <h1 className="car-window-name" id="car-3-player-name"
          style={{top: '15px', right: '18px', transform: 'rotate(90deg)'}}/>
          <h1 className="car-window-name" id="car-4-player-name"
          style={{bottom: '290px', right: '18px', transform: 'rotate(90deg)'}}/>
        </div>
      </div>
      <div className="bottom-bar">
        <div className="left-bar">
          <h1 className="time-left" id="time-left">20:00</h1>
          <h1 className="score-red" id="score-red">0</h1>
        </div>
        <div className="right-bar">
          <h1 className="score-blue" id="score-blue">0</h1>
        </div>
      </div>
    </div>
  );
};

export default WatchingWindow;
