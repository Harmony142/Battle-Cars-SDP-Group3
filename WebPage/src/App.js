import React from "react";
import { BrowserRouter as Router, Switch, Route } from "react-router-dom";
import "./index.css";
import Home from "./Home/Home";
import PlayingWindow from "./Windows/PlayingWindow";
import WatchingWindow from "./Windows/WatchingWindow";

var scoreRed = 0;
var scoreBlue = 0;

var timer = 0;

var car1PlayerName = '';
var car2PlayerName = '';
var car3PlayerName = '';
var car4PlayerName = '';

const AWS = require('aws-sdk');
const dynamoDB = new AWS.DynamoDB({
    accessKeyId: 'AKIAY563PRYUZGQH44NH',
    secretAccessKey: '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',
    region: 'us-east-2'
});

document.interval = setInterval(() => {
  var params = {
    ConsistentRead: true,
    TableName: 'BattleCarsScore',
    Key: {
      "id": {
        "N": "1"
      }
    }
  }

  var response = dynamoDB.getItem(params, function(err, data) {
    if (err) {
      console.log("DynamoDB Read Error", err);
    } else {
      // console.log("DynamoDB Read Success");
      try {
        var item = response.response.data.Item;

        // Update the score
        try {
          scoreRed = item.score_red.N;
          scoreBlue = item.score_blue.N;
        } catch(err) {
          console.log("could not update score");
        }

        // Update the timer
        try {
          timer = item.time_left.S;
        } catch(err) {
          console.log("could not update time left");
        }

        // Update who is driving what car
        try {
          for(var i = 1; i <=4; i++) {
            window['car' + i + 'PlayerName'] = item['car_' + i].S;
          }
        } catch(err) {
          console.log("could not update player names");
        }
      } catch(err) {
        console.log("could not retrieve item from response");
      }
    }
  });
}, 1000);

function App() {
  return (
    <Router>
      <Switch>
        <Route exact path="/" component={Home} />
        <Route exact path="/Playing" component={PlayingWindow} />
        <Route exact path="/Watching" component={WatchingWindow} />
      </Switch>
    </Router>
  );
}

export default App;
export { scoreRed, scoreBlue, timer, car1PlayerName, car2PlayerName, car3PlayerName, car4PlayerName };
