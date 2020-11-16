import React from "react";

import "./ChatRoom.css";
import useChat from "../useChat";

const ChatRoom = (props) => {
  const { roomId } = props.match.params;
  const { messages, sendMessage } = useChat(roomId);
  const [newMessage, setNewMessage] = React.useState("");
  
  const keysPressed = {'w':false, 'a':false, 's':false, 'd':false};
  document.addEventListener('keydown', e => keysPressed[e.key] = true)
  document.addEventListener('keyup', e => keysPressed[e.key] = false)

  const handleKeyPress = (event) => {
    sendMessage(JSON.stringify(keysPressed));
    setNewMessage("");
  }

  const handleNewMessageChange = (event) => {
    //setNewMessage(event.target.value);
  };

  return (
    <>
    <body
        className="page-header"
        style={{
          backgroundImage:
            "url(" + require("./space.jpg") + ")",
        }}
      >
    <div onKeyPress={handleKeyPress}>
      <h1 className="room-name">Name: {roomId}</h1>
      <textarea
        value={newMessage}
        onChange={handleNewMessageChange}
        className="new-message-input-field"
      />
    </div>
    </body>
    </>
  );
};

export default ChatRoom;
