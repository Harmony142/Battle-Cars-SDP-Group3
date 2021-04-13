import React, { useEffect } from "react";
import "./Windows.css";
import CustomizationMenu from './Customization.jsx'
import { playerName, selectedCar } from '../Home/Home.jsx'
import { scoreRed, scoreBlue, timer, car1PlayerName, car2PlayerName, car3PlayerName, car4PlayerName } from '../App.js';

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

const targetCar = selectedCar.split('-')[1];

function uuidv4() {
  // From https://stackoverflow.com/questions/105034/how-to-create-a-guid-uuid
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
    var r = Math.random() * 16 | 0, v = c == 'x' ? r : (r & 0x3 | 0x8);
    return v.toString(16);
  });
}

const PlayingWindow = (props) => {
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
          const element = document.getElementById('car-' + i + '-player-name');
          if(playerName !== '' && carName === playerName) {
            element.innerHTML = 'You';
            element.style.color = '#ffff80';
          } else {
            element.innerHTML = carName.length > 10 ? carName.slice(0, 10) + '...' : carName;
            element.style.color = 'white';
          }
        }
      } catch(err) {
        console.log("could not update player names", err);
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

      if (playerName === window['car' + targetCar + 'PlayerName']) {
        pushToSQS();
      }
      allowed_keys.forEach(key => prevKeysPressed[key] = currKeysPressed[key]);
    }
  }

  async function pushToSQS() {
    // Send user commands to our SQS queue to be read and processed by the hub
    const payload = JSON.parse(JSON.stringify(currKeysPressed));
    payload['StartTime'] = Date.now();
    payload['PlayerName'] = playerName === '' ? null : playerName;
    payload['CarNumber'] = selectedCar;

    // Use a uuid so no messages are deduped since we can't disable deduplication on FIFO SQS queues
    var uuid = uuidv4()
    var params = {
      MessageDeduplicationId: uuid,  // Required for FIFO queues
      MessageGroupId: uuid,  // Required for FIFO queues
      MessageBody: JSON.stringify(payload),
      QueueUrl: 'https://sqs.us-east-2.amazonaws.com/614103748137/car-commands-' + targetCar + '.fifo'
    }
    sqs.sendMessage(params, function(err, data) {
      if (err) {
        // console.log("SQS Send Error", err);
      } else {
        // console.log("SQS Send Success", data.MessageId);
      }
    });
  }

  return (
    <div onKeyUp={handleKeyPress} onKeyDown={handleKeyPress}>
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
          <CustomizationMenu/>
          <h1 className="time-left" id="time-left">20:00</h1>
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
          </div>
        </div>
      </div>
      <textarea className="new-message-input-field"/>
    </div>
  );
};

export default PlayingWindow;
