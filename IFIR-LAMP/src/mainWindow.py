# -*- coding: utf-8 -*-
import sys
import os
import platform
import time
import cv2 as cv
from PyQt5.QtWidgets import QApplication, QMainWindow, QTableWidgetItem, QAbstractItemView, QFileDialog
from PyQt5.QtCore import pyqtSlot, QTimer, QDateTime, QDate, Qt, QObject, QEvent, QStandardPaths, QThread, pyqtSignal
from Ui_MainWindow import Ui_MainWindow
from utils import ImgUtils, ExcelUtil
from Dialog import MessageBox, KeyboardDialog
from config import Config
import dao
from led import LedControl
from logFactory import LoggerFactory
from temperature import read_temp
from threading import Timer
from control import fill, titration, drainage, setup, stop, half_restart, RAD_ON, RAD_OFF
from task import *
if platform.platform().upper().startswith("LINUX"):
    import RPi.GPIO as GPIO
os.environ['MPLCONFIGDIR'] = os.getcwd() + "/configs/"
envpath = '/home/pi/文档/venv/lib/python3.9/site-packages/cv2/qt/plugins/platforms'
os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = envpath


log = LoggerFactory.getLogger()


TERMINAL1 = 35  # IN1
TERMINAL2 = 37  # IN2


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowStaysOnTopHint)
        # 挂载UI组件
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.thread = ThreadClass()
        self.temptask = TempTask()
        self.TimerStatus = TimerStatus()
        # 加载配置文件
        self.config = Config()
        # 数据库
        self.dao = dao.Dao(self.config.dbConfig)
        # 创建缓存文件夹
        self.savePath = self.__createCacheDir__()
        self.historyList = []
        # 初始化相机模块
        self.liveTimer = None   # 相机预览时定时获取图片并显示的定时器
        self.Timer = None
        self.textTimer = None
        self.camera = None
        self.VisionWait = None
        self.__initCamera__()
        # LED灯光控制
        self.led = LedControl()
        # 创建小键盘
        self.keyboard = self.__createKeyBoard__()
        # 初始化UI
        self.__initUI__()
        # QTheard
        self.ui.temp_upBtn.clicked.connect(self.thread.start_worker1)
        self.ui.temp_downBtn_2.clicked.connect(self.thread.start_worker2)
        self.ui.stopBtn.clicked.connect(self.thread.stop_worker)
        # 定义线程
        self.thread.runstatus.connect(self.onThreadStatus)
        self.temptask.tempFinished.connect(self.onTemp)
        self.TimerStatus.runTimer.connect(self.onTimer)

    def __initCamera__(self):
        """ 初始化相机参数 """
        print("init camera...")
        cameraInitTime = QDateTime.currentDateTime().toMSecsSinceEpoch()
        status = False
        for i in range(10):
            self.camera = cv.VideoCapture(i)
            if self.camera.isOpened():
                self.camera.set(cv.CAP_PROP_FRAME_WIDTH, 640)
                self.camera.set(cv.CAP_PROP_FRAME_HEIGHT, 480)
                print("camera[{}] inited use time:{}".format(i, QDateTime.currentDateTime().toMSecsSinceEpoch() - cameraInitTime))
                status = True
                break
        if status is False:
            if MessageBox.warning(self, "警告", "未发现图像采集设备，是否要关闭程序", "关闭", "忽略") == 1:
                self.close().emit()

    def __initUI__(self):
        # 设置初始化页面为首页
        self.ui.stackedWidget.setCurrentIndex(0)
        # 初始化输入框获取焦点时的事件
        self.__initFocusEvent__()
        # 初始化表格样式及表头数据
        self.__initTable__()
        # 把窗口移动到屏幕的中间
        self.move(0, 0)

    def __initTable__(self):
        """ 初始化查询表格 """
        # 表1 [时间， 编号]
        table1 = self.ui.qTableWidget_1
        # # 将表格变为禁止编辑
        table1.setEditTriggers(QAbstractItemView.NoEditTriggers)
        # 设置表格整行选中
        table1.setSelectionBehavior(QAbstractItemView.SelectRows)
        table1.setColumnWidth(0, 260)
        # 表2 [序号，R值， G值]
        table2 = self.ui.qTableWidget_2
        # # 将表格变为禁止编辑
        table2.setEditTriggers(QAbstractItemView.NoEditTriggers)
        # 设置表格整行选中
        table2.setSelectionBehavior(QAbstractItemView.SelectRows)
        table2.setColumnWidth(1, 180)
        table2.setColumnWidth(2, 180)

    def __createCacheDir__(self):
        """ 创建保存文件的目录, 若存在则删除 """
        cacheDir = os.path.join(self.getDesktopPath(), "IMG_VISION")
        if not os.path.exists(cacheDir):
            # 创建缓存文件夹
            os.mkdir(cacheDir)
        captureDir = os.path.join(self.getDesktopPath(), "IMG_VISION", "capture")
        if not os.path.exists(captureDir):
            # 创建缓存文件夹
            os.mkdir(captureDir)
        return cacheDir, captureDir

    def __createKeyBoard__(self):
        """ 创建小键盘 """
        keyBoard = KeyboardDialog(self)
        keyBoard.inputKey.connect(self.onKeyBoardValue)
        return keyBoard

    def __initFocusEvent__(self):
        """ 初始化输入框获取焦点时的事件 """
        self.ui.numLineEdit.installEventFilter(self)
        self.ui.numLineEdit.clearFocus()

    def getImg(self):
        """ 获取图像 """
        ret, frame = self.camera.read()
        if ret:
            # 旋转180度后返回
            frame = cv.transpose(frame)
            img = cv.flip(frame, -1)
            return img
        return None

    def eventFilter(self, obj: QObject, event: QEvent):
        if obj == self.ui.numLineEdit and event.type() == QEvent.MouseButtonPress:
            self.keyboard.show()
            self.ui.numLineEdit.setFocus()
        return super(MainWindow, self).eventFilter(obj, event)

    def startLive(self):
        """ 实时预览图片 """
        # 修改预览按钮样式
        self.ui.previewBtn.setText("停止")
        # self.ui.previewBtn.setStyleSheet("background-color:#F56C6C;")
        # 打开LED灯
        self.led.setOn()
        # 开启定时器
        if self.liveTimer is None:
            self.liveTimer = QTimer(self)
            self.liveTimer.timeout.connect(self.onCameraLive)
        if not self.liveTimer.isActive():
            self.liveTimer.start(100)

    def stopLive(self):
        """ 停止实时预览 """
        # 修改预览按钮样式
        self.ui.previewBtn.setText("预览")
        # self.ui.previewBtn.setStyleSheet("background-color:rgba(64, 158, 255, 255);")
        # 关闭LED灯
        self.led.setOff()
        # 暂停定时器
        if self.liveTimer is not None and self.liveTimer.isActive():
            self.liveTimer.stop()
    
    def start_temp(self):
        """ 实时预览温度 """
        self.ui.temp_downBtn.setText("停止")
        
        if self.Timer is None:
            self.Timer = QTimer(self)
            self.Timer.timeout.connect(self.on_tempdown_clicked)
        if not self.Timer.isActive():
            self.Timer.start(1000)
            
    def stop_temp(self):
        """ 停止实时预览温度 """
        self.ui.temp_downBtn.setText("测温")
        
        if self.Timer is not None and self.Timer.isActive():
            self.Timer.stop()

    def start_text(self):
        """实时显示状态"""
        #self.ui.lamp_Btn.setText("暂停")
        if self.textTimer is None:
            self.textTimer = QTimer(self)
            self.textTimer.timeout.connect(self.lamp_text)
        if not self.textTimer.isActive():
            self.textTimer.start(1000)

    def stop_text(self):
        #self.ui.lamp_Btn.setText("LAMP")
        if self.textTimer is not None and self.textTimer.isActive():
            self.textTimer.stop()
            
    def getDesktopPath(self):
        """ 获取桌面路径 """
        return QStandardPaths.writableLocation(QStandardPaths.DesktopLocation)

    def processImg(self, frame):
        """ 图片处理 """
        # 截取有效部分
        img = ImgUtils.getROI(frame)
        if img is not None:
            # 显示获取到的图片
            ImgUtils.liveRGBImg(img, self.ui.srcImgLabel)
            # 统一图像大小
            img = cv.resize(img, (640, 150))
            # 分离通道
            chB, chG, chR = cv.split(img)
            # 对R通道进行处理
            peaksR, projectionImgR = ImgUtils.processImgChannel(chR, "R", (0, 0, 255))
            print("peaksR:", peaksR)
            ImgUtils.liveRGBImg(projectionImgR, self.ui.channelRLabel)
            # 对G通道进行处理
            peaksG, projectionImgG = ImgUtils.processImgChannel(chG, "G", (0, 255, 0))
            #print("peaksG:", peaksG)
            #ImgUtils.liveRGBImg(projectionImgG, self.ui.channelGLabel)
            #  判断R和G通道峰值的数量，对较少的补None
            rSize, gSize = len(peaksR), len(peaksG)
            if rSize > 0 or gSize > 0:
                if rSize > gSize:
                    lessVal = rSize - gSize
                    # 在gSize集合中补0
                    for i in range(lessVal):
                        peaksG.append(ImgUtils.Peak(None))
                elif rSize < gSize:
                    lessVal = gSize - rSize
                    for i in range(lessVal):
                        peaksR.append(ImgUtils.Peak(None))
            # 显示结果
            self.showResult(peaksR)
            # # # 保存结果
            self.saveResult(peaksR)
            # 清空编号，防止重复编号测量
            self.ui.numLineEdit.setText("")
        else:
            MessageBox.warning(self, "提示", "未获取到有效图片", "关闭")

    def showResult(self, peaksR):
        """ 显示检测结果 """
        table = self.ui.resultTableWidget
        table.model().removeRows(0, table.rowCount())
        table.setRowCount(len(peaksR))
        for i in range(len(peaksR)):
            # 填充序号
            numItem = QTableWidgetItem(str(i + 1))
            numItem.setTextAlignment(Qt.AlignCenter)
            table.setItem(i, 0, QTableWidgetItem(numItem))
            rVal = peaksR[i].avePix
            #gVal = peaksG[i].avePix
            # 填充C值
            rItem = QTableWidgetItem(str(rVal))
            rItem.setTextAlignment(Qt.AlignCenter)
            table.setItem(i, 1, QTableWidgetItem(rItem))
            # 填充T值
            # gItem = QTableWidgetItem(str(gVal))
            # gItem.setTextAlignment(Qt.AlignCenter)
            # table.setItem(i, 2, QTableWidgetItem(gItem))


    def saveResult(self, peaksR):
        """ 获取测量结果并保存结果 """
        # 检查是否存在相同的记录
        try:
            createTime = QDateTime.currentDateTime()
            testNum = self.ui.numLineEdit.text()
            if testNum is None:
                testNum = ""
            self.dao.addRecord(peaksR, testNum, createTime)
        except Exception as e:
            log.error(e)

    @pyqtSlot(str)
    def onKeyBoardValue(self, val):
        # self.ui.numLineEdit.setText
        text = self.ui.numLineEdit.text()
        print(val)
        if val == "delete":
            if text is not None and text.strip() != "":
                text = text.strip()
                text = text[0:len(text) - 1]
                self.ui.numLineEdit.setText(text)
        elif val == "clear":
            self.ui.numLineEdit.clear()
        else:
            if text is not None and text.strip() != "":
                self.ui.numLineEdit.setText(text + val)
            else:
                self.ui.numLineEdit.setText(val)

    @pyqtSlot()
    def onCameraLive(self):
        frame = self.getImg()
        if frame is not None:
            # 裁取要显示的部分
            img = ImgUtils.getROI(frame)
            if img is not None:
                ImgUtils.liveRGBImg(img, self.ui.srcImgLabel)
            else:
                self.ui.srcImgLabel.clear()
                self.ui.srcImgLabel.setText("请插入样本")

    @pyqtSlot()
    def on_backBtn_clicked(self):
        """ 测量页面返回按钮点击事件 """
        # 返回主页面
        # 停止预览
        self.stopLive()
        self.keyboard.close()
        RAD_OFF()
        self.ui.stackedWidget.setCurrentIndex(0)

    @pyqtSlot()
    def on_testBtn_clicked(self):
        """ 测量菜单按钮点击事件 """
        # 设置当前页面为测量页面
        self.ui.stackedWidget.setCurrentIndex(2)

    @pyqtSlot()
    def on_testBtn_2_clicked(self):
        """ 调试页面切换检测页面 """
        self.ui.stackedWidget.setCurrentIndex(2)

    @pyqtSlot()
    def on_queryBtn_clicked(self):
        """ 查询菜单按钮点击事件 """
        # 停止预览
        self.stopLive()
        # 设置当前页面为查询页面
        self.ui.stackedWidget.setCurrentIndex(3)
        today = QDate.currentDate()
        self.ui.qBeginDate.setDate(today)
        self.ui.qEndDate.setDate(today)
        
    @pyqtSlot()   
    def on_tempdown(self):
        self.ui.temp_downBtn.clicked.connect(self.start_temp)
        
    def on_tempdown_clicked(self):
        """测温按钮点击事件 """
        global G_temp
        re_data = read_temp()  # 将AD值处理成温度
        G_temp = re_data
        # print(re_data)
        self.ui.temp.setText('%.3f' % re_data + "℃")  # 改变当前温度窗口数据
            
    
    @pyqtSlot()
    def on_backbtn_2_clicked(self):
        """加热界面返回停止测温事件"""
        self.stop_temp()

    @pyqtSlot()
    def on_tempBtn_clicked(self):
        """调试按钮点击事件"""
        # 设置当前页面为加热页面
        self.ui.stackedWidget.setCurrentIndex(1)
        self.ui.temp.setAlignment(Qt.AlignCenter)


    @pyqtSlot()
    def on_didingBtn_clicked(self):
        """ 按压按钮点击事件 """
        self.ui.stackedWidget.setCurrentIndex(4)
        
        self.ui.ding_halfBtn.setEnabled(True)
        #self.ui.resetBtn.setEnabled(False)
        self.ui.ding_halfBtn_2.setEnabled(False)
    @pyqtSlot()
    def on_ding_allBtn_clicked(self):
        """自检按钮点击事件"""
        fill()
        #self.ui.ding_allBtn.setEnabled(False)
        self.ui.ding_halfBtn.setEnabled(False)
        self.ui.ding_halfBtn_2.setEnabled(False)
        #self.ui.resetBtn.setEnabled(True)
    @pyqtSlot()
    def on_ding_halfBtn_clicked(self):
        """混合按压按钮点击事件"""
        titration()
        #self.ui.ding_allBtn.setEnabled(False)
        #self.ui.ding_halfBtn.setEnabled(False)
        self.ui.ding_halfBtn_2.setEnabled(True)
        #self.ui.resetBtn.setEnabled(False)
    @pyqtSlot()
    def on_ding_halfBtn_2_clicked(self):
        """层析反应按压按钮点击事件"""
        half_restart()
        time.sleep(1)
        drainage()
        #self.ui.ding_allBtn.setEnabled(True)
        self.ui.ding_halfBtn.setEnabled(True)
        self.ui.ding_halfBtn_2.setEnabled(False)
        #self.ui.resetBtn.setEnabled(False)

    @pyqtSlot()
    def on_resetBtn_clicked(self):
        """复位按钮点击事件"""
        drainage()
        # self.ui.ding_allBtn.setEnabled(True)
        self.ui.ding_halfBtn.setEnabled(True)
        self.ui.ding_halfBtn_2.setEnabled(False)
        # self.ui.resetBtn.setEnabled(False)
    @pyqtSlot()
    def on_quitBtn_clicked(self):
        """ 退出按钮 """
        if MessageBox.question(self, "提示", "是否要退出程序", "确定", "取消"):
            self.close()

    @pyqtSlot()
    def on_shutdownBtn_clicked(self):
        """ 关机按钮点击事件 """
        if MessageBox.question(self, "提示", "此操作将会关闭操作系统，是否继续", "继续", "取消"):
            if platform.platform().startswith("Linux"):
                os.system("sudo init 0")
            else:
                self.close()

    @pyqtSlot()
    def on_mClearBtn_clicked(self):
        """ 测试页面清除按钮 """
        # 清空label
        self.ui.srcImgLabel.clear()
        #self.ui.channelGLabel.clear()
        self.ui.channelRLabel.clear()
        # 清空表格
        self.ui.resultTableWidget.model().removeRows(0, self.ui.resultTableWidget.rowCount())
        self.TimerStatus.stop()
        self.temptask.stop1()
        self.thread.stop_sum()
        if self.VisionWait is not None and self.VisionWait == 8:
            self.thread.timervision.cancel()
            self.VisionWait = None
        self.stopLive()
        self.ui.lamp_2.clear()
        self.ui.label.clear()
        # RAD_OFF()

    def lamp_text(self):
        lamp_data = read_temp()  # 将AD值处理成温度
        global G_temp
        G_temp = lamp_data
        #print(lamp_data)
        self.ui.lamp_2.setText('LAMP:%.3f' % lamp_data + "℃")  # 改变当前温度窗口数据
        self.thread.start_worker1()
    def onThreadStatus(self, status: int):
        """检测状态"""
        if status == ThreadClass.T1:
            self.temptask.stop1()
            self.ui.lamp_2.setText("正在执行层析上样...")
            
        elif status == ThreadClass.T2:
            self.ui.lamp_2.setText("等待执行层析检测...")
            self.TimerStatus.start4()
            time.sleep(1)
            self.thread.wait_detect()

        elif status == ThreadClass.T3:
            self.ui.lamp_2.setText("开始层析检测")
            self.startLive()
            time.sleep(1)
            self.on_measureBtn_clicked()
            self.VisionWait = None
        elif status == 4:
            self.TimerStatus.start1()
            
        elif status == 5:
            self.TimerStatus.start2()
            
        elif status == 6:
            self.ui.label.setAlignment(Qt.AlignCenter)
            #self.ui.label.setText("降温")
            self.TimerStatus.start3()
            
        elif status == 7:
            #self.ui.label.setAlignment(Qt.AlignCenter)
            #self.ui.label.setText("预热")
            self.TimerStatus.start5()
            
        elif status == ThreadClass.T8:
            self.VisionWait = status
            
        elif status == ThreadClass.FINISHED:
            self.ui.lamp_2.setText("任务结束")
            
    def onTemp(self, status: float):
        """temp"""
        global g_temp
        # print(status )
        g_temp = status
        self.ui.lamp_2.setText('TEC:%.3f' % status + "℃")  # 改变当前温度窗口数据
        # print("temp")

    def onTimer(self, status: int):
        """状态计时器"""
        global G_time
        G_time = status
        times = status
        min = times / 60
        s = times % 60
        self.ui.label.setAlignment(Qt.AlignCenter)
        self.ui.label.setText("计时： %d : %d" % (min, s))
        
    @pyqtSlot()
    def on_lamp_Btn_clicked(self):
        """状态列表变化按钮"""
        self.ui.lamp_2.setAlignment(Qt.AlignCenter)
        self.ui.lamp_2.setText("开始...")
        self.ui.label.setAlignment(Qt.AlignCenter)
        self.ui.label.setText("预热")
        if MessageBox.question(self, "提示", "请确认芯片已插入", "确定", "取消"):
            self.ui.lamp_2.setText("正在执行等温扩增")
            time.sleep(0.5)
            #self.start_text()
            self.temptask.start1()
            time.sleep(1)
            self.thread.start_worker1()
            RAD_ON()

    @pyqtSlot()
    def on_measureBtn_clicked(self):
        """ 测量页面检测按钮点击事件 """
        # 检查是否输入编号
        testNum = self.ui.numLineEdit.text()
        if testNum is None or testNum.strip() == "":
            btnVal = MessageBox.warning(self, "警告", "未检测到测试编号，是否继续", "继续", "取消")
            if btnVal == 0:
                return
        # 初始化结果显示,清空表格
        self.ui.resultTableWidget.model().removeRows(0, self.ui.resultTableWidget.rowCount())
        # 由于要获取图片，先关闭预览
        self.stopLive()
        # 清理界面
        # self.on_mClearBtn_clicked()
        # 开灯
        self.led.setOn()
        time.sleep(0.5)
        # 获取图片并处理
        frame = self.getImg()
        # 取图后关灯
        self.led.setOff()
        if frame is not None:
            # 保存获取到的图片
            # 获取时间
            filename = f"{QDateTime.currentDateTime().toString('yyyy_MM_dd_hh_mm_ss')}_{testNum}.jpg"
            cv.imwrite(os.path.join(self.savePath[0], filename), frame)
            self.processImg(frame)
        else:
            MessageBox.warning(self, "警告", "获取图像失败！", "关闭")
    @pyqtSlot()
    def on_previewBtn_clicked(self):
        """ 预览按钮 """
        if self.ui.previewBtn.text() == "预览":
            # 并开启预览功能
            self.startLive()
        elif self.ui.previewBtn.text() == "停止":
            self.stopLive()

    @pyqtSlot()
    def on_temp_downBtn_clicked(self):
        """ 测温按钮 """
        if self.ui.temp_downBtn.text() == "测温":
            self.start_temp()
        elif self.ui.temp_downBtn.text() == "停止":
            self.stop_temp()


    @pyqtSlot()
    def on_captureImgBtn_clicked(self):
        """ 抓图按钮 """
        # 先停止预览
        status = False
        if self.liveTimer is not None and self.liveTimer.isActive():
            status = True
        self.stopLive()
        # 获取图片
        img = self.getImg()
        if img is not None:
            filename = f"{QDateTime.currentDateTime().toString('yyyy_MM_dd_hh_mm_ss')}.jpg"
            cv.imwrite(os.path.join(self.savePath[1], filename), img)
            MessageBox.information(self, "提示", "保存成功", "关闭")
        # 获取图片后还原相机状态
        if status:
            self.startLive()

    @pyqtSlot()
    def on_qQueryBtn_clicked(self):
        """ 查询页面查询按钮点击事件 """
        beginDate = self.ui.qBeginDate.date()
        endDate = self.ui.qEndDate.date()
        if endDate < beginDate:
            MessageBox.warning(self, "警告", "查询的结束时间不能小于开始时间", "关闭")
            return
        beginDate = beginDate.toString("yyyy/MM/dd") + " 00:00:00"
        endDate = endDate.toString("yyyy/MM/dd") + " 23:59:59"
        try:
            self.historyList = self.dao.select(beginDate, endDate)
            temp = []
            table = self.ui.qTableWidget_1
            table.model().removeRows(0, table.rowCount())
            for record in self.historyList:
                testTime = QDateTime(record.createTime).toString("yyyy年MM月dd日 HH:mm:ss")
                numberTimeStr = "{}_{}".format(record.testNum, testTime)
                if numberTimeStr not in temp:
                    print(testTime, record.testNum)
                    temp.append(numberTimeStr)
                    table.insertRow(table.rowCount())
                    # 填充时间
                    timeItem = QTableWidgetItem(testTime)
                    timeItem.setTextAlignment(Qt.AlignCenter)
                    table.setItem(table.rowCount() - 1, 0, timeItem)
                    # 编号
                    numItem = QTableWidgetItem(record.testNum)
                    numItem.setTextAlignment(Qt.AlignCenter)
                    table.setItem(table.rowCount() - 1, 1, numItem)
        except Exception as e:
            log.error(e)

    @pyqtSlot(int, int, int, int)
    def on_qTableWidget_1_currentCellChanged(self, row, col, val1, val2):
        timeCell = self.ui.qTableWidget_1.item(row, 0)
        numberCell = self.ui.qTableWidget_1.item(row, 1)
        timeVal, numberVal = "", ""
        if timeCell is not None:
            timeVal = timeCell.text()
        if numberCell is not None:
            numberVal = numberCell.text()
        table = self.ui.qTableWidget_2
        table.model().removeRows(0, table.rowCount())
        for data in self.historyList:
            if QDateTime(data.createTime).toString("yyyy年MM月dd日 HH:mm:ss") == timeVal and data.testNum == numberVal:
                print(data)
                table.insertRow(table.rowCount())
                # 编号
                numItem = QTableWidgetItem(str(data.serialNum))
                numItem.setTextAlignment(Qt.AlignCenter)
                table.setItem(table.rowCount() - 1, 0, numItem)
                # R值
                rItem = QTableWidgetItem(str(data.rVal))
                rItem.setTextAlignment(Qt.AlignCenter)
                table.setItem(table.rowCount() - 1, 1, rItem)
                # G值
                # gItem = QTableWidgetItem(str(data.gVal))
                # gItem.setTextAlignment(Qt.AlignCenter)
                # table.setItem(table.rowCount() - 1, 2, gItem)

    @pyqtSlot()
    def on_qExportBtn_clicked(self):
        """ 查询页面导出按钮点击事件 """
        direct = QFileDialog.getExistingDirectory(self, "保存到", self.getDesktopPath())
        if direct is not None and direct.strip() != "":
            # 导出文件的文件名称
            beginDate = self.ui.qBeginDate.date().toString("yyyy_MM_dd")
            endDate = self.ui.qEndDate.date().toString("yyyy_MM_dd")
            fileName = os.path.join(direct, "ifir100_{}-{}.xlsx".format(beginDate, endDate))
            # 生成导出的数据
            dataList = [['测试编号', '序号', 'R', '时间']]
            for data in self.historyList:
                testNum = data.testNum
                serialNum = data.serialNum
                rVal = data.rVal
                #gVal = data.gVal
                testTime = QDateTime(data.createTime).toString("yyyy/MM/dd HH:mm:ss")
                dataList.append([testNum, serialNum, rVal, testTime])
            # 导出数据
            ExcelUtil.exportData(fileName, dataList)
            MessageBox.information(self, "提示", "数据导出成功", "关闭")

    @pyqtSlot()
    def on_qClearBtn_clicked(self):
        """ 清空数据库中的数据 """
        beginDate = self.ui.qBeginDate.date()
        endDate = self.ui.qEndDate.date()
        if endDate < beginDate:
            MessageBox.warning(self, "警告", "结束时间不能小于开始时间", "关闭")
            return
        # 编辑时间为起始时间的0点至结束时间的23点59分59秒
        beginDateStr = beginDate.toString("yyyy/MM/dd") + " 00:00:00"
        endDateStr = endDate.toString("yyyy/MM/dd") + " 23:59:59"
        # 删除操作的状态，默认是未删除
        status = False
        msg = "是否要删除时间在{}和{}的全部数据，数据删除后将无法再恢复！" \
            .format(beginDate.toString("yyyy/MM/dd"), endDate.toString("yyyy/MM/dd"))
        if MessageBox.question(self, "提示", msg, "是", "否") == 1:
            try:
                self.dao.deleteByTime(beginDateStr, endDateStr)
                status = True
            except Exception as e:
                log.error(e)
        if status:
            self.ui.qTableWidget_1.model().removeRows(0, self.ui.qTableWidget_1.rowCount())
            self.ui.qTableWidget_1.setRowCount(3)
            self.ui.qTableWidget_2.model().removeRows(0, self.ui.qTableWidget_2.rowCount())
            self.ui.qTableWidget_2.setRowCount(3)
            MessageBox.information(self, "提示", "数据删除成功", "关闭")


