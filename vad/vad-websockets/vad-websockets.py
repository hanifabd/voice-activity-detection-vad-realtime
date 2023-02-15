import asyncio
import websockets
import webrtcvad
import struct
import sys


vad = webrtcvad.Vad(3)

class AudioStream:
    def __init__(self) -> None:
        self.sample_rate = 16000
        self.frame_size = 320
        self.bytes_per_sample = 2
        self.buffer = b''

    def convert_buffer_size(self, audio_frame):
        buffer = self.buffer + audio_frame
        if len(buffer) >= (self.frame_size * self.bytes_per_sample):
            split_640 = struct.unpack(f'<{self.frame_size}h', buffer[:self.frame_size * self.bytes_per_sample])
            split_640 = bytes(struct.pack(f'<{self.frame_size}h', *split_640))
            self.buffer = buffer[self.frame_size * self.bytes_per_sample:]
            status = True
        else:
            split_640 =  buffer
            self.buffer = buffer
            status = False
        return split_640, status
    
    def voice_activity_detection(self, audio_frame):
        converted_frame, status = self.convert_buffer_size(audio_frame)
        if status == True:
            is_speech = vad.is_speech(converted_frame, sample_rate=16000)
            if is_speech:
                return "1"
            else:
                return "_"
        else:
            return ""


audiostream = AudioStream()
async def handler(websocket, path):
    print(f"WebSocket connection established for client from {path}")
    try:
        async for message in websocket:
            is_active = audiostream.voice_activity_detection(message)
            sys.stdout.write(is_active)
            sys.stdout.flush()
    except websockets.exceptions.ConnectionClosed:
        print(f"WebSocket connection closed for client")
    except Exception as e:
        print(f"Error occurred: {e}")
    finally:
        await websocket.close()

async def main():
    PORT = 5000
    async with websockets.serve(handler, 'localhost', PORT):
        print(f"WebSocket server started at ws://localhost:{PORT}")
        await asyncio.Future()

asyncio.run(main())