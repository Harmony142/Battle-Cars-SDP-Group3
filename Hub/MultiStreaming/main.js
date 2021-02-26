const PUBLISH_TOKEN = "c07ecced5613412f39c72733959dc7fb1af58137fb1f66f3fbb0ceafb72cf10b";
var XMLHttpRequest = require("xmlhttprequest").XMLHttpRequest;
var xhr = new XMLHttpRequest();

xhr.open("POST", "https://director.millicast.com/api/director/publish", true);
xhr.setRequestHeader("Authorization", `Bearer ${PUBLISH_TOKEN}`);
xhr.setRequestHeader("Content-Type", "application/json");

xhr.onreadystatechange = function() { // Call a function when the state changes.
  if (this.status === 200) {
    var jsonData = JSON.parse(xhr.responseText);
    console.log("Call Complete:",jsonData);
  }
}

xhr.send(JSON.stringify({ streamName: "kgplc3ye" }));