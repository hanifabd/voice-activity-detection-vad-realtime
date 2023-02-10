import ast
import pika

sample_user_id = "test-user"
sample_session_id = "test-session"
transcription = []
print(f'Transcription for {sample_user_id} - {sample_session_id}')

def callback(ch, method, props, body):
    dict_string = body.decode('utf-8')
    data = ast.literal_eval(dict_string)
    
    if (data["user_id"] == sample_user_id) and (data["session_id"] == sample_session_id):
        transcription.append(data["transcription"])
        print(f'{" ".join(transcription)}\n')

while(True):
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost', heartbeat=60))
        channel = connection.channel()
        channel.queue_declare('transcription_results_events')
        try:
            channel.basic_qos(prefetch_count=1)
            channel.basic_consume(queue='transcription_results_events', on_message_callback=callback, auto_ack=True)
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