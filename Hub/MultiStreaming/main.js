//Replace this variable with your token
const PUBLISH_TOKEN = "c07ecced5613412f39c72733959dc7fb1af58137fb1f66f3fbb0ceafb72cf10b";
const streamName = 'kgplc3ye'; //Replace with your stream name.
let url; //Websocket URL path.
let jwt; //Authenticated API token.
let iceServers; // STUN/TURN server paths to better guarantee our connection.

//Authenticate publisher and get connection point.
var XMLHttpRequest = require("xmlhttprequest").XMLHttpRequest;
var xhr = new XMLHttpRequest();
xhr.open("POST", "https://director.millicast.com/api/director/publish", true);
xhr.setRequestHeader("Authorization", `Bearer ${PUBLISH_TOKEN}`);
xhr.setRequestHeader("Content-Type", "application/json");
xhr.onreadystatechange = function() {
  console.log(this.readyState, XMLHttpRequest.DONE, this.status)
  if (this.readyState === 3 && this.status === 200) {
    let js = JSON.parse(xhr.responseText);
    console.log("success:",js);
    url = js.data.urls[0];
    jwt = js.data.jwt;
    connect();
  }
}
xhr.send(JSON.stringify({ streamName: streamName }));

//Create websocket for signaling.
function connect() {
  console.log(url + "?token=" + jwt)
  let ws = new WebSocket(url + "?token=" + jwt);
  ws.onopen = function(){
    console.log('ws::onopen');
    // Add RTCPeerConnection.createOffer to your stream name
  }
  ws.addEventListener('message', evt => {
    console.log('ws::message',evt);
  });
}

// const PUBLISH_TOKEN = "c07ecced5613412f39c72733959dc7fb1af58137fb1f66f3fbb0ceafb72cf10b";
// var XMLHttpRequest = require("xmlhttprequest").XMLHttpRequest;
// var xhr = new XMLHttpRequest();

// xhr.open("POST", "https://director.millicast.com/api/director/publish", true);
// xhr.setRequestHeader("Authorization", `Bearer ${PUBLISH_TOKEN}`);
// xhr.setRequestHeader("Content-Type", "application/json");

// xhr.onreadystatechange = function() { // Call a function when the state changes.
//   if (this.status === 200) {
//     var jsonData = JSON.parse(xhr.responseText);
//     console.log("Call Complete:",jsonData);
//   }
// }

// xhr.send(JSON.stringify({ streamName: "kgplc3ye" }));