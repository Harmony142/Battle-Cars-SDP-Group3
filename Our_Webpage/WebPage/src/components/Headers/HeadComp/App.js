import React, { Component } from 'react';
 
class App extends Component {  
  constructor(props){
    super(props);
    this.state = {
      content: 'Use arrow keys on your keyboard!'
    };
  }
  render() {
    return (
      <div>Hello</div>
    );
  }
}
 
export default App;