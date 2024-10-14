import time
from PyQt5.QtCore import QThread, QObject, pyqtSignal
from temperature import read_temp

# 线程执行结果
class TaskResult:

    def __init__(self) -> None:
        self.val = 55


# 升降温线程
class TempTask(QThread):
    
    # 升降温完成的信号
    tempFinished = pyqtSignal(float)

    # 初始化对象
    def __init__(self, parent: QObject = None) -> None:
        super().__init__(parent)
        # 当前温度值，主线程传入
        self.temp = 0
        # 定义临时变量
        self.params = None


    def run(self) -> None:
        # 根据temp的当前值，决定升降温
        while self.running:
            temp = read_temp()
            # 通知主线程
            self.tempFinished.emit(temp)
    def start1(self):
        self.running = True
        self.start()
    def stop1(self):
        self.running = False
        #print("stop")



class TimerStatus(QThread):

    # 定义一个信号，用来通知主线程当前线程运行的阶段以及状态
    runTimer = pyqtSignal(int)

    # 定义线程运行的状态信息
    # T1 = 0          # 正在执行任务1
    #
    # T2 = 1          # 正在执行任务2
    #
    # T3 = 2          # 正在执行任务3
    #
    # ERROR = -1      # 执行失败
    #
    # FINISHED = 0XFFFF
    # 初始化对象
    def __init__(self, parent: QObject = None) -> None:
        super().__init__(parent)
        self.result:TaskResult = None
        self.param = 0
        # 时间值
        self.timevalue = 0
        # self.Timering = False

    def run(self) -> None:
        while self.Timering:
            self.runTimer.emit(self.timevalue)
            time.sleep(1)
            self.timevalue = self.timevalue - 1
            # 模拟结果
            # self.result = TaskResult()
            if self.timevalue == 0:
                self.runTimer.emit(self.timevalue)
                self.Timering = False
                
        
    # 步骤1 65℃ LAMP
    def start1(self):
        self.timevalue = 1080 #1080
        self.Timering = True
        self.start()

    # 步骤2，80℃ 灭活
    def start2(self):
        self.timevalue = 240 #240
        self.Timering = True
        self.start()

    # 步骤3，15℃ 降温
    def start3(self):
        self.timevalue = 10 #60
        self.Timering = True
        self.start()

    # 步骤4，层析检测
    def start4(self):
        self.timevalue = 480
        self.Timering = True
        self.start()

    def start5(self):
        self.timevalue = 50
        self.Timering = True
        self.start()
        
    # 计时停止
    def stop(self):
        self.Timering = False
        self.timevalue = 0