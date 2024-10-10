import paho.mqtt.client as mqtt
import json
import threading
import time
import RPi.GPIO as GPIO
import cam1 as Cam1
import Tesseract as ts

plate_num = []

SERVO_PIN = 16
TRIG_PIN = 11
ECHO_PIN = 12
GPIO.setmode(GPIO.BOARD)

GPIO.setup(SERVO_PIN, GPIO.OUT)
GPIO.setup(TRIG_PIN, GPIO.OUT)
GPIO.setup(ECHO_PIN, GPIO.IN)

# 서보 모터 설정
servo = GPIO.PWM(SERVO_PIN, 50)  # 50Hz PWM 주파수
servo.start(0)


def measure_distance():
    GPIO.output(TRIG_PIN, True)
    time.sleep(0.00001)
    GPIO.output(TRIG_PIN, False)
   
    start_time = time.time()
    while GPIO.input(ECHO_PIN) == 0:
        start_time = time.time()
   
    end_time = time.time()
    while GPIO.input(ECHO_PIN) == 1:
        end_time = time.time()
   
    duration = end_time - start_time
    distance = duration * 34300 / 2  # 거리 계산 (cm)
    return distance



def Communication():
    def on_connect(client, userdata, flags, rc):
        if rc == 0:
            print("connected OK")
        else:
            print("Bad connection Returned code=", rc)


    def on_disconnect(client, userdata, flags, rc=0):
        print(str(rc))


    def on_subscribe(client, userdata, mid, granted_qos):
        print("subscribed: " + str(mid) + " " + str(granted_qos))


    def on_message(client, userdata, msg):
        #plate_num = "abc1234"
        print(str(msg.payload.decode("utf-8")))
        data_loc = json.loads(msg.payload.decode())
        license_plate = plate_num.pop()
        #data = {"licensplate": plate_num.pop(), "location": data_loc['location']}
        #json_message = json.dumps(data)
        message = f"{license_plate},{data_loc['location']}"
        print(message) #테스트
        Pub_Status(message) #status로 보내기
       
    client = mqtt.Client()
# 콜백 함수 설정 on_connect(브로커에 접속), on_disconnect(브로커에 접속중료), on_subscribe(topic 구독),
# on_message(발행된 메세지가 들어왔을 때)
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_subscribe = on_subscribe
    client.on_message = on_message
# 로컬 아닌, 원격 mqtt broker에 연결
# address : broker.hivemq.com
# port: 1883 에 연결
    client.connect('broker.hivemq.com', 1883)
# test/hello 라는 topic 구독
    client.subscribe('WFS/door/Connect', 1)
    client.loop_forever()



def Pub_Status(data): #테스트 완료
    def on_connect(client, userdata, flags, rc):
    # 연결이 성공적으로 된다면 완료 메세지 출력
        if rc == 0:
            print("completely connected status")
        else:
            print("Bad connection Returned code=", rc)

# 연결이 끊기면 출력
    def on_disconnect(client, userdata, flags, rc=0):
        print(str(rc))


    def on_publish(client, userdata, mid):
        print("In on_pub callback mid= ", mid)


# 새로운 클라이언트 생성
    client = mqtt.Client()
# 콜백 함수 설정 on_connect(브로커에 접속), on_disconnect(브로커에 접속중료), on_publish(메세지 발행)
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_publish = on_publish
# 로컬 아닌, 원격 mqtt broker에 연결
# address : broker.hivemq.com
# port: 1883 에 연결
    client.connect('broker.hivemq.com', 1883)
    client.loop_start()
# 'test/hello' 라는 topic 으로 메세지 발행
    client.publish('WFS/web/Status', data, 1)
    client.loop_stop()
# 연결 종료
    client.disconnect()


def Pub_GetIn(): #테스트 완료
    def on_connect(client, userdata, flags, rc):
    # 연결이 성공적으로 된다면 완료 메세지 출력
        if rc == 0:
            print("completely connected")
        else:
            print("Bad connection Returned code=", rc)

# 연결이 끊기면 출력
    def on_disconnect(client, userdata, flags, rc=0):
        print(str(rc))


    def on_publish(client, userdata, mid):
        print("In on_pub callback mid= ", mid)


# 새로운 클라이언트 생성
    client = mqtt.Client()
# 콜백 함수 설정 on_connect(브로커에 접속), on_disconnect(브로커에 접속중료), on_publish(메세지 발행)
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_publish = on_publish
# 로컬 아닌, 원격 mqtt broker에 연결
# address : broker.hivemq.com
# port: 1883 에 연결
    client.connect('broker.hivemq.com', 1883)
    client.loop_start()
# 'test/hello' 라는 topic 으로 메세지 발행
    client.publish('WFS/charger/GetIn', "1", 1)
    client.loop_stop()
# 연결 종료
    client.disconnect()


#문열기
def open_door():
    servo.ChangeDutyCycle(7)  # 서보 모터를 90도로 이동
    time.sleep(0.5)
    servo.ChangeDutyCycle(0)
    servo.ChangeDutyCycle(2)
    time.sleep(0.5)
    servo.ChangeDutyCycle(0)
    print("출입문이 닫힙니다")
    time.sleep(2)
    servo.ChangeDutyCycle(7)  # 서보 모터를 90도로 이동
    time.sleep(0.5)
    servo.ChangeDutyCycle(0)


def UC_plate():
    global plate_num
    #plate_num.append("12가1234") #테스트
    while True:
        distance = measure_distance()
        print(f"Distance: {distance:.2f} cm")
        if distance < 5:
            print("차량 감지 완료")
            Pub_GetIn()
            #Cam1.camt1()
            plate_num.append(ts.find_plate('test.jpg'))
           
            open_door()
            #print(plate_num.pop())
            #break  # 테스트
        time.sleep(1)


if __name__ == "__main__":
    try:
        # Start the communication thread
        Communication_thread = threading.Thread(target=Communication)
        Communication_thread.start()
       
        # Start the UC_plate thread
        UC_plate_thread = threading.Thread(target=UC_plate)
        UC_plate_thread.start()
       
        UC_plate_thread.join()
    except KeyboardInterrupt:
        print("프로그램이 종료됩니다.")
    finally:
        # Stop the MQTT client and clean up GPIO
        GPIO.cleanup()
        servo.stop()
