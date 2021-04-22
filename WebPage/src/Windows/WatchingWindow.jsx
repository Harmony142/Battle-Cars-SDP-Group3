import React, { useEffect } from "react";
import "./Windows.css";
import CustomizationMenu from './Customization.jsx'
import { playerName, selectedCar } from '../Home/Home.jsx'
import { scoreRed, scoreBlue, timer, car1PlayerName, car2PlayerName, car3PlayerName, car4PlayerName, winner, overtime }
    from '../App.js';

document.body.style.overflow = "hidden";

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
        const max_length = 10;
        for(var i = 1; i <=4; i++) {
          const carName = window['car' + i + 'PlayerName'];
          const element = document.getElementById('car-' + i + '-player-name');
          if(playerName !== '' && carName === playerName) {
            element.innerHTML = 'You';
            element.style.color = '#ffff80';
          } else {
            element.innerHTML = carName.length > 10 ? carName.slice(0, max_length) + '...' : carName;
            element.style.color = 'white';
          }
        }
      } catch(err) {
        console.log("could not update player names", err);
      }

      // Update the victory card
      try {
        const victoryCard = document.getElementById('victory-card')
        if (winner == 'Red Team') {
            victoryCard.innerHTML = 'Red Team Wins!';
            victoryCard.style.background = 'firebrick';
            victoryCard.style.visibility = 'visible';
        } else if (winner == 'Blue Team') {
            victoryCard.innerHTML = 'Blue Team Wins!';
            victoryCard.style.background = 'dodgerblue';
            victoryCard.style.visibility = 'visible';
        } else if (winner == 'Draw') {
            victoryCard.innerHTML = 'It\'s a Draw!';
            victoryCard.style.background = 'linear-gradient(90deg, dodgerblue 5%, firebrick)';
            victoryCard.style.visibility = 'visible';
        } else {
            victoryCard.style.visibility = 'hidden';
        }
      } catch(err) {
         console.log('could not update victory card');
      }

      // Update overtime flag
      try {
        const overtimeStyle = document.getElementById('overtime-flag').style;
        if (overtime) {
          overtimeStyle.visibility = 'visible';
        } else {
          overtimeStyle.visibility = 'hidden';
        }
      } catch(err) {
        console.log('could not update overtime flag');
      }
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  return (
    <div>
      <div className="red-half"/>
      <div className="blue-half"/>
      <div className="main-window">
        <h1 className="victory-card" id="victory-card">Red Team Wins!</h1>
        <div className="screen-wrapper">
          <iframe src="https://viewer.millicast.com/v2?streamId=hrFywT/kgplc3ye"
          allowFullScreen className="room-video"/>
          <h1 className="car-window-name" id="car-1-player-name"
          style={{top: '150px', left: '20px', transform: 'rotate(-90deg)'}}/>
          <h1 className="car-window-name" id="car-2-player-name"
          style={{bottom: '50px', left: '20px', transform: 'rotate(-90deg)'}}/>
          <h1 className="car-window-name" id="car-3-player-name"
          style={{top: '0px', right: '18px', transform: 'rotate(90deg)'}}/>
          <h1 className="car-window-name" id="car-4-player-name"
          style={{bottom: '200px', right: '18px', transform: 'rotate(90deg)'}}/>
        </div>
      </div>
      <div className="bottom-bar">
        <div className="left-bar">
          <h1 className="time-left" id="time-left">20:00</h1>
          <h1 className="overtime-flag" id="overtime-flag">Overtime!</h1>
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
