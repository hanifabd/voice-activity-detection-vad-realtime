import webrtcvad
import pyaudio
import sys
import time
import struct
import pika
import json

def decode_audio_frame(audio_frame):
    decoded = struct.unpack('h' * (len(audio_frame) // 2), audio_frame)
    return decoded

print("Voice Activity Monitoring")
print("1 - Activity Detected")
print("_ - No Activity Detected")
print("X - No Activity Detected for Last IDLE_TIME Seconds")
input("Press Enter to continue...")
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

# Connect to Queue
connection_param = pika.ConnectionParameters('localhost')
connection = pika.BlockingConnection(connection_param)
channel = connection.channel()
channel.confirm_delivery()
channel.queue_declare('transcription_events')
channel.queue_declare('transcription_results_events')

inactive_session = False
inactive_since = time.time()
frames = [] # list to hold audio frames
sample_user_id = "test-user"
sample_session_id = "test-session"
while True:
    # Read audio data from the microphone
    data = stream.read(FRAMES_PER_BUFFER)

    # Check if the audio is active (i.e. contains speech)
    is_active = vad.is_speech(data, sample_rate=RATE)
    
    # Check Flagging for Stop after N Seconds
    idle_time_cut = 0.5
    if is_active:
        inactive_session = False
    else:
        if inactive_session == False:
            inactive_session = True
            inactive_since = time.time()
        else:
            inactive_session = True

    # Stop hearing if no voice activity detected for N Seconds
    if (inactive_session == True) and (time.time() - inactive_since) > idle_time_cut:
        sys.stdout.write('X')
        
        # Append data chunk of audio to frames - save later
        frames.append(decode_audio_frame(data))
        
        # Push to Queue
        try:
            channel.basic_publish(
                exchange='',
                routing_key='transcription_events',
                body=json.dumps(
                    {
                        "user_id": sample_user_id,
                        "session_id": sample_session_id,
                        "decoded_audio_frames": frames
                    }
                )
            )
        except pika.exceptions.ConnectionClosed:
            print('Error. Connection closed, and the message was never delivered.')
            continue

        # Clear Frames List
        frames = []

        # # Stop Debug
        # break
        
        # # Some Sample Activity - 5 Seconds execution
        # time.sleep(5)
        # Flagging to Listen Again
        inactive_session = False
    else:
        sys.stdout.write('1' if is_active else '_')
    
    # Append data chunk of audio to frames - save later
    frames.append(decode_audio_frame(data))

    # Flush Terminal
    sys.stdout.flush()

# Close the PyAudio stream
stream.stop_stream()
