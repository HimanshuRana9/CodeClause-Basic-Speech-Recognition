import React, {useRef, useState, useEffect} from 'react';

// API URL taken from environment variable at build time, or fallback to same origin
const BACKEND = process.env.REACT_APP_API_URL || '';

export default function LiveRecorder(){
  const mediaRecorderRef = useRef(null);
  const [recording, setRecording] = useState(false);
  const [status, setStatus] = useState('idle');
  const [transcript, setTranscript] = useState('');
  const [chunks, setChunks] = useState([]);
  const [progress, setProgress] = useState(null);

  const start = async ()=>{
    setStatus('requesting-media');
    const stream = await navigator.mediaDevices.getUserMedia({audio:true});
    mediaRecorderRef.current = new MediaRecorder(stream, {mimeType:'audio/webm'});
    mediaRecorderRef.current.ondataavailable = (e)=>{
      if (e.data && e.data.size > 0){
        setChunks(prev => prev.concat(e.data));
      }
    };
    mediaRecorderRef.current.start(1000);
    setRecording(true);
    setStatus('recording');
  };

  const stop = async ()=>{
    if (!mediaRecorderRef.current) return;
    mediaRecorderRef.current.stop();
    setRecording(false);
    setStatus('processing');

    const blob = new Blob(chunks, {type: 'audio/webm'});
    const fd = new FormData();
    fd.append('file', blob, 'recording.webm');

    const url = BACKEND || window.location.origin;
    try {
      setProgress('uploading');
      const resp = await fetch(url + '/transcribe', { method: 'POST', body: fd });
      setProgress('processing');
      const data = await resp.json();
      if (resp.ok) {
        setTranscript(data.text || '');
        setStatus('done');
      } else {
        setTranscript('Error: ' + (data.error || resp.statusText));
        setStatus('error');
      }
    } catch (e) {
      setTranscript('Upload failed: ' + e.message);
      setStatus('error');
    } finally {
      setChunks([]);
      setProgress(null);
    }
  };

  return (
    <div>
      <div style={{marginBottom:10}}>
        <button onClick={start} disabled={recording}>Start</button>
        <button onClick={stop} disabled={!recording}>Stop & Transcribe</button>
      </div>
      <div><strong>Status:</strong> {status} {progress ? `(${progress})` : ''}</div>
      <div style={{marginTop:10}}><strong>Transcript:</strong> <pre style={{whiteSpace:'pre-wrap'}}>{transcript}</pre></div>
    </div>
  );
}
