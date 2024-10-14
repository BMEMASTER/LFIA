import platform
if platform.platform().upper().startswith("LINUX"):
    import RPi.GPIO as GPIO
import time
from temperature import read_temp
#import cv2 as cv

TERMINAL1 = 35  # IN1
TERMINAL2 = 37  # IN2
TERMINAL3 = 29  # DIR
TERMINAL4 = 31  # PUL
TERMINAL5 = 15  # PAD

class PID():
    def __init__(self, dt, max, min, Kp, Ki, Kd):
        self.dt = dt  # 循环时长
        self.max = max  # 操作变量最大值
        self.min = min  # 操作变量最小值
        self.Kp = Kp  # 比例增益
        self.Ki = Ki  # 微分增益
        self.Kd = Kd  # 积分增益
        self.error = 0  # 当前误差
        self.error_1 = 0  #上次误差
        self.error_2 = 0  # 上上次误差
        self.pre_output = 0  #上次的输出值

    def calculate(self, setPoint, pv, t):
        # 其中 pv:process value 即过程值
        
        error = setPoint - t  # 误差（设定值与实际值的差值）
        Pout = self.Kp * (error - self.error_1)  # 比例项 Kp * (e(t)-e(t-1))
        Iout = self.Ki * error  # 积分项 Ki * e(t)
        Dout = self.Kd * (error - 2*self.error_1 + self.error_2)  # 微分项 Kd * (e(t)-2*e(t-1)+e(t-2))
        output = Pout + Iout + Dout + self.pre_output  # 新的目标值  位置式PID：u(t) = Kp*(e(t)-e(t-1)) + Ki*e(t) + Kd*(e(t)-2*e(t-1)+e(t-2)) + u(t-1）

        if (output > self.max):
            output = self.max
        elif (output < self.min):
            output = self.min

        self.pre_output = t
        self.error_2 = self.error_1  #e(k-2) = e(k) ,进入下一次计算使用
        self.error_1 = error  # e(k-1) = e(k)
        return output

def setup():
    # 初始化
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BOARD)
    GPIO.setup(TERMINAL1, 0)
    GPIO.setup(TERMINAL2, 0)
    GPIO.setup(TERMINAL3, 0)
    GPIO.setup(TERMINAL4, 0)
    GPIO.setup(TERMINAL5, 0)
def start(pulse_terminal):
    # 开启脉冲
    pulse_terminal.start(0)
    pulse_terminal.ChangeDutyCycle(50)  # 设置脉冲带宽 0~100


def stop(pulse_terminal):
    # 停止脉冲
    pulse_terminal.stop()


def set_direction(direction=1):
    GPIO.output(TERMINAL3, direction)  # 设置高低电平


def fill():
    setup()
    pulse_terminal = GPIO.PWM(TERMINAL4, 1000)  # 固定丝杆步进电机压到底
    set_direction(0)
    start(pulse_terminal)
    time.sleep(6)
    stop(pulse_terminal)
    GPIO.output(TERMINAL4, 0)
    
    
def titration():
    setup()
    pulse_terminal = GPIO.PWM(TERMINAL4, 1000)  # 固定丝杆步进电机压一半
    set_direction(0)
    start(pulse_terminal)
    time.sleep(3)
    stop(pulse_terminal)
    GPIO.output(TERMINAL4, 0)

def half_restart():
    setup()
    pulse_terminal = GPIO.PWM(TERMINAL4, 1000)  # 固定丝杆步进电机half复位
    set_direction(0)
    start(pulse_terminal)
    time.sleep(0.5)
    stop(pulse_terminal)
    GPIO.output(TERMINAL4, 0)

def drainage():
    setup()
    pulse_terminal = GPIO.PWM(TERMINAL4, 1000)  # 固定丝杆步进电机复位
    set_direction(1)
    start(pulse_terminal)
    time.sleep(4)
    stop(pulse_terminal)
    GPIO.output(TERMINAL4, 0)
    
    
def light_on():
    setup()
    GPIO.output(TERMINAL3, 1)  # 设置高低电平
    
    
def light_off():
    setup()
    GPIO.output(TERMINAL3, 0)  # 设置高低电平
    GPIO.cleanup()
   
def RAD_ON():
    setup()
    GPIO.output(TERMINAL5, 1)
    
def RAD_OFF():
    setup()
    GPIO.output(TERMINAL5, 0)
    

    
            
            
            
    
if __name__ == '__main__':  # Program start from here
    #setup()
    #pulse_terminal = GPIO.PWM(TERMINAL3, 1000) # 
    #start(pulse_terminal)
    #time.sleep(5)
    #stop(pulse_terminal)
    #RAD_ON()
    #time.sleep(10)
    #RAD_OFF()
    #titration()
    #time.sleep(2)
    half_restart()
    #time.sleep(1)
    #drainage()
    #GPIO.cleanup()

