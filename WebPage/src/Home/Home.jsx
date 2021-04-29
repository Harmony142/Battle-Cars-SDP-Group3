import React, { useEffect } from "react";
import { Link } from "react-router-dom";
import { pushToSQS } from '../Windows/PlayingWindow.jsx'
import { car1PlayerName, car2PlayerName, car3PlayerName, car4PlayerName } from '../App.js';

import "./Home.css";

var playerName = '';
var selectedCar = null;

function resetSelections() {
  playerName = '';
  selectedCar = null;
};

function updateCarButtons() {
  // Update who is driving what car
  try {
    for(var i = 1; i <=4; i++) {
      const carName = window['car' + i + 'PlayerName'];
      const label = document.getElementById('car-' + i + '-player-name');
      const activeButton = document.getElementById('car-' + i).style;
      const disabledButton = document.getElementById('disabled-car-' + i).style;
      if(carName !== '') {
        label.innerHTML = 'Current Player: ' + (carName.length > 10 ? carName.slice(0, 10) + '...' : carName);

        // Disable button so other players can't select this unless the name is the same
        if (playerName !== carName) {
          activeButton.visibility = 'hidden';
          disabledButton.visibility = 'visible';
        } else {
          activeButton.visibility = 'visible';
          disabledButton.visibility = 'hidden';
        }
      }
      else {
        activeButton.visibility = 'visible';
        disabledButton.visibility = 'hidden';
        label.style.visibility = 'hidden';
      }
    }
  } catch(err) {
    console.log("could not update player names", err);
  }
};

const Home = () => {
  useEffect(() => {
    const interval = setInterval(() => {
      updateCarButtons();
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  const updatePlayButton = () => {
    const playButtonStyle = document.getElementById('play-button').style;
    const disabledPlayButtonStyle = document.getElementById('disabled-play-button').style;

    if(selectedCar !== null && playerName !== '') {
        playButtonStyle.visibility = 'visible';
        disabledPlayButtonStyle.visibility = 'hidden';
    } else {
        playButtonStyle.visibility = 'hidden';
        disabledPlayButtonStyle.visibility = 'visible';
    }
  };

  const handleCarEnter = (event) => {
    // Highlight button
    document.getElementById('car-' + event.target.id.split('-')[1]).style.borderStyle = 'inset';
  };

  const handleCarLeave = (event) => {
    // Remove button highlight
    const button = document.getElementById('car-' + event.target.id.split('-')[1]);
    if(button.id !== selectedCar) {
      button.style.borderStyle = 'outset';
    }
  };

  const handleCarSelection = (event) => {
    // Set this button pressed down
    const button = document.getElementById('car-' + event.target.id.split('-')[1]);
    console.log('Selected Car ' + button.id);
    selectedCar = button.id;
    const selectedCarStyle = button.style;
    selectedCarStyle.borderStyle = 'inset';
    selectedCarStyle.backgroundColor = 'darkgrey';

    // Set all other buttons not pressed
    for(var i = 1; i <= 4; i++) {
      const car_id = 'car-' + i;
      if(car_id !== button.id) {
        const carSelectStyle = document.getElementById(car_id).style;
        carSelectStyle.borderStyle = 'outset';
        carSelectStyle.backgroundColor = 'lightgrey';
      }
    }

    updatePlayButton();
  };

  const handleNameChange = (event) => {
    playerName = event.target.value;
    updateCarButtons();
    updatePlayButton();
  };

  const sendInitialMessage = (event) => {
    // Connect the player and set the colors to the default Party to show someone has connected
    const payload = JSON.parse(JSON.stringify({'KeyW':false, 'KeyA':false, 'KeyS':false, 'KeyD':false, 'ShiftLeft':false}));
    payload['PlayerName'] = playerName === '' ? null : playerName;
    payload['Pattern'] = 'Party';
    payload['Red'] = 50;
    payload['Green'] = 50;
    payload['Blue'] = 50;

    pushToSQS(payload);
  };

  return (
    <div className="home-window">
      <div className="red-half"/>
      <div className="blue-half"/>
      <div className="input-wrapper">
        <h1 className="title">Battle Cars</h1>
        <h1 className="car-selection-label">Choose Your Car:</h1>
        <div className="car-selection-wrapper">
          <div className="car-wrapper" style={{top: '0px', left: '0px'}}>
            <h1 className="car-selection" id="car-1"
              onMouseEnter={handleCarEnter} onMouseLeave={handleCarLeave} onMouseDown={handleCarSelection}>Car 1</h1>
            <h1 className="disabled-car-selection" id="disabled-car-1">Car 1</h1>
            <h2 className="car-player-name" id="car-1-player-name"
              onMouseEnter={handleCarEnter} onMouseLeave={handleCarLeave} onMouseDown={handleCarSelection}/>
          </div>

          <div className="car-wrapper" style={{bottom: '0px', left: '0px'}}>
            <h1 className="car-selection" id="car-2"
              onMouseEnter={handleCarEnter} onMouseLeave={handleCarLeave} onMouseDown={handleCarSelection}>Car 2</h1>
            <h1 className="disabled-car-selection" id="disabled-car-2">Car 2</h1>
            <h2 className="car-player-name" id="car-2-player-name"
              onMouseEnter={handleCarEnter} onMouseLeave={handleCarLeave} onMouseDown={handleCarSelection}/>
          </div>

          <div className="car-wrapper" style={{top: '0px', right: '0px'}}>
            <h1 className="car-selection" id="car-3"
              onMouseEnter={handleCarEnter} onMouseLeave={handleCarLeave} onMouseDown={handleCarSelection}>Car 3</h1>
            <h1 className="disabled-car-selection" id="disabled-car-3">Car 3</h1>
            <h2 className="car-player-name" id="car-3-player-name"
              onMouseEnter={handleCarEnter} onMouseLeave={handleCarLeave} onMouseDown={handleCarSelection}/>
          </div>

          <div className="car-wrapper" style={{bottom: '0px', right: '0px'}}>
            <h1 className="car-selection" id="car-4"
              onMouseEnter={handleCarEnter} onMouseLeave={handleCarLeave} onMouseDown={handleCarSelection}>Car 4</h1>
            <h1 className="disabled-car-selection" id="disabled-car-4">Car 4</h1>
            <h2 className="car-player-name" id="car-4-player-name"
              onMouseEnter={handleCarEnter} onMouseLeave={handleCarLeave} onMouseDown={handleCarSelection}/>
          </div>
        </div>
        <input
          type="text"
          placeholder="Enter Your Name"
          onChange={handleNameChange}
          className="text-input-field"
        />
        <Link to={'/Watching'} className="watch-button" id="watch-button">Watch</Link>
        <Link to={'/Playing'} className="play-button" id="play-button" onMouseDown={sendInitialMessage}>Play</Link>
        <h1 className="disabled-play-button" id="disabled-play-button">Select a Car and Enter Your Name to Play</h1>
      </div>
    </div>
  );
};

export default Home;
export { playerName, selectedCar, resetSelections };
