import React from "react";
import "./ChatRoom.css";
import Space from './space.jpg';
// import { API } from 'aws-amplify';
import { createTodo, updateTodo } from '../graphql/mutations';
import CustomizationMenu from './Customization.jsx'

// updateTodo
const prev_keysPressed = {'KeyW':false, 'KeyA':false, 'KeyS':false, 'KeyD':false, 'ShiftLeft':false};
const curr_keysPressed = {'KeyW':false, 'KeyA':false, 'KeyS':false, 'KeyD':false, 'ShiftLeft':false};
const formData = {id: 1234, name: "hello", description: ""}

const allowed_keys = Object.keys(curr_keysPressed);
// console.log(JSON.stringify(allowed_keys));

document.addEventListener('keydown', e => {if(allowed_keys.includes(e.code)){curr_keysPressed[e.code] = true;}});
document.addEventListener('keyup', e => {if(allowed_keys.includes(e.code)){curr_keysPressed[e.code] = false;}});

document.body.style.overflow = "hidden";

const ChatRoom = (props) => {
  const [newMessage, setNewMessage] = React.useState("");

  const handleKeyPress = (event) => {
    if(JSON.stringify(prev_keysPressed) !== JSON.stringify(curr_keysPressed)){
      createNote();
      allowed_keys.forEach(key => prev_keysPressed[key] = curr_keysPressed[key]);
    }
  }

  async function createNote() {
    const payload = JSON.parse(JSON.stringify(curr_keysPressed));
    var d = new Date();
    payload['StartTime'] = d.getTime();
    formData.description = JSON.stringify(payload);
    console.log(formData);
    API.graphql({ query: createTodo, variables: { input: formData } })
        .catch(e => {API.graphql({ query: updateTodo, variables: { input: formData } });});
  }

  const handleNewMessageChange = (event) => {
  };


  return (
    <div  onKeyUp={handleKeyPress} onKeyDown={handleKeyPress}>
      <img className="room-page" src={Space} alt=''/>
      <iframe src="https://viewer.millicast.com/v2?streamId=hrFywT/kgplc3ye" allowFullScreen className="room-video"></iframe>
      {/* <h1 className="room-name">Name: {roomId}</h1> */}
      <textarea
        value={newMessage}
        onChange={handleNewMessageChange}
        className="new-message-input-field"
      />
      <CustomizationMenu/>
    </div>
  );
};

export default ChatRoom;
