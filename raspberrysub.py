###라즈베리파이 subscriber 코드###

import RPi.GPIO as GPIO
import cv2
import time
import io
from PIL import Image, ImageFilter
import paho.mqtt.client as mqtt

LED1=5 #GPIO 5 10cm 이내일 때 켜질 LED
LED2=6 #GPIO 6 20cm 이내일 때 켜질 LED

#Led 제어 클래스
class Led:
	def __init__(self):#생성자
		GPIO.setup(LED1, GPIO.OUT)	# GPIO5 핀을 출력으로 지정
		GPIO.setup(LED2, GPIO.OUT)  # GPIO6 핀을 출력으로 지정

	def ledOn(self,pin):#GPIO pin에 연결된 LED On
		GPIO.output(pin, 1)

	def ledOff(self,pin):#GPIO pin에 연결된 LED Off
		GPIO.output(pin,0)

	def ledControl(self,distance):#전체 LED 컨트롤 함수
		if distance < 10:#거리 10cm 이하, 두 LED 모두 on
			self.ledOn(5)
			self.ledOn(6)
		elif distance < 20:#거리 20cm 이하, 6번 LED만 on
			self.ledOn(6)
			self.ledOff(5)
		else:#거리가 20 이상일 시 두 LED off
			self.ledOff(5)
			self.ledOff(6)

class Sub: #subscriber
	def __init__(self):#생성자
		self.led = Led()#Led 클래스 객체 생성
		self.client = mqtt.Client()#mqtt Client 객체 생성

	def on_connect(self,client, userdata, flag, rc): #브로커에 연결될 시 실행
		print("라즈베리파이 subscriber 연결 완료")
		client.subscribe("distance", qos=0)#"distance" 토픽으로 구독

	def on_message(self,client, userdata, msg):#브로커에서 메시지가 오면 실행
		distance = float(msg.payload.decode())#msg에 오는 코드를 실수형으로 변형해서 distance에 저장
		print("라즈베리파이에서 수신한 길이입니다. %f cm"%distance)
		self.led.ledControl(distance)#거리에 따라 led를 제어

	def run(self):
		self.client.on_connect = self.on_connect #콜백함수 등록
		self.client.on_message = self.on_message #콜백함수 등록
		ip = input("브로커의 IP>>")  # 브로커 IP 주소 입력
		self.client.connect(ip, 1883)
		self.client.loop_forever()#메시지 루프 실행

if __name__== "__main__": #Main
	GPIO.setmode(GPIO.BCM)  # BCM 모드로 작동
	GPIO.setwarnings(False)  # 경고글이 출력되지 않게 설정
	sub = Sub()

	try:
		sub.run()
	except KeyboardInterrupt: #Ctrl C 입력시 예외처리
		print("Ctrl+C로 강제종료")
	finally:
		GPIO.cleanup()  # 어떤 식으로 종료되든 GPIO 정리