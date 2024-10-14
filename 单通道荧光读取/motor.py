import RPi.GPIO as GPIO
import time

TERMINAL1 = 38  # PUL +
TERMINAL2 = 35  # DIR +
TERMINAL3 = 40  # LIGHT +

def setup():
    # 初始化
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(TERMINAL1, 0)
    GPIO.setup(TERMINAL2, 0)
    GPIO.setup(TERMINAL3, 0)

def start(pulse_terminal):
    # 开启脉冲
    pulse_terminal.start(0)
    pulse_terminal.ChangeDutyCycle(50)  # 设置脉冲带宽 0~100


def stop(pulse_terminal):
    # 停止脉冲
    pulse_terminal.stop()


def set_direction(direction=1):
    GPIO.output(TERMINAL2, direction)  # 设置高低电平


def fill():
    setup()
    pulse_terminal = GPIO.PWM(TERMINAL1, 2000)
    set_direction(1)
    start(pulse_terminal)
    time.sleep(25)
    stop(pulse_terminal)
    GPIO.cleanup()
    
    
def titration():
    setup()
    pulse_terminal = GPIO.PWM(TERMINAL1, 800)
    set_direction(1)
    start(pulse_terminal)
    time.sleep(2)
    stop(pulse_terminal)
    GPIO.cleanup()
 

def drainage():
    setup()
    pulse_terminal = GPIO.PWM(TERMINAL1, 2000)
    set_direction(0)
    start(pulse_terminal)
    time.sleep(25)
    stop(pulse_terminal)
    GPIO.cleanup()



def light_led():
    setup()
    GPIO.output(TERMINAL3, 1)
    GPIO.cleanup()


def light_off():
    GPIO.output(TERMINAL3, 0)
    GPIO.cleanup()
if __name__ == '__main__':  # Program start from here
    setup()

    pulse_terminal = GPIO.PWM(TERMINAL1, 2000)# 脉冲带宽调制
    set_direction(1)
    start(pulse_terminal)
    time.sleep(25)
    stop(pulse_terminal)
  # fill()
  # set_direction(0) 
  # start(pulse_terminal)
  # time.sleep(3)

    GPIO.cleanup()



