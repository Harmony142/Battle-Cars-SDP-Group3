import React, { useEffect } from "react";
import "./Windows.css";
import { Link } from "react-router-dom";
import { playerName, selectedCar } from '../Home/Home.jsx'
import { scoreRed, scoreBlue, timer, car1PlayerName, car2PlayerName, car3PlayerName, car4PlayerName, winner, overtime }
    from '../App.js';

const promise = require('promise');
const confetti = require('canvas-confetti');
confetti.Promise = promise;

var myConfetti = confetti.create(document.getElementById('page-wrapper'), {
    resize: true,
    useWorker: true
});

var goalConfettiLength = 2 * 1000;
var redEnd = Date.now();
var blueEnd = Date.now();
var redColors = ['#DC143C', '#B22222', '#F08080'];
var blueColors = ['#191970', '#1E90FF', '#00BFFF'];
var confettiDefaults = { startVelocity: 30, spread: 360, ticks: 60, zIndex: 2 };

function randomInRange(min, max) {
  return Math.random() * (max - min) + min;
}

const prevKeysPressed = {'KeyW':false, 'KeyA':false, 'KeyS':false, 'KeyD':false, 'ShiftLeft':false};
const currKeysPressed = {'KeyW':false, 'KeyA':false, 'KeyS':false, 'KeyD':false, 'ShiftLeft':false};
const allowed_keys = Object.keys(currKeysPressed);

const AWS = require('aws-sdk');

const sqs = new AWS.SQS({
    accessKeyId: 'AKIAY563PRYUWD457KGQ',
    secretAccessKey: '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',
    region: 'us-east-2'
});

document.addEventListener('keydown', e => {if(allowed_keys.includes(e.code)){currKeysPressed[e.code] = true;}});
document.addEventListener('keyup', e => {if(allowed_keys.includes(e.code)){currKeysPressed[e.code] = false;}});

document.body.style.overflow = "hidden";

function uuidv4() {
  // From https://stackoverflow.com/questions/105034/how-to-create-a-guid-uuid
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    var r = Math.random() * 16 | 0, v = c == 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
}

async function pushToSQS(payload) {
  if (selectedCar !== null) {
    const targetCar = selectedCar.split('-')[1];
    const currentPlayer = window['car' + targetCar + 'PlayerName'];
    if (currentPlayer === '' || playerName === currentPlayer) {
      // Use a uuid so no messages are deduped since we can't disable deduplication on FIFO SQS queues
      const uuid = uuidv4()
      const params = {
        MessageDeduplicationId: uuid,  // Required for FIFO queues
        MessageGroupId: uuid,  // Required for FIFO queues
        MessageBody: JSON.stringify(payload),
        QueueUrl: 'https://sqs.us-east-2.amazonaws.com/614103748137/car-commands-' + targetCar + '.fifo'
      }

      sqs.sendMessage(params, function(err, data) {
        if (err) {
          console.log("SQS Send Error", err);
        } else {
          console.log("SQS Send Success", data.MessageId);
        }
      });
    }
  }
}

const sendCustomizationData = (event) => {
  const payload = JSON.parse(JSON.stringify(currKeysPressed));
  payload['PlayerName'] = playerName === '' ? null : playerName;
  payload['Pattern'] = document.getElementById('dropup-button').innerHTML;
  payload['Red'] = document.getElementById('red-slider').value;
  payload['Green'] = document.getElementById('green-slider').value;
  payload['Blue'] = document.getElementById('blue-slider').value;

  pushToSQS(payload);
};

