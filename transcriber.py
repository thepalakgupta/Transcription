"""
Core transcription logic for Speech-to-Text Transcriber.
Handles: URL audio download, video audio extraction, Whisper transcription, filler word removal.
"""

import os
import re
import subprocess
import shutil
from pathlib import Path
from typing import Optional


# ---------------------------------------------------------------------------
# Filler word removal
# ---------------------------------------------------------------------------

# Matches common hesitation sounds:
#   uh, uhh, uhhh  /  um, umm  /  hm, hmm  /  mhm  /  ah, ahh  /  er, err
# Must be a standalone "word" (not part of another word).
_FILLER_RE = re.compile(
    r'(?<![a-zA-Z])(?:[Uu]h+|[Uu]m+|[Hh]m+|[Mm]hm+|[Aa]h+|[Ee]r+)(?![a-zA-Z])[,]?\s*',
)


def remove_filler_words(text: str) -> str:
    """Remove hesitation sounds / filler words from transcription text."""
    cleaned = _FILLER_RE.sub(' ', text)
    # Collapse multiple spaces
    cleaned = re.sub(r'\s{2,}', ' ', cleaned)
    # Remove space before punctuation
    cleaned = re.sub(r'\s+([.,!?;:])', r'\1', cleaned)
    # Remove repeated punctuation (e.g. ",," → ",")
    cleaned = re.sub(r'([.,!?;:]){2,}', r'\1', cleaned)
    return cleaned.strip()


# ---------------------------------------------------------------------------
# Audio acquisition
# ---------------------------------------------------------------------------

def download_audio_from_url(url: str, output_dir: str) -> str:
    """
    Download audio from a URL (YouTube, Vimeo, etc.) using yt-dlp.
    Returns the path to the downloaded audio file (WAV).
    """
    import yt_dlp  # imported lazily so the module loads even if not installed

    output_template = os.path.join(output_dir, 'audio.%(ext)s')
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'wav',
        }],
        'outtmpl': output_template,
        'quiet': True,
        'no_warnings': True,
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    # Locate the output file
    for candidate in Path(output_dir).iterdir():
        if candidate.stem == 'audio' and candidate.suffix in ('.wav', '.mp3', '.m4a', '.webm', '.ogg'):
            return str(candidate)

    raise FileNotFoundError(
        "yt-dlp finished but no audio file was found. "
        "Make sure ffmpeg is installed and in your PATH."
    )


def extract_audio_from_video(video_path: str, output_dir: str) -> str:
    """
    Extract the audio track from a video file using ffmpeg.
    Returns the path to a 16 kHz mono WAV file (optimal for Whisper).
    """
    if not shutil.which('ffmpeg'):
        raise EnvironmentError(
            "ffmpeg is not found in your PATH. "
            "Install it from https://ffmpeg.org/download.html and add it to PATH."
        )

    output_path = os.path.join(output_dir, 'audio.wav')
    cmd = [
        'ffmpeg',
        '-i', video_path,
        '-vn',              # drop video stream
        '-acodec', 'pcm_s16le',
        '-ar', '16000',     # 16 kHz – Whisper's native sample rate
        '-ac', '1',         # mono
        '-y',               # overwrite without asking
        output_path,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"ffmpeg failed to extract audio:\n{result.stderr[-1500:]}"
        )
    return output_path


# ---------------------------------------------------------------------------
# Transcription
# ---------------------------------------------------------------------------

def transcribe(
    audio_path: str,
    model,                       # pre-loaded whisper model
    language: Optional[str] = None,
) -> dict:
    """
    Transcribe an audio file with a pre-loaded Whisper model.

    Returns a dict with keys:
      - 'text'     : full transcription string
      - 'segments' : list of segment dicts (each has 'start', 'end', 'text')
      - 'language' : detected/forced language code
    """
    decode_options: dict = {'task': 'transcribe', 'verbose': False}
    if language:
        decode_options['language'] = language

    return model.transcribe(audio_path, **decode_options)


# ---------------------------------------------------------------------------
# SRT export
# ---------------------------------------------------------------------------

def segments_to_srt(segments: list, apply_filler_removal: bool = False) -> str:
    """Convert Whisper segment list to SRT subtitle format."""
    lines = []
    index = 1
    for seg in segments:
        text = seg['text'].strip()
        if apply_filler_removal:
            text = remove_filler_words(text)
        if not text:
            continue
        start = _srt_timestamp(seg['start'])
        end = _srt_timestamp(seg['end'])
        lines.append(f"{index}\n{start} --> {end}\n{text}\n")
        index += 1
    return "\n".join(lines)


def _srt_timestamp(seconds: float) -> str:
    """Format a float number of seconds as HH:MM:SS,mmm."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int(round((seconds - int(seconds)) * 1000))
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