class ThreadClass(QThread):
    runstatus = pyqtSignal(int)
    T1 = 1
    T2 = 2
    T3 = 3
    T4 = 4
    T5 = 5
    T6 = 6
    T7 = 7
    T8 = 8
    FINISHED = 0XFFFF
    def __init__(self, parent:QObject = None) -> None:
        super(ThreadClass, self).__init__(parent)
        self.is_running = True
        self.TimerStatus = TimerStatus()
        #self.num = 30
        # 定义温控状态
        self.PRE_HEAT = 'PRE_HEAT'
        self.SOAK_65 = 'SOAK_65'
        self.HOT = 'HOT'
        self.SOAK_85 = 'SOAK_85'
        self.COOL = 'COOL'
        self.SOAK_4 = 'SOAK_4'
        self.status = self.PRE_HEAT
        # 设置temp点
        self.PRE65 = 65
        self.PRE = 115
        self.SP65 = 65 #82.5
        self.SP85 = 80
        self.SP4 = 15
        # PID
        self.dt = 0.01  # 循环时长
        self.max = 10  # 操作变量最大值
        self.min = -10  # 操作变量最小值
        self.Kp = 100  # 比例增益100
        self.Ki = 3  # 微分增益3
        self.Kd = 13  # 积分增益15
        self.error = 0  # 当前误差
        self.error_1 = 0  #上次误差
        self.error_2 = 0  # 上上次误差
        self.pre_output = 0  #上次的输出值
        self.integral = 0

    def run(self):
        self.status = self.PRE_HEAT
        ThreadClass.T4 = 4
        ThreadClass.T5 = 5
        ThreadClass.T6 = 6
        ThreadClass.T7 = 7
        self.state()
        #print("finish")
        
    def pid_control(self, t, setpoint):
        #pid = PID(1, 10, -10, 0.3, 0.05, 0.65)# 0.3, 0.05, 0.65
        #setpoint = self.num
        val = t
        inc = self.calculate(setpoint, val, t)#新的目标值
        pwm_out = inc*10
        # print("temp:%f inc:%f pwm:%f" % (t, inc, pwm_out))
        # val += inc
        if 55 < t <= 70:
            if inc >= 0:
                GPIO.output(TERMINAL1, 0)
                pwm = GPIO.PWM(TERMINAL2, 1000)
                pwm.start(pwm_out)#以占空比为百分之十的模式启动pwm波
                time.sleep(0.1)
                stop(pwm)
            elif inc < 0:
                GPIO.output(TERMINAL1, 0)#在38号针脚上创建一个1000Hz的PWM波
                GPIO.output(TERMINAL2, 0)
                #pwm.start(-(pwm_out))#以占空比为百分之十的模式启动pwm波
                #time.sleep(1)
                #stop(pwm)
        elif t > 70:
            if inc >= 0:
                GPIO.output(TERMINAL1, 0)
                pwm = GPIO.PWM(TERMINAL2, 1000)
                pwm.start(pwm_out)#以占空比为百分之十的模式启动pwm波
                time.sleep(0.1)
                stop(pwm)
            elif inc < 0:
                GPIO.output(TERMINAL2, 0)
                GPIO.output(TERMINAL1, 0)
        elif t <= 55:
            if inc >= 0:
                GPIO.output(TERMINAL1, 0)
                pwm = GPIO.PWM(TERMINAL2, 1000)
                pwm.start(pwm_out)#以占空比为百分之十的模式启动pwm波
                time.sleep(0.1)
                stop(pwm)
            elif inc < 0:
                GPIO.output(TERMINAL1, 1)#在38号针脚上创建一个1000Hz的PWM波
                GPIO.output(TERMINAL2, 0)
                #GPIO.output(TERMINAL1, 1)#在38号针脚上创建一个1000Hz的PWM波
                #pwm.start(-(pwm_out))#以占空比为百分之十的模式启动pwm波
                #time.sleep(3)
                #stop(pwm)
                
    def pid_control_hot(self, t, setpoint):
        #pid = PID(1, 10, -10, 0.3, 0.05, 0.65) #0.3, 0.05, 0.65
        #setpoint = self.num
        val = t
        inc = self.calculate(setpoint, val, t)#新的目标值
        pwm_out = inc * 10
        # print("temp:%f inc:%f pwm:%f" % (t, inc, pwm_out))
        #val += inc
        
        if inc >= 0:
            GPIO.output(TERMINAL1, 0)
            pwm = GPIO.PWM(TERMINAL2, 1000)
            pwm.start(pwm_out)#以占空比为百分之十的模式启动pwm波
            time.sleep(0.1)
            stop(pwm)
        elif inc < 0:
            GPIO.output(TERMINAL1, 0)#在38号针脚上创建一个1000Hz的PWM波
            GPIO.output(TERMINAL2, 0)
            #pwm.start(-(pwm_out))#以占空比为百分之十的模式启动pwm波
            #time.sleep(1)
            #stop(pwm)
        
    # 状态迁移
    def to_65(self):
        self.status = self.SOAK_65
        global G_time
        G_time = 60
        
    def to_hot(self):
        self.status = self.HOT

    def to_85(self):
        self.status = self.SOAK_85
        global G_time
        G_time = 60
        
    def start_cool(self):
        self.status = self.COOL

    def start_worker1(self):
        temp = read_temp()
        if temp is not None:
            try:
                self.is_running = True
                #self.num = 65
                self.start()
            except Exception as e:
                print("DS18B20-None", e)
        #self.ui.temp_upBtn.setEnabled(False)
        
    def start_worker2(self):
        time.sleep(1)
        self.state2()
        self.stop_run()
      
    def stop_worker(self):
        self.is_running = False
        print('stopping temp...')
        self.runstatus.emit(ThreadClass.T1)
        self.state2()
        self.stop_run()
        #time.sleep(1)
        #self.terminate()
        
    def stop_run(self):
        time.sleep(1)
        self.is_running = False
        print("stopping thread...")
        self.runstatus.emit(ThreadClass.T2)
        
        
        #self.terminate()
        
    def stop_sum(self):
        self.is_running = False
        print("stopping threadsum...")
        #time.sleep(1)
        #self.terminate()
        
    def state(self):
        setup()
        print('Starting thread...')
        status = 10
        global G_time
        G_time = 50
        while self.is_running:
            t = self.setText()  # print('温度:%2.2f'%t)
            # 65摄氏度预热
            if self.status == self.PRE_HEAT:
                self.pid_control(t, self.PRE65)  # self.PRE
                # if abs(t - 65) < 1:
                if t >= 65:
                    self.runstatus.emit(ThreadClass.T7)
                    ThreadClass.T7 = 0
                    timerp = self.timercool()
                    if timerp == 0:
                        self.to_65()
                    #self.timerPRE = Timer(45, self.to_65) #45
                    #self.timerPRE.start()
                    
            # 65摄氏度保持
            if self.status == self.SOAK_65:  # self.SOAK_65
                self.pid_control(t, self.SP65)  # self.SP65
                if abs(t - 65) < 2:
                    self.runstatus.emit(ThreadClass.T4)
                    ThreadClass.T4 = 0
                    #self.timerPRE.cancel()
                    timer = self.timercool()
                    if timer == 0:
                        self.to_85()
                    #self.timer = Timer(10, self.to_hot) #1250
                    #self.timer.start()
                    
            # 80摄氏度预热
            #elif self.status == self.HOT:
                #self.runstatus.emit(ThreadClass.T7)
                #ThreadClass.T7 = 0
                #self.pid_control_hot(t, self.SP85)
                #if t >= 66:
                    #self.timer.cancel()
                    #self.timeHOT = Timer(40, self.to_85) #100
                    #self.timeHOT.start()
                    
            # 80摄氏度保持
            elif self.status == self.SOAK_85:
                self.pid_control_hot(t, self.SP85)
                if abs(t - 80) < 1:
                    self.runstatus.emit(ThreadClass.T5)
                    ThreadClass.T5 = 0
                    #self.timeHOT.cancel()
                    timers = self.timercool()
                    if timers == 0:
                        self.start_cool()
                        #self.stop_worker()
                    #self.timers = Timer(120, self.start_cool) #240
                    #self.timers.start()
                    #self.stop_run()
                    
            # 降温至20摄氏度
            elif self.status == self.COOL:
                self.pid_control(t, self.SP4)
                if t < 25:
                    self.runstatus.emit(ThreadClass.T6)
                    ThreadClass.T6 = 0
                    time.sleep(0.1)
                    tc = self.timercool()
                    #print(tc)
                    if tc == 0:
                        self.stop_worker()
                    #self.timers.cancel()
                    #self.state2()
                    #self.stop_run()    
        GPIO.output(TERMINAL1, 0)
        GPIO.output(TERMINAL2, 0)
    def state2(self):
        titration()
        time.sleep(10)
        half_restart()
        time.sleep(1)
        drainage()
        
    def state3(self):
        # time.sleep(6)
        self.runstatus.emit(ThreadClass.T3)
        
    def setText(self):
        global g_temp
        t =g_temp
        return t
    def timercool(self):
        time.sleep(0.001)
        global G_time       
        tc = G_time
        return tc
    def wait_detect(self):
        self.timervision = Timer(10, self.state3)
        self.timervision.start()
        self.runstatus.emit(ThreadClass.T8)
        
    def calculate(self, setPoint, pv, t):
        # 其中 pv:process value 
        error = setPoint - t  # 误差（设定值与实际值的差值）
        Pout = self.Kp * error   # 比例项 Kp * (e(t)-e(t-1))
        self.integral += error
        print(self.integral)
        if (self.integral > 6000):
            self.integral = 6000
        elif (self.integral < -6000):
            self.integral = -6000
        
        # Iout = self.Ki * self.integral  # 积分项 Ki * e(t)
        Dout = self.Kd * (error - self.error_1)  # 微分项 Kd * (e(t)-2*e(t-1)+e(t-2))
        output = (Pout + self.integral + Dout)/1000  # + self.pre_output
        # 新的目标值  位置式PID：u(t) = Kp*(e(t)-e(t-1)) + Ki*e(t) + Kd*(e(t)-2*e(t-1)+e(t-2)) + u(t-1）
        # print(output)
        if (output > self.max):
            output = self.max
        elif (output < self.min):
            output = self.min
        self.pre_output = t
        self.error_2 = self.error_1  # e(k-2) = e(k) ,进入下一次计算使用
        self.error_1 = error  # e(k-1) = e(k)
        return output
    

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow()
    if platform.platform().startswith("Windows-10"):
        win.show()
    else:
        win.showFullScreen()
    sys.exit(app.exec())