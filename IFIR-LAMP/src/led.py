# -*- coding: utf-8 -*-
import platform
if platform.platform().upper().startswith("LINUX"):
    import RPi.GPIO as GPIO


class LedControl:
    """ 控制LED开关的对象 """
    def __init__(self):
        # 初始化控制LED灯的GPIO
        if platform.platform().upper().startswith("LINUX"):
            try:
                # 使用第35，37号引脚控制两个紫光灯的开关
                self.gpioPins = [11, 13]
                # 初始化树莓派GPIO
                GPIO.setwarnings(False)
                GPIO.setmode(GPIO.BOARD)
                GPIO.setup(self.gpioPins, GPIO.OUT)
            except Exception as e:
                print("当前系统不支持GPIO", e)

    def __del__(self):
        """ 清理资源，清楚引脚状态 """
        if platform.platform().upper().startswith("LINUX"):
            try:
                # 拉低引脚的电平并清除
                GPIO.output(self.gpioPins, GPIO.LOW)
                GPIO.cleanup()
            except Exception as e:
                print("引脚资源释放失败...", e)

    def setOn(self):
        """ 打开led灯光 """
        if platform.platform().upper().startswith("LINUX"):
            try:
                GPIO.output(self.gpioPins, GPIO.HIGH)
            except Exception as e:
                print("打开LED灯失败", e)

    def setOff(self):
        """ 关闭led灯光 """
        if platform.platform().upper().startswith("LINUX"):
            try:
                GPIO.output(self.gpioPins, GPIO.LOW)
            except Exception:
                print("关闭LED灯失败")