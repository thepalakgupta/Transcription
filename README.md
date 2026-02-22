# Speech-to-Text Transcriber

A local, privacy-first web app that transcribes audio from YouTube/video URLs, uploaded video files, or uploaded audio files — with automatic filler word removal (`uh`, `um`, `hmm`, etc.).

No API keys. No cloud uploads. Everything runs on your machine.

---

## How It Works

```
Input (URL / Video / Audio)
        │
        ▼
┌───────────────────┐
│  Audio Extraction │  ← yt-dlp (URLs)  or  ffmpeg (video files)
└───────────────────┘
        │
        ▼
┌───────────────────┐
│  OpenAI Whisper   │  ← runs locally, no internet needed
│  (transcription)  │
└───────────────────┘
        │
        ▼
┌───────────────────┐
│  Filler Removal   │  ← regex cleans uh/um/hmm/ah/er
└───────────────────┘
        │
        ▼
  Output: .txt  /  .srt subtitles
```

---

## Project Structure

```
speech_transcriber/
├── app.py            ← Streamlit web UI (run this)
├── transcriber.py    ← Core logic (audio extraction, Whisper, filler removal)
├── requirements.txt  ← Python dependencies
└── README.md         ← This file
```

---

## Prerequisites

You need **two things** installed before the Python packages:

### 1. Python 3.9 or higher

Check if you have it:
```bash
python --version
```

If not, download from https://www.python.org/downloads/ — make sure to tick **"Add Python to PATH"** during install.

---

### 2. ffmpeg (pre-built binary — NOT source code)

ffmpeg handles audio extraction from videos and URL downloads. The easiest way on Windows:

**Option A — winget (recommended, one command):**
```bash
winget install ffmpeg
```
Then restart your terminal.

**Option B — manual:**
1. Go to https://www.gyan.dev/ffmpeg/builds/
2. Download `ffmpeg-release-essentials.zip`
3. Extract to somewhere permanent, e.g. `C:\ffmpeg\`
4. Add `C:\ffmpeg\bin` to your system PATH:
   - Press `Win + S` → search **"Edit the system environment variables"**
   - Click **Environment Variables**
   - Under **System variables**, select `Path` → **Edit** → **New**
   - Paste `C:\ffmpeg\bin`
   - Click OK on all dialogs
5. Restart your terminal

**Verify ffmpeg is working:**
```bash
ffmpeg -version
```
You should see version info, not an error.

---

## Installation (Step by Step)

Open a terminal (Command Prompt or PowerShell) and run these commands in order:

### Step 1 — Navigate to the project folder
```bash
cd C:\Users\dell\speech_transcriber
```

### Step 2 — (Optional but recommended) Create a virtual environment
This keeps the project's packages isolated from your system Python.
```bash
python -m venv venv
venv\Scripts\activate
```
Your terminal prompt will now show `(venv)` at the start.

> Skip this step if you don't want a virtual environment. The app will still work.

### Step 3 — Install Python dependencies
```bash
pip install -r requirements.txt
```

This installs:
| Package | What it does |
|---|---|
| `streamlit` | Web UI framework |
| `openai-whisper` | Local speech recognition model |
| `yt-dlp` | Downloads audio from YouTube and 1000+ sites |
| `torch` | PyTorch — required by Whisper (auto-installed) |

> **First-time install is large (~2–3 GB)** because PyTorch is included. This is a one-time download.

> **GPU acceleration (optional):** If you have an NVIDIA GPU, install PyTorch with CUDA support *before* the requirements to get much faster transcription:
> ```bash
> pip install torch --index-url https://download.pytorch.org/whl/cu121
> pip install -r requirements.txt
> ```

---

## Running the App

```bash
streamlit run app.py
```

Your browser will open automatically at **http://localhost:8501**

If it doesn't open automatically, copy that URL and paste it in your browser.

> If you used a virtual environment, make sure it is activated (`venv\Scripts\activate`) before running.

---

## Using the App

### Sidebar Settings (left panel)

| Setting | Description |
|---|---|
| **Whisper model** | Controls accuracy vs speed (see model guide below) |
| **Language** | Set to `Auto-detect` unless you know the language |
| **Remove filler words** | Strips `uh`, `um`, `hmm`, `ah`, `er` from output |
| **Export SRT subtitles** | Also generates a timed subtitle file |

### Three Input Modes (tabs at top)

**Tab 1 — Video URL**
- Paste any YouTube, Vimeo, or supported URL
- Click **Transcribe**
- yt-dlp downloads just the audio track (no full video download)

**Tab 2 — Upload Video**
- Drag and drop or browse for a video file
- Supported: MP4, MKV, AVI, MOV, WEBM, FLV, TS
- ffmpeg strips the audio track before transcription

**Tab 3 — Upload Audio**
- Drag and drop or browse for an audio file
- Supported: MP3, WAV, M4A, OGG, FLAC, AAC, WMA, OPUS

### Output

When transcription finishes, you get:
- **Two side-by-side panels** (when filler removal is on): original vs cleaned text
- **Download buttons** for `.txt` files
- **SRT panel** (if enabled in sidebar) with download button
- **Detected language** shown at the bottom

---

## Whisper Model Guide

Pick based on your hardware and how much accuracy you need:

| Model | Size | Speed | Accuracy | Best for |
|---|---|---|---|---|
| `tiny` | 75 MB | Very fast | Lower | Quick drafts, testing |
| `base` | 150 MB | Fast | Good | English content, everyday use |
| `small` | 490 MB | Moderate | Better | Non-English, mixed audio |
| `medium` | 1.5 GB | Slow | High | Important transcriptions |
| `large` | 3 GB | Very slow | Best | Maximum accuracy needed |

> Models are downloaded from the internet the **first time** you select them, then cached locally at `C:\Users\<you>\.cache\whisper\`. Subsequent uses are instant.

**Recommendation for most users:** Start with `base`. If accuracy isn't good enough, try `small`.

---

## Troubleshooting

**"ffmpeg is not found in your PATH"**
- Run `ffmpeg -version` in a new terminal
- If it says "not recognized", ffmpeg is not in PATH — re-do the ffmpeg install steps above and restart your terminal (or your PC)

**"yt-dlp error" on a YouTube URL**
- The video may be age-restricted, private, or geo-blocked
- Try a different video to confirm the setup works
- Update yt-dlp: `pip install -U yt-dlp`

**App is very slow during transcription**
- This is normal for the `medium` or `large` models on CPU
- Switch to `base` or `tiny` for faster results
- A GPU dramatically speeds this up (see GPU install note above)

**"Out of memory" / app crashes**
- Use a smaller model (`tiny` or `base`)
- Close other heavy applications while transcribing

**Virtual environment not activating**
- Make sure you ran `python -m venv venv` inside the `speech_transcriber` folder
- Use `venv\Scripts\activate` (Windows), not `source venv/bin/activate` (that's Linux/Mac)

**Port 8501 already in use**
```bash
streamlit run app.py --server.port 8502
```

---

## Stopping the App

Press `Ctrl + C` in the terminal where `streamlit run` is running.

---

## Quick-Start Cheat Sheet

```bash
# 1. Navigate to project
cd C:\Users\dell\speech_transcriber

# 2. Activate virtual environment (if you created one)
venv\Scripts\activate

# 3. Run the app
streamlit run app.py

# 4. Open browser at http://localhost:8501
```

---

## Tech Stack

- [OpenAI Whisper](https://github.com/openai/whisper) — speech recognition
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) — video/audio URL downloading
- [ffmpeg](https://ffmpeg.org/) — audio extraction from video files
- [Streamlit](https://streamlit.io) — web UI framework
