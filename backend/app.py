import os
import tempfile
import subprocess
import uuid
import shutil
from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI
import logging
import time

app = Flask(__name__)
CORS(app)
logging.basicConfig(level=logging.INFO)

OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
if not OPENAI_API_KEY:
    app.logger.warning("OPENAI_API_KEY not set. Transcription will fail until set in environment.")

client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

# Config
MAX_SINGLE_FILE_MB = 20  # if file larger than this, split into segments (MB)
SEGMENT_SECONDS = 60     # length of each segment when splitting long audio (seconds)
TRANSCRIBE_MODEL = "whisper-1"

def filesize_mb(path):
    return os.path.getsize(path) / (1024*1024)

def split_audio(input_path, out_dir, segment_seconds=60):
    """Use ffmpeg to split input audio into segments of segment_seconds.
    Output files will be placed into out_dir as segment-000.webm (or mp3 depending on input)."""
    os.makedirs(out_dir, exist_ok=True)
    # Generate segment pattern
    out_pattern = os.path.join(out_dir, "segment-%03d.webm")
    # ffmpeg command: re-encode to webm and segment
    cmd = [
        "ffmpeg", "-y", "-i", input_path,
        "-c", "libvorbis",
        "-f", "segment",
        "-segment_time", str(segment_seconds),
        "-segment_format", "webm",
        out_pattern
    ]
    app.logger.info("Running ffmpeg split: %s", " ".join(cmd))
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        app.logger.error("ffmpeg failed: %s", proc.stderr)
        raise RuntimeError(f"ffmpeg failed: {proc.stderr}")
    # collect created files
    files = sorted([os.path.join(out_dir, f) for f in os.listdir(out_dir) if f.startswith('segment-')])
    return files

def transcribe_file(path, retries=2, backoff=2):
    """Send a single file to OpenAI Whisper via the OpenAI Python client.
       Returns transcript text.
    """
    if client is None:
        raise RuntimeError("OPENAI_API_KEY not configured on server.")
    last_exc = None
    for attempt in range(retries+1):
        try:
            with open(path, "rb") as audio_file:
                resp = client.audio.transcriptions.create(
                    model=TRANSCRIBE_MODEL,
                    file=audio_file
                )
            # response may be dict-like
            text = resp.get('text') if isinstance(resp, dict) else getattr(resp, 'text', None)
            return text or ''
        except Exception as e:
            last_exc = e
            app.logger.warning("Transcription attempt %s failed: %s", attempt+1, str(e))
            time.sleep(backoff * (attempt+1))
    raise last_exc

@app.route('/')
def index():
    return jsonify({"status":"ok","message":"Speech backend (Whisper API)"}), 200

@app.route('/health')
def health():
    return "healthy", 200

@app.route('/transcribe', methods=['POST'])
def transcribe():
    if 'file' not in request.files:
        return jsonify({"error":"no file part"}), 400
    f = request.files['file']
    if f.filename == '':
        return jsonify({"error":"empty filename"}), 400

    tmpdir = tempfile.mkdtemp(prefix='upload-')
    filename = f.filename
    save_path = os.path.join(tmpdir, filename)
    f.save(save_path)
    app.logger.info(f"Saved uploaded file to {save_path} (size={filesize_mb(save_path):.2f} MB)")

    try:
        # If file is large, split into segments
        if filesize_mb(save_path) > MAX_SINGLE_FILE_MB:
            app.logger.info("File exceeds %s MB — splitting into %s second segments", MAX_SINGLE_FILE_MB, SEGMENT_SECONDS)
            segdir = os.path.join(tmpdir, "segments")
            segment_files = split_audio(save_path, segdir, SEGMENT_SECONDS)
            if not segment_files:
                raise RuntimeError("No segments produced by ffmpeg")
            transcripts = []
            for seg in segment_files:
                try:
                    t = transcribe_file(seg)
                    transcripts.append(t)
                except Exception as e:
                    app.logger.exception("Failed to transcribe segment %s", seg)
                    transcripts.append("[transcription failed for a segment]")
            full_text = "\n".join(transcripts)
            return jsonify({"text": full_text}), 200
        else:
            # Single file transcription
            text = transcribe_file(save_path)
            return jsonify({"text": text}), 200
    except Exception as e:
        app.logger.exception("Transcription pipeline failed")
        return jsonify({"error": str(e)}), 500
    finally:
        try:
            shutil.rmtree(tmpdir)
        except Exception:
            pass

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
