"""
Speech-to-Text Transcriber — Streamlit web app.

Supports:
  • Video URL  (YouTube, Vimeo, etc. via yt-dlp)
  • Uploaded video file  (MP4, MKV, AVI, MOV, WEBM …)
  • Uploaded audio file  (MP3, WAV, M4A, OGG, FLAC …)

Transcription engine: OpenAI Whisper (local, no API key required).
"""

import os
import shutil
import tempfile

import streamlit as st
import whisper

from transcriber import (
    download_audio_from_url,
    extract_audio_from_video,
    remove_filler_words,
    segments_to_srt,
    transcribe,
)

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Speech Transcriber",
    page_icon="🎙",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Sidebar – settings
# ---------------------------------------------------------------------------

with st.sidebar:
    st.title("Settings")
    st.divider()

    MODEL_OPTIONS = {
        "tiny          (~75 MB  · fastest)":                    "tiny",
        "base          (~150 MB · fast, good for English)":     "base",
        "small         (~490 MB · balanced)":                   "small",
        "medium        (~1.5 GB · high accuracy)":              "medium",
        "large-v2      (~3 GB   · very high accuracy)":         "large-v2",
        "large-v3      (~3 GB   · best accuracy)":              "large-v3",
        "large-v3-turbo (~800 MB · fast + near-large accuracy ★)": "large-v3-turbo",
    }
    model_label = st.selectbox(
        "Whisper model",
        list(MODEL_OPTIONS.keys()),
        index=1,
        help="Models are downloaded once and cached locally. large-v3-turbo offers the best speed/accuracy balance.",
    )
    model_size = MODEL_OPTIONS[model_label]

    st.divider()
    remove_fillers = st.toggle(
        "Remove filler words",
        value=True,
        help="Strips sounds like 'uh', 'um', 'hmm', 'ah', 'er' from the output.",
    )
    show_srt = st.toggle(
        "Export SRT subtitles",
        value=False,
        help="Show timed subtitle output that you can save as a .srt file.",
    )


# ---------------------------------------------------------------------------
# Cached model loader (avoids reloading on every interaction)
# ---------------------------------------------------------------------------

@st.cache_resource(show_spinner="Loading Whisper model — this happens only once…")
def get_model(size: str):
    return whisper.load_model(size)


# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------

st.title("🎙 Speech-to-Text Transcriber")
st.caption(
    "Transcribe audio from a video URL, an uploaded video, or an uploaded audio file. "
    "Everything runs locally — no data leaves your machine."
)
st.divider()

# ---------------------------------------------------------------------------
# Input tabs
# ---------------------------------------------------------------------------

tab_url, tab_video, tab_audio = st.tabs(
    ["🔗  Video URL", "🎬  Upload Video", "🎵  Upload Audio"]
)

source_ready   = False
source_label   = ""
tmp_dir        = None
audio_path     = None

with tab_url:
    url_input = st.text_input(
        "Paste a video URL",
        placeholder="https://www.youtube.com/watch?v=…",
    )
    url_go = st.button("Transcribe", key="url_btn", type="primary")

    if url_go:
        if not url_input.strip():
            st.warning("Please enter a URL first.")
        else:
            source_ready = True
            source_label = "URL"

with tab_video:
    video_file = st.file_uploader(
        "Upload a video file",
        type=["mp4", "mkv", "avi", "mov", "webm", "flv", "ts"],
        key="video_upload",
    )
    video_go = st.button("Transcribe", key="video_btn", type="primary")

    if video_go:
        if not video_file:
            st.warning("Please upload a video file first.")
        else:
            source_ready = True
            source_label = "video"

with tab_audio:
    audio_file = st.file_uploader(
        "Upload an audio file",
        type=["mp3", "wav", "m4a", "ogg", "flac", "aac", "wma", "opus"],
        key="audio_upload",
    )
    audio_go = st.button("Transcribe", key="audio_btn", type="primary")

    if audio_go:
        if not audio_file:
            st.warning("Please upload an audio file first.")
        else:
            source_ready = True
            source_label = "audio"


# ---------------------------------------------------------------------------
# Processing pipeline
# ---------------------------------------------------------------------------

