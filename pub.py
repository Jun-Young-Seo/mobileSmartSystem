###라즈베리파이 Publisher 코드###


import RPi.GPIO as GPIO
import cv2
import time
import io
from PIL import Image, ImageFilter
import paho.mqtt.client as mqtt

trig = 26  #GPIO 26핀 트리거
echo = 27  #GPIO 27핀 에코

#초음파센서 제어 클래스
class Sonic:
	def __init__(self):#생성자
		GPIO.setup(trig, GPIO.OUT) #트리거는 출력용으로 설정 26
		GPIO.setup(echo, GPIO.IN)  #에코는 입력용으로 설정 27

	def measureDistance(self,trig, echo):
		GPIO.output(trig, GPIO.HIGH) # trig = 26 , echo = 27
		time.sleep(0.1)#0.1초 단위로 거리를 측정. 이 코드가 없으면 발사와 동시에 수신해서 측정이 잘 안됨
		GPIO.output(trig, GPIO.LOW) # trig 핀 신호 High->Low. 초음사 발사

		while(GPIO.input(echo) == 0): # echo 핀 값이 1로 바뀔때까지 루프
			pass

		# echo 핀 값이 1이면 초음파 발사
		pulseStart = time.time() # 초음파 발사 시간 기록
		while(GPIO.input(echo) == 1): # echo 핀 값이 0이 될때까지 루프
			pass

		# echo 핀 값이 0이 되면 초음파 수신
		pulseEnd = time.time() # 초음파 돌아 온 시간 기록
		pulseDuration = pulseEnd - pulseStart # 경과 시간 계산
		distance = pulseDuration*340*100/2#cm 단위로
		print(distance," cm")
		return distance # 거리 계산하여 리턴(단위 cm)

class Camera:
	def __init__(self):
		self.camera = cv2.VideoCapture(0, cv2.CAP_V4L)
		self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
		self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)#640x480 사이즈 사진 촬영
		self.camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # 버퍼 크기를 1로 설정

	def __del__(self):#소멸자
		#소멸될 때 카메라 자원 해제
		self.camera.release()
		cv2.destroyAllWindows()

	def take_picture(self,distance):
		# 버퍼에 저장된 모든 프레임을 버리고 새 프레임 읽기
		# 최신 이미지 얻기 위해
		for i in range(2):
			ret, frame = self.camera.read()

		pilim = Image.fromarray(frame)  # 프레임 데이터를 이미지 형태로 변환
		stream = io.BytesIO()  # 이미지를 저장할 스트림 버퍼 생성
		pilim.save(stream, 'jpeg')  # 프레임을 jpeg 형식으로 바꾸어 스트림에 저장
		imBytes = stream.getvalue()  # 스트림에서 바이트 배열로 이미지 저장
		return imBytes #Jpeg 데이터 반환

class Mqtt:
	def __init__(self):#생성자
		broker_ip = "localhost" #publisher가 라즈베리파이므로 localhost
		self.client = mqtt.Client() #mqtt 클라이언트 객체 생성
		self.client.connect(broker_ip, 1883)  # 1883 포트로 mosquitto에 접속
		self.client.loop_start()  # 메시지 루프를 실행하는 스레드 생성
	def __del__(self):#소멸자
		self.client.loop_stop()#클라이언트 객체 루프 종료
		self.client.disconnect()#클라이언트 객체 연결 종료
	def publishDistance(self,distance):
		self.client.publish("distance", distance, qos=0)# 라즈베리파이 subscriber에게 거리 전송
	def publishImBytes(self,imBytes):
		self.client.publish("jpeg", imBytes, qos=0)  # 윈도우 subscriber에게 이미지 전송

class Pub: #publisher 클래스
	#distance 토픽으로 거리, jpeg 토픽으로 이미지 publishing
	def run(self):
		sonic = Sonic()#초음파 센서 객체 생성
		mqtt = Mqtt()#mqtt 객체 생성
		camera = Camera()#카메라 객체 생성
		while True:
			distance = sonic.measureDistance(trig,echo) #거리 측정
			mqtt.publishDistance(distance) #거리 publish
			if distance<10:#거리가 10cm 이하일 때 이미지 publish
				imBytes = camera.take_picture(distance) #jpeg 데이터 imBytes에 저장
				mqtt.publishImBytes(imBytes) #거리가 10 이하일 때 publish
				time.sleep(5) #시스템 처리 시간을 위해 5초단 대기.
				#time.sleep()이 없으면 전송 후 바로 캡쳐 후 또 보내서 전송이 잘 안됨


if __name__== "__main__":
	GPIO.setmode(GPIO.BCM)  # BCM 모드로 작동
	GPIO.setwarnings(False)  # 경고글이 출력되지 않게 설정
	pub = Pub()
	try:
		pub.run()
	except KeyboardInterrupt: #Ctrl C 입력시 예외처리
		print("Ctrl+C로 강제종료")
	finally:
		GPIO.cleanup()  # 어떤 식으로 종료되든 GPIO 정리