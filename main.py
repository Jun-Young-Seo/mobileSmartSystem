import time
import paho.mqtt.client as mqtt
import cv2

def on_connect(client, userdata, flag, rc):
	print("jpeg 토픽으로 메시지 구독 신청")
	client.subscribe("jpeg", qos = 0)

def on_message(client, userdata, msg):
	filename = './data/image%d.jpg' % (time.time()*10)
	file = open(filename, "wb") # 파일 열기. 없으면 새로 생성
	file.write(msg.payload) # 수신한 이미지를 파일에 쓰기
	file.close()
	print("이미지수신 %s" % filename)
	image = cv2.imread(filename,cv2.IMREAD_UNCHANGED)
	cv2.imshow('capture',image)#capture 이름 윈도우에 출력
	cv2.waitKey(5000)#publisher가 5초 단위로 이미지를 보내주므로 5초간 키 기다리기
	cv2.destroyAllWindows()#5초 뒤 이미지 창 종료



ip = input("브로커의 IP>>") # 브로커 IP 주소 입력

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message
client.connect(ip, 1883)
client.loop_forever() # 메시지 루프 실행
