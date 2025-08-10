Final deploy-ready repo (best approach)
--------------------------------------
This repository is prepared to be deployed as two separate Render services: backend and frontend.

Backend (recommended settings):
  - Dockerfile Path: backend/Dockerfile
  - Root Directory: leave blank in Render
  - Env vars: OPENAI_API_KEY (required)
  - Endpoint: POST /transcribe (multipart/form-data 'file')
  - For large uploads (>20MB), the backend splits audio into ~60s segments and transcribes each, concatenating results.

Frontend (recommended settings):
  - Dockerfile Path: frontend/Dockerfile
  - Optionally set REACT_APP_API_URL at build time to point to your backend URL.

Local testing:
  docker-compose up --build

Notes & next steps:
 - Monitor Render logs for ffmpeg output and OpenAI errors.
 - Consider adding authentication, rate limiting, and usage monitoring for production.
 - For real-time streaming transcription, a WebSocket-based approach is needed (more complex).
