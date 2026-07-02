import os
from faster_whisper import WhisperModel
from pyannote.audio import Pipeline
from pyannote.audio import Pipeline
from dotenv import load_dotenv
from pydub import AudioSegment
# import traceback
# import logging

load_dotenv()

token = os.getenv("HF_TOKEN")

# Load Whisper model
whisper_model = WhisperModel(
    "base",
    device="cpu",
    compute_type="int8"
)

# Load diarization model
pipeline = Pipeline.from_pretrained(
    "pyannote/speaker-diarization-3.1",
    token=token
)

def process_audio(file_path):
    # Step 1: Full audio transcription
    segments, _ = whisper_model.transcribe(
        file_path,
        beam_size=5,
        word_timestamps=True,
        vad_filter=True
    )

    transcript = []
    for seg in segments:
        transcript.append({
            "start": seg.start,
            "end": seg.end,
            "text": seg.text.strip()
        })

    # Step 2: Speaker diarization only
    diarize_output = pipeline(file_path)
    diarization = diarize_output.speaker_diarization

    final_output = []

    for turn, _, speaker in diarization.itertracks(yield_label=True):
        duration = turn.end - turn.start
        if duration < 1.0:
            continue

        # Match transcript segments with speaker time range
        speaker_text = []

        for seg in transcript:
            if seg["start"] >= turn.start and seg["end"] <= turn.end:
                speaker_text.append(seg["text"])

        text = " ".join(speaker_text)

        if text:
            final_output.append({
                "speaker": speaker,
                "text": text
            })

    return final_output