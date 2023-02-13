import whisper
import ast
import struct
import wave
import time
import datetime
import pika
import json
import os


model = whisper.load_model("tiny", download_root="../model/")

def encode_audio_frame(audio_frames):
    encoded = [struct.pack('h' * len(decoded_frame), *decoded_frame) for decoded_frame in audio_frames]
    return encoded

def callback(ch, method, props, body):
    dict_string = body.decode('utf-8')
    data = ast.literal_eval(dict_string)
    print(f'{datetime.datetime.now()} [Received Data] - {data["user_id"]} - {data["session_id"]}')

    # Re encode audio frames
    audio_frames = encode_audio_frame(data["decoded_audio_frames"])
    
    # Save the recorded data as a WAV file
    audio_recorded_filename = f'audio/{data["user_id"]}-{data["session_id"]}-{time.time()}.wav'
    wf = wave.open(audio_recorded_filename, 'wb')
    wf.setnchannels(1)
    wf.setsampwidth(2)
    wf.setframerate(16000)
    wf.writeframes(b''.join(audio_frames))
    wf.close()

    # Check if audio file has been created
    while not os.path.isfile(audio_recorded_filename):
        time.sleep(0.5)

    # Transcibe audio
    transcription = model.transcribe(
        audio = audio_recorded_filename,
        language = "id",
    )
    
    # Get text from transcription
    transcription_text = str(transcription["text"].strip())

    # Dont send text if only contains whitespaces
    if not transcription_text.isspace():
        # Dont send text if only  ""
        if transcription_text != "":
            # Send Request to Show
            ch.basic_publish(
                exchange = '',
                routing_key = "transcription_results_events",
                body=json.dumps({
                    "user_id": data["user_id"],
                    "session_id": data["session_id"],
                    "transcription": transcription_text
                })
            )

while(True):
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost', heartbeat=60))
        channel = connection.channel()
        channel.queue_declare(queue='transcription_events')
        channel.queue_declare('transcription_results_events')
        try:
            channel.basic_qos(prefetch_count=1)
            channel.basic_consume(queue='transcription_events', on_message_callback=callback, auto_ack=True)
            print('[*] Waiting for messages. To exit press CTRL+C')
            channel.start_consuming()
        except KeyboardInterrupt:
            channel.stop_consuming()
            connection.close()
            break
    except pika.exceptions.ConnectionClosedByBroker:
        print("Connection was closed, retrying...")
        continue
    except pika.exceptions.AMQPConnectionError:
        print("Connection was closed, retrying...")
        continue
    except pika.exceptions.AMQPChannelError as err:
        print("Caught a channel error: {}, stopping...".format(err))
        break