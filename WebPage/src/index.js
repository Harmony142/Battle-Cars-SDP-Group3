import React from "react";
import ReactDOM from "react-dom";
import App from "./App";
import Amplify from 'aws-amplify';
// import config from './aws-exports'
import awsmobile from './aws-exports';
import * as serviceWorker from "./serviceWorker";
Amplify.configure(awsmobile);
// temp
ReactDOM.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
  document.getElementById("root")
);

// If you want your app to work offline and load faster, you can change
// unregister() to register() below. Note this comes with some pitfalls.
// Learn more about service workers: https://bit.ly/CRA-PWA
serviceWorker.unregister();