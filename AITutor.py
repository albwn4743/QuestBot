import sounddevice as sd
import numpy as np
import queue
import tempfile
import torch
from silero_vad import get_speech_timestamps, load_silero_vad
import scipy.io.wavfile as wav
from faster_whisper import WhisperModel

# ---------------- SETTINGS ----------------
samplerate = 16000
channels = 1
chunk_duration = 4   # better than 5 (faster response)

# ------------------------------------------

# Load models
vad = load_silero_vad()

model = WhisperModel(
    "medium",
    device="cuda",        # change to "cpu" if needed
    compute_type="int8"
)

q = queue.Queue()



# ---------------- AUDIO ----------------
def audio_callback(indata, frames, time, status):
    q.put(indata.copy())

def normalize_audio(audio):
    max_val = np.max(np.abs(audio))
    if max_val > 0:
        audio = audio / max_val
    return audio

def to_mono(audio):
    if len(audio.shape) > 1:
        return np.mean(audio, axis=1)
    return audio

# ---------------- VAD ----------------
def apply_vad(audio):
    audio_tensor = torch.from_numpy(audio).float()
    timestamps = get_speech_timestamps(audio_tensor, vad, sampling_rate=16000)

    speech_audio = []
    for ts in timestamps:
        speech_audio.append(audio[ts['start']:ts['end']])

    if len(speech_audio) == 0:
        return None

    return np.concatenate(speech_audio)



# ---------------- MAIN LOOP ----------------
with sd.InputStream(samplerate=samplerate, channels=channels, callback=audio_callback):
    print("🎤 Speak in English (Ctrl + C to stop)")

    buffer = []

    while True:
        data = q.get()
        buffer.append(data)

        # Collect chunk
        if len(buffer) * len(data) >= samplerate * chunk_duration:

            audio_data = np.concatenate(buffer, axis=0)
            buffer = []   # ✅ IMPORTANT reset

            # Convert to mono
            audio_data = to_mono(audio_data)

            # Normalize
            audio_data = normalize_audio(audio_data)

            # Apply VAD
            speech_audio = apply_vad(audio_data)
            if speech_audio is None:
                continue

            # Save temp file
            with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
                wav.write(f.name, samplerate, speech_audio)

                segments, _ = model.transcribe(
                    f.name,
                    language="en",
                    initial_prompt="This is an English interview conversation.",
                    temperature=0,                # more stable
                    beam_size=5,
                    best_of=5,
                    vad_filter=True,
                    condition_on_previous_text=True,
                    no_speech_threshold=0.6,
                    log_prob_threshold=-1.0
                )

                # Combine segments
                new_text = " ".join([seg.text for seg in segments]).strip()

                # Ignore very short/noisy outputs
                if len(new_text) < 5:
                    continue

                print("🗿", new_text)