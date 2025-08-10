import React from 'react';
import LiveRecorder from './components/LiveRecorder';

export default function App(){
  return (
    <div style={{fontFamily:'Arial, sans-serif', padding:20}}>
      <h2>Speech Recorder + Whisper API (Demo)</h2>
      <LiveRecorder />
    </div>
  );
}
