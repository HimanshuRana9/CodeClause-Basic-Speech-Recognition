Backend (production-ready)
-------------------------
- Endpoint: POST /transcribe (multipart/form 'file') -> returns JSON { text: '...' }
- If uploaded file > 20 MB it will be split into 60s segments using ffmpeg and each segment will be transcribed and concatenated.
- Set OPENAI_API_KEY in Render environment for the backend service.
- Dockerfile installs ffmpeg and uses gunicorn.
