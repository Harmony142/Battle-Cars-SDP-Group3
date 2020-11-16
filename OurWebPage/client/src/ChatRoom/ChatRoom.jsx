import React from "react";
import "./ChatRoom.css";
import useChat from "../useChat";
import Space from './space.jpg'

const prev_keysPressed = {'w':false, 'a':false, 's':false, 'd':false};
const curr_keysPressed = {'w':false, 'a':false, 's':false, 'd':false};

const ChatRoom = (props) => {
  const { roomId } = props.match.params;
  const { messages, sendMessage } = useChat(roomId);
  const [newMessage, setNewMessage] = React.useState("");
  
  // const keysPressed = {'w':false, 'a':false, 's':false, 'd':false};
  document.addEventListener('keydown', e => curr_keysPressed[e.key] = true)
  document.addEventListener('keyup', e => curr_keysPressed[e.key] = false)

  document.body.style.overflow = "hidden"

  const handleKeyPress = (event) => {
    if(JSON.stringify(prev_keysPressed) !== JSON.stringify(curr_keysPressed)){
      sendMessage(JSON.stringify(curr_keysPressed));
      setNewMessage("");
      prev_keysPressed['w'] = curr_keysPressed['w'];
      prev_keysPressed['a'] = curr_keysPressed['a'];
      prev_keysPressed['s'] = curr_keysPressed['s'];
      prev_keysPressed['d'] = curr_keysPressed['d'];
    }
  }

  const handleNewMessageChange = (event) => {
    //setNewMessage(event.target.value);
  };


  return (
    <div  onKeyUp={handleKeyPress} onKeyDown={handleKeyPress}>
      <img className="room-page" src={Space}/>
      <iframe src="https://viewer.millicast.com/v2?streamId=hrFywT/kgplc3ye" allowFullScreen className="room-video"></iframe>
      <h1 className="room-name">Name: {roomId}</h1>
      <textarea
        value={newMessage}
        onChange={handleNewMessageChange}
        className="new-message-input-field"
      />
    </div>
  );
};

export default ChatRoom;
