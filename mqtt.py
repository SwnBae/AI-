import time
import paho.mqtt.client as mqtt
import paho.mqtt.publish as publish

broker_address="broker.hivemq.com"  # raspberryPi
broker_port=8883

client = mqtt.Client("WFS")

client.connect(broker_address, broker_port)

topic = "test/topic"
message = "Hello, MQTT!"

# 메시지 퍼블리시
publish.single(topic,message,hostname = broker_address)

print(f"Published message '{message}' to topic '{topic}'")

# 클라이언트 연결 종료
client.disconnect()




import paho.mqtt.client as mqtt

# MQTT 브로커 주소와 포트 설정
broker_address = "broker.hivemq.com"
broker_port = 1883

# 메시지 수신 시 호출될 콜백 함수 정의
def on_message(client, userdata, message):
    print(f"Received message '{message.payload.decode()}' on topic '{message.topic}'")

# MQTT 클라이언트 생성
client = mqtt.Client("WFS")

# 콜백 함수 등록
client.on_message = on_message

# 브로커에 연결
client.connect(broker_address, broker_port)

# 구독할 주제 설정
topic = "test/topic"
client.subscribe(topic)

# 네트워크 루프 실행 (메시지를 기다리며 처리)
client.loop_forever()
