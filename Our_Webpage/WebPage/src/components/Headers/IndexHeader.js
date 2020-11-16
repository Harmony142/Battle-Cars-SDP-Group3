
import React from "react";

import App from "components/Headers/HeadComp/App.js"
// core components
const Boom = {
  color: "white",
  fontSize:"450%", 
  marginTop:"20px",
  // height: "100vh", /* Magic here */
  display: "flex",
  justifyContent: "center",
  //alignItems: "center", // cene
};
const video={
  display: "flex",
  alignItems: "center",
};

const handleKeyPress = (event) => {
  console.log("Hello")
  // sendMessage(JSON.stringify(keysPressed));
  // setNewMessage("");
}


function IndexHeader() {
  return (
    <>
    <body
        className="page-header"
        style={{
          backgroundImage:
            "url(" + require("assets/img/space.jpg") + ")",
        }}
        onKeyPress={handleKeyPress}
      >
        <div vertical="true" layout>
        <App />
        <script>alert(1)</script>
        <div>
          <b style={Boom}>Boom Boom Cars</b>
        </div>
        <div style={video}><iframe src="https://viewer.millicast.com/v2?streamId=hrFywT/kgplc3ye" allowFullScreen align="middle" width="640" height="480"></iframe></div>
        </div>
        <div
          className="moving-clouds"
          style={{
            backgroundImage: "url(" + require("assets/img/clouds.png") + ")",
          }}
        />
        <h6 className="category category-absolute">
          Designed and coded by yours truly
        </h6>
      </body>
    </>
  );
}

export default IndexHeader;
