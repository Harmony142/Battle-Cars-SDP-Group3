import React, { useEffect } from "react";
import { Link } from "react-router-dom";
import { car1PlayerName, car2PlayerName, car3PlayerName, car4PlayerName } from '../App.js';

import "./Home.css";

var playerName = '';
var selectedCar = null;

// TODO lock cars that already have players with cursor indicator

const Home = () => {
  useEffect(() => {
    const interval = setInterval(() => {
      // Update who is driving what car
      try {
        for(var i = 1; i <=4; i++) {
          const carName = window['car' + i + 'PlayerName'];
          const element = document.getElementById('car-' + i + '-player-name');
          if(carName !== '') {
            element.innerHTML = 'Current Player: ' + (carName.length > 10 ? carName.slice(0, 10) + '...' : carName);
          }
          else {
            element.style.visibility = 'hidden';
          }
        }
      } catch(err) {
        console.log("could not update player names", err);
      }
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  const handleCarEnter = (event) => {
    // Highlight button
    event.target.style.borderStyle = 'inset';
  };

  const updatePlayButton = () => {
    const playButtonStyle = document.getElementById('play-button').style;
    const disabledPlayButtonStyle = document.getElementById('disabled-play-button').style;

    if(selectedCar !== null && playerName !== '')
    {
        playButtonStyle.visibility = 'visible';
        disabledPlayButtonStyle.visibility = 'hidden';
    } else {
        playButtonStyle.visibility = 'hidden';
        disabledPlayButtonStyle.visibility = 'visible';
    }
  };

  const handleCarLeave = (event) => {
    // Remove button highlight
    if(event.target.id !== selectedCar) {
      event.target.style.borderStyle = 'outset';
    }
  };

  const handleCarSelection = (event) => {
    // Set this button pressed down
    console.log('Selected Car ' + event.target.id);
    selectedCar = event.target.id;
    const selectedCarStyle = event.target.style;
    selectedCarStyle.borderStyle = 'inset';
    selectedCarStyle.backgroundColor = 'darkgrey';

    // Set all other buttons not pressed
    for(var i = 1; i <= 4; i++) {
      const car_id = 'car-' + i;
      if(car_id !== event.target.id) {
        const carSelectStyle = document.getElementById(car_id).style;
        carSelectStyle.borderStyle = 'outset';
        carSelectStyle.backgroundColor = 'lightgrey';
      }
    }

    updatePlayButton();
  };

  const handleNameChange = (event) => {
    playerName = event.target.value;
    updatePlayButton();
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
            <h2 className="car-player-name" id="car-1-player-name"/>
          </div>

          <div className="car-wrapper" style={{bottom: '0px', left: '0px'}}>
            <h1 className="car-selection" id="car-2"
              onMouseEnter={handleCarEnter} onMouseLeave={handleCarLeave} onMouseDown={handleCarSelection}>Car 2</h1>
            <h2 className="car-player-name" id="car-2-player-name"/>
          </div>

          <div className="car-wrapper" style={{top: '0px', right: '0px'}}>
            <h1 className="car-selection" id="car-3"
              onMouseEnter={handleCarEnter} onMouseLeave={handleCarLeave} onMouseDown={handleCarSelection}>Car 3</h1>
            <h2 className="car-player-name" id="car-3-player-name"/>
          </div>

          <div className="car-wrapper" style={{bottom: '0px', right: '0px'}}>
            <h1 className="car-selection" id="car-4"
              onMouseEnter={handleCarEnter} onMouseLeave={handleCarLeave} onMouseDown={handleCarSelection}>Car 4</h1>
            <h2 className="car-player-name" id="car-4-player-name"/>
          </div>
        </div>
        <input
          type="text"
          placeholder="Enter Your Name"
          onChange={handleNameChange}
          className="text-input-field"
        />
        <Link to={'/Watching'} className="watch-button" id="watch-button">Watch</Link>
        <Link to={'/Playing'} className="play-button" id="play-button">Play</Link>
        <h1 className="disabled-play-button" id="disabled-play-button">Select a Car and Enter Your Name to Play</h1>
      </div>
    </div>
  );
};

export default Home;
export { playerName, selectedCar };
