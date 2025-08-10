Frontend README
----------------
- The frontend builds a React app that records audio and uploads to /transcribe.
- Configure backend URL at build time using REACT_APP_API_URL, e.g:
  REACT_APP_API_URL=https://speech-backend.onrender.com npm run build
- If REACT_APP_API_URL is not set, the frontend will use same-origin URL at runtime.
