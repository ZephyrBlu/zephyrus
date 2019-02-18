import { Component } from 'react';

export default class Replays extends Component {
  state = {
    currentPage: 'replays',
  };

  render() {
    return (
      <p>{this.state.currentPage} Page</p>
    );
  }
}