if source_ready:
    tmp_dir = tempfile.mkdtemp()
    error_occurred = False

    try:
        # --- Step 1: obtain audio file ---
        with st.status("Preparing audio…", expanded=True) as status:
            if source_label == "URL":
                st.write(f"Downloading audio from: `{url_input.strip()}`")
                audio_path = download_audio_from_url(url_input.strip(), tmp_dir)
                st.write("Download complete.")

            elif source_label == "video":
                video_path = os.path.join(tmp_dir, video_file.name)
                with open(video_path, "wb") as f:
                    f.write(video_file.read())
                st.write(f"Extracting audio from **{video_file.name}**…")
                audio_path = extract_audio_from_video(video_path, tmp_dir)
                st.write("Audio extracted.")

            else:  # audio file
                audio_path = os.path.join(tmp_dir, audio_file.name)
                with open(audio_path, "wb") as f:
                    f.write(audio_file.read())
                st.write(f"Audio file ready: **{audio_file.name}**")

            status.update(label="Audio ready.", state="complete")

        # --- Step 2: load model & transcribe ---
        model = get_model(model_size)

        with st.status(
            f"Transcribing with Whisper **{model_size}** model…", expanded=True
        ) as status:
            st.write("Running speech recognition — please wait…")
            result = transcribe(audio_path, model=model, language="en")
            status.update(label="Transcription complete!", state="complete")

        # --- Step 3: post-process ---
        raw_text     = result["text"].strip()
        cleaned_text = remove_filler_words(raw_text) if remove_fillers else raw_text
        segments     = result.get("segments", [])
        detected_lang = result.get("language", "unknown")

        # --- Step 4: display results ---
        st.divider()
        st.subheader("Transcription")

        if remove_fillers:
            col_raw, col_clean = st.columns(2)
            with col_raw:
                st.markdown("**Original** *(with filler words)*")
                st.text_area(
                    "raw", raw_text, height=320,
                    label_visibility="collapsed", key="raw_out"
                )
                st.download_button(
                    "⬇ Download original (.txt)",
                    data=raw_text,
                    file_name="transcription_original.txt",
                    mime="text/plain",
                )
            with col_clean:
                st.markdown("**Cleaned** *(filler words removed)*")
                st.text_area(
                    "clean", cleaned_text, height=320,
                    label_visibility="collapsed", key="clean_out"
                )
                st.download_button(
                    "⬇ Download cleaned (.txt)",
                    data=cleaned_text,
                    file_name="transcription_cleaned.txt",
                    mime="text/plain",
                )
        else:
            st.text_area(
                "out", raw_text, height=380,
                label_visibility="collapsed", key="main_out"
            )
            st.download_button(
                "⬇ Download transcription (.txt)",
                data=raw_text,
                file_name="transcription.txt",
                mime="text/plain",
            )

        # Language badge
        st.caption(f"Detected language: **{detected_lang}**")

        # --- Step 5: optional SRT export ---
        if show_srt and segments:
            st.divider()
            st.subheader("SRT Subtitles")
            srt_content = segments_to_srt(
                segments, apply_filler_removal=remove_fillers
            )
            st.text_area(
                "srt", srt_content, height=280,
                label_visibility="collapsed", key="srt_out"
            )
            st.download_button(
                "⬇ Download subtitles (.srt)",
                data=srt_content,
                file_name="subtitles.srt",
                mime="text/plain",
            )

    except Exception as exc:
        st.error(f"**Error:** {exc}")
        with st.expander("Troubleshooting tips"):
            st.markdown(
                """
- **ffmpeg not found** — Install from https://ffmpeg.org/download.html and add to PATH.
- **yt-dlp error** — The URL may be private, geo-blocked, or unsupported.
- **Out of memory** — Try a smaller Whisper model (e.g. `tiny` or `base`).
- **Slow transcription** — Expected for large files or the `medium`/`large` models.
                """
            )
    finally:
        # Always clean up temp files
        if tmp_dir and os.path.exists(tmp_dir):
            shutil.rmtree(tmp_dir, ignore_errors=True)

# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------
st.divider()
st.caption(
    "Powered by [OpenAI Whisper](https://github.com/openai/whisper) · "
    "[yt-dlp](https://github.com/yt-dlp/yt-dlp) · "
    "[Streamlit](https://streamlit.io)"
)
