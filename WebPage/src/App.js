import React from "react";
import { BrowserRouter as Router, Switch, Route } from "react-router-dom";
// import { withAuthenticator, AmplifySignOut } from '@aws-amplify/ui-react'
import "./index.css";
import Home from "./Home/Home";
import ChatRoom from "./ChatRoom/ChatRoom";

function App() {
  return (
    <Router>
      <Switch>
        <Route exact path="/" component={Home} />
        <Route exact path="/:roomId" component={ChatRoom} />
        {/* <AmplifySignOut /> */}
      </Switch>
    </Router>
  );
}

export default App;
