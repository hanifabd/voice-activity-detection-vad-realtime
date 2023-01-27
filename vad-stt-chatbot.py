import webrtcvad
import pyaudio
import sys
import time
import wave
from uuid import uuid4
import requests
import json

import whisper
# Load Model
model = whisper.load_model("tiny", download_root="../Speech to Text/whisper/model/")

input("Press Enter to continue...")
print("Voice Activity Monitoring")
print("1 - Activity Detected")
print("_ - No Activity Detected")
print("X - No Activity Detected for Last IDLE_TIME Seconds")
print("\nMonitor Voice Activity Below:")

# Parameters
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000 # 8000, 16000, 32000
FRAMES_PER_BUFFER = 320

# Initialize the VAD with a mode (e.g. aggressive, moderate, or gentle)
# 0: Least filtering noise - 3: Aggressive in filtering noise
vad = webrtcvad.Vad(3)

# Open a PyAudio stream to get audio data from the microphone
pa = pyaudio.PyAudio()
stream = pa.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=FRAMES_PER_BUFFER)

inactive_session = False
inactive_since = time.time()
frames = [] # list to hold audio frames
while True:
    # Read audio data from the microphone
    data = stream.read(FRAMES_PER_BUFFER)

    # Check if the audio is active (i.e. contains speech)
    is_active = vad.is_speech(data, sample_rate=RATE)
    
    # Check Flagging for Stop after N Seconds
    idle_time = 1
    if is_active:
        inactive_session = False
    else:
        if inactive_session == False:
            inactive_session = True
            inactive_since = time.time()
        else:
            inactive_session = True

    # Stop hearing if no voice activity detected for N Seconds
    if (inactive_session == True) and (time.time() - inactive_since) > idle_time:
        sys.stdout.write('X')
        
        # Append data chunk of audio to frames - save later
        frames.append(data)

        # Save the recorded data as a WAV file
        audio_recorded_filename = f'RECORDED-{str(time.time())}-{str(uuid4()).replace("-","")}.wav'
        wf = wave.open(audio_recorded_filename, 'wb')
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(pa.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))
        wf.close()

        # Transcribe
        transcription = model.transcribe(
            audio=audio_recorded_filename,
            language="id",
        )

        # Sent to Chatbot
        response = requests.request(
            "POST", 
            "<CHATBOT_ENDPOINT>", 
            headers={'Content-Type': 'application/json'}, 
            data=json.dumps({
                "sender": "test-user",
                "message": str(transcription["text"].strip()),
            })
        )

        # Print User and Bot Message
        print(f'\nUser: {str(transcription["text"].strip())}')
        for message in response.json():
            print(f'Bot : {json.dumps(message["text"])}')

        # # Stop Debug
        break
        
        # # Some Sample Activity - 5 Seconds execution
        # time.sleep(5)
        # # Flagging to Listen Again
        # inactive_session = False
    else:
        sys.stdout.write('1' if is_active else '_')
    
    # Append data chunk of audio to frames - save later
    frames.append(data)

    # Flush Terminal
    sys.stdout.flush()

# Close the PyAudio stream
stream.stop_stream()
