###윈도우 Subscriber 코드###


import time
import paho.mqtt.client as mqtt
import cv2

def on_connect(client, userdata, flag, rc): #브로커에게 연결될 시 실행
	print("윈도우 Subscriber 연결 완료")
	client.subscribe("jpeg",qos=0) #jpeg 토픽으로 구독

def on_message(client, userdata, msg):#브로커에게 메시지가 오면 실행
	if msg.topic == "jpeg": #메시지 토픽 jpeg로 설정
		print("이미지를 수신했습니다.")
		filename = './data/image%d.jpg' % (time.time()*10)
		file = open(filename, "wb") # 파일 열기. 없으면 새로 생성
		file.write(msg.payload) # 수신한 이미지를 파일에 쓰기
		file.close()
		image = cv2.imread(filename,cv2.IMREAD_UNCHANGED) #원본 이미지로 출력
		cv2.imshow('capture',image) #capture 이름의 윈도우에 출력
		cv2.waitKey(5000) #publisher가 5초 단위로 이미지를 보내주므로 5초간 키 기다리기
		cv2.destroyAllWindows() #5초 뒤 이미지 창 종료


ip = input("브로커의 IP>>") # 브로커 IP 주소 입력

client = mqtt.Client()
client.on_connect = on_connect#콜백 함수
client.on_message = on_message#콜백 함수
client.connect(ip, 1883)#1883 포트
client.loop_forever() # 메시지 루프 실행
