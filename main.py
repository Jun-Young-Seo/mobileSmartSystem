import RPi.GPIO as GPIO
import cv2
import time
import io
from PIL import Image, ImageFilter
import paho.mqtt.client as mqtt

LED1=5 #GPIO 5 10cm 이내일 때 켜질 LED
LED2=6 #GPIO 6 20cm 이내일 때 켜질 LED
trig = 26  #GPIO20
echo = 27  #GPIO16

#Led 제어 클래스
class Led:
	def __init__(self):
		GPIO.setup(LED1, GPIO.OUT)
		GPIO.setup(LED2, GPIO.OUT)  # GPIO6 핀을 출력으로 지정

	def ledOn(self,pin):
		GPIO.output(pin, 1)

	def ledOff(self,pin):
		GPIO.output(pin,0)

	def ledControl(self,distance):
		if distance < 10:
			self.ledOn(5)
			self.ledOn(6)
		elif distance < 20:
			self.ledOn(6)
			self.ledOff(5)
		else:
			self.ledOff(5)
			self.ledOff(6)

#초음파센서 제어 클래스
class Sonic:
	def __init__(self):
		GPIO.setup(trig, GPIO.OUT)
		GPIO.setup(echo, GPIO.IN)

	def measureDistance(self,trig, echo):
		GPIO.output(trig, GPIO.HIGH) # trig = 20 , echo = 16
		time.sleep(0.1)#0.1초 단위로 거리를 측정.
		GPIO.output(trig, GPIO.LOW) # trig 핀 신호 High->Low. 초음사 발사 지시


		while(GPIO.input(echo) == 0): # echo 핀 값이 1로 바뀔때까지 루프
			pass


		# echo 핀 값이 1이면 초음파가 발사되었음
		pulse_start = time.time() # 초음파 발사 시간 기록
		while(GPIO.input(echo) == 1): # echo 핀 값이 0이 될때까지 루프
			pass


		# echo 핀 값이 0이 되면 초음파 수신하였음
		pulse_end = time.time() # 초음파가 되돌아 온 시간 기록
		pulse_duration = pulse_end - pulse_start # 경과 시간 계산
		distance = pulse_duration*340*100/2
		print("%f cm"%distance)
		return distance # 거리 계산하여 리턴(단위 cm)

class Camera:
	def __init__(self):
		self.camera = cv2.VideoCapture(0, cv2.CAP_V4L)
		self.size = self.camera.get(cv2.CAP_PROP_BUFFERSIZE)
		self.camera.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
		self.camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
		self.camera.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # 버퍼 크기를 1로 설정

	def __del__(self):
		self.camera.release()
		cv2.destroyAllWindows()

	def take_picture(self,distance):
		# 버퍼에 저장된 모든 프레임을 버리고 새 프레임 읽기
		for i in range(2):
			ret, frame = self.camera.read()

		pilim = Image.fromarray(frame)  # 프레임 데이터를 이미지 형태로 변환
		stream = io.BytesIO()  # 이미지를 저장할 스트림 버퍼 생성
		pilim.save(stream, 'jpeg')  # 프레임을 jpeg 형태로 바꾸어 스트림에 저장
		imBytes = stream.getvalue()  # 바이트 배열로 저장
		return imBytes
class Mqtt:
	def __init__(self):
		broker_ip = "localhost"
		self.client = mqtt.Client()
		self.client.connect(broker_ip, 1883)  # 1883 포트로 mosquitto에 접속
		self.client.loop_start()  # 메시지 루프를 실행하는 스레드 생성
	def __del__(self):
		self.client.loop_stop()
		self.client.disconnect()
	def publish(self,imBytes):
		self.client.publish("jpeg", imBytes, qos=0)  # 이미지 전송

class App:
	def run(self):
		led = Led()
		sonic = Sonic()
		camera = Camera()
		mqtt =Mqtt()
		while True:
			distance = sonic.measureDistance(trig, echo)
			led.ledControl(distance)
			if distance <10 :
				imBytes = camera.take_picture(distance)
				mqtt.publish(imBytes)
				print("사진 전송 완료... 5초 대기")
				time.sleep(5);


if __name__== "__main__":
	GPIO.setmode(GPIO.BCM)  # BCM 모드로 작동
	GPIO.setwarnings(False)  # 경고글이 출력되지 않게 설정
	app = App()

	try:
		app.run()
	except KeyboardInterrupt: #Ctrl C 입력시 예외처리
		print("Ctrl+C로 강제종료")
	finally:
		GPIO.cleanup()  # 어떤 식으로 종료되든 GPIO 정리