const PlayingWindow = (props) => {
  useEffect(() => {
    const interval = setInterval(function() {
      if (Date.now() < redEnd) {
        myConfetti({
          particleCount: 3,
          angle: 120,
          spread: 55,
          origin: { x: 1 },
          colors: redColors,
          zIndex: 2
        });
     }}, 50);

    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const interval = setInterval(function() {
      if (Date.now() < blueEnd) {
        myConfetti({
          particleCount: 3,
          angle: 60,
          spread: 55,
          origin: { x: 0 },
          colors: blueColors,
          zIndex: 2
        });
     }}, 50);

    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const interval = setInterval(function() {
      if (winner === 'Red Team' || winner === 'Blue Team') {
        var particleCount = 50;
        // since particles fall down, start a bit higher than random
        myConfetti(Object.assign({}, confettiDefaults, { particleCount, origin: { x: randomInRange(0.1, 0.3), y: Math.random() - 0.2 } }));
        myConfetti(Object.assign({}, confettiDefaults, { particleCount, origin: { x: randomInRange(0.7, 0.9), y: Math.random() - 0.2 } }));
      }}, 250);

    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const interval = setInterval(() => {
      // Update the score
      try {
        const redScore = document.getElementById('score-red');
        if (scoreRed > parseInt(redScore.innerHTML)) {
          redEnd = Date.now() + goalConfettiLength;
        }
        redScore.innerHTML = scoreRed;

        const blueScore = document.getElementById('score-blue');
        if (scoreBlue > blueScore.innerHTML) {
          blueEnd = Date.now() + goalConfettiLength;
        }
        blueScore.innerHTML = scoreBlue;
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

  const handleKeyPress = (event) => {
    if(JSON.stringify(prevKeysPressed) !== JSON.stringify(currKeysPressed)){
      allowed_keys.forEach(key => {
        var keyStyle = document.getElementById(key).style;
        if(currKeysPressed[key]) {
            keyStyle.borderStyle = 'inset';
            keyStyle.backgroundColor = '#ffff80';
        } else {
            keyStyle.borderStyle = 'outset';
            keyStyle.backgroundColor = 'lightgrey';
        }
      });

      // Send user commands to our SQS queue to be read and processed by the hub
      const payload = JSON.parse(JSON.stringify(currKeysPressed));
      payload['PlayerName'] = playerName === '' ? null : playerName;

      pushToSQS(payload);
      allowed_keys.forEach(key => prevKeysPressed[key] = currKeysPressed[key]);
    }
  }

  const selectPattern = (event) => {
    document.getElementById("dropup-button").innerHTML = event.target.innerHTML;
    sendCustomizationData();
  };

  return (
    <div id='page-wrapper' onKeyUp={handleKeyPress} onKeyDown={handleKeyPress}>
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
          <div className="slider-wrapper">
            <div className="slider-container">
              <input type="range" min="0" max="255" className="red-slider" id="red-slider"
              onMouseUp={sendCustomizationData}/>
            </div>
            <div className="slider-container">
              <input type="range" min="0" max="255" className="green-slider" id="green-slider"
              onMouseUp={sendCustomizationData}/>
            </div>
            <div className="slider-container">
              <input type="range" min="0" max="255" className="blue-slider" id="blue-slider"
              onMouseUp={sendCustomizationData}/>
            </div>
          </div>
          <div className="dropup">
            <button className="dropup-button" id="dropup-button">Party</button>
            <div className="dropup-content">
              <pattern onMouseDown={selectPattern}>Off</pattern>
              <pattern onMouseDown={selectPattern}>Solid</pattern>
              <pattern onMouseDown={selectPattern}>Flashing</pattern>
              <pattern onMouseDown={selectPattern}>Alternating</pattern>
              <pattern onMouseDown={selectPattern}>Snake</pattern>
              <pattern onMouseDown={selectPattern}>Pulse</pattern>
              <pattern onMouseDown={selectPattern}>Wave</pattern>
              <pattern onMouseDown={selectPattern}>Rainbow</pattern>
              <pattern onMouseDown={selectPattern}>Party</pattern>
            </div>
          </div>
          <h1 className="time-left" id="time-left" style={{left: '220px'}}>20:00</h1>
          <h1 className="overtime-flag" id="overtime-flag" style={{left: '224px'}}>Overtime!</h1>
          <h1 className="score-red" id="score-red">0</h1>
        </div>
        <div className="right-bar">
          <h1 className="score-blue" id="score-blue">0</h1>
          <div className="controls-wrapper">
            <div className="wasd-wrapper">
              <h1 className="key" id="KeyW" style={{top: '0px', left: '53px'}}>W</h1>
              <h1 className="key" id="KeyA" style={{bottom: '0px', left: '0px'}}>A</h1>
              <h1 className="key" id="KeyS" style={{bottom: '0px', left: '53px'}}>S</h1>
              <h1 className="key" id="KeyD" style={{bottom: '0px', right: '0px'}}>D</h1>
            </div>
            <h1 className="shift-key" id="ShiftLeft">LShift</h1>
            <Link to={'/'} className="home-button" id="home-button" style={{top:'0px', left:'0px'}}>Back to Login</Link>
          </div>
        </div>
      </div>
      <textarea className="new-message-input-field"/>
    </div>
  );
};

export default PlayingWindow;
export { pushToSQS };
