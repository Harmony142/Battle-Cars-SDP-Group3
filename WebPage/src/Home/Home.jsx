import React from "react";
import { Link } from "react-router-dom";

import "./Home.css";

const Home = () => {
  const [roomName, setRoomName] = React.useState("");

  const handleRoomNameChange = (event) => {
    setRoomName(event.target.value);
  };

  return (
    <div className="home-window">
      <div className="red-half"/>
      <div className="blue-half"/>
      <div className="input-wrapper">
          <input
            type="text"
            placeholder="Name"
            value={roomName}
            onChange={handleRoomNameChange}
            className="text-input-field"
          />
          <Link to={`/${roomName}`} className="enter-room-button">
            Join
          </Link>
      </div>
    </div>
  );
};

export default Home;
