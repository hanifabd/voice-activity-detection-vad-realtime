import asyncio
import websockets
import webrtcvad
import sys
import struct
import time

vad = webrtcvad.Vad(3)

SAMPLE_RATE = 16000
FRAME_SIZE = 320
BYTES_PER_SAMPLE = 2

INACTIVITY_TIMEOUT = 1

PORT = 5000

class AudioStream:
    def __init__(self):
        self.buffers = {}
        self.last_activity_time = {}

    def add_audio_data(self, client_id, audio_data):
        if client_id not in self.buffers:
            self.buffers[client_id] = b''
            self.last_activity_time[client_id] = time.time()
        self.buffers[client_id] += audio_data
        self.last_activity_time[client_id] = time.time()
    
    def save_audio_data(self, client_id):
        filename = f"audio_{client_id}_{time.time()}.wav"
        with open(filename, "wb") as f:
            f.write(self.buffers[client_id])
        self.buffers[client_id] = b''
        del self.last_activity_time[client_id]

    def process_audio_data(self, client_id):
        buffer = self.buffers[client_id]
        print(len(buffer))
        print(FRAME_SIZE * BYTES_PER_SAMPLE)
        while len(buffer) >= FRAME_SIZE * BYTES_PER_SAMPLE:
            pcm_data = struct.unpack(f'<{FRAME_SIZE}h', buffer[:FRAME_SIZE * BYTES_PER_SAMPLE])
            pcm_data = bytes(struct.pack(f'<{FRAME_SIZE}h', *pcm_data))
            if vad.is_speech(pcm_data, SAMPLE_RATE):
                sys.stdout.write(f"{client_id}: 1\n")
                self.last_activity_time[client_id] = time.time()
            else:
                sys.stdout.write(f"{client_id}: _\n")
                if time.time() - self.last_activity_time[client_id] > INACTIVITY_TIMEOUT:
                    sys.stdout.write(f"{client_id}: X\n")
                    self.save_audio_data(client_id)

            # Flush Terminal
            sys.stdout.flush()
            buffer = buffer[FRAME_SIZE * BYTES_PER_SAMPLE:]
        self.buffers[client_id] = buffer
                
audio_stream = AudioStream()

async def handle_websocket(websocket, path):
    client_id = id(websocket)
    print(f"WebSocket connection established for client {client_id} and path {path}")
    try:
        async for message in websocket:
            audio_stream.add_audio_data(client_id, message)
            audio_stream.process_audio_data(client_id)
            break
    except websockets.exceptions.ConnectionClosed:
        print(f"WebSocket connection closed for client {client_id} and path {path}")
    except Exception as e:
        print(f"Error occurred: {e}")
    finally:
        await websocket.close()
        if client_id in audio_stream.buffers:
            del audio_stream.buffers[client_id]
    
async def main():
    async with websockets.serve(handle_websocket, 'localhost', PORT):
        print(f"WebSocket server started at ws://localhost:{PORT}")
        await asyncio.Future()

asyncio.run(main())
