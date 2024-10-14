# -*- coding: utf-8 -*-
import sys
import os
os.environ['MPLCONFIGDIR'] = os.getcwd() + "/configs/"
import matplotlib.pyplot as plt
import platform
import time
import cv2 as cv
import numpy as np
from PyQt5.QtWidgets import QApplication, QMainWindow, QTableWidgetItem, QAbstractItemView, QFileDialog, QMessageBox
from PyQt5.QtCore import pyqtSlot, QTimer, QDateTime, QDate, Qt, QObject, QEvent, QStandardPaths
from PyQt5.QtGui import QMouseEvent
from Ui_MainWindow import Ui_MainWindow
from utils import ImgUtils, ExcelUtil
from logFactory import LoggerFactory
envpath = '/home/pi/文档/venv/lib/python3.9/site-packages/cv2/qt/plugins/platforms'
os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = envpath


log = LoggerFactory.getLogger()


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        # 挂载UI组件
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.uiInit = True
        # 创建缓存文件夹
        self.cacheDir, self.captureDir = '', ''
        self.__createCacheDir__()
        # 检测时间
        self.testTime = None
        # 相机预览时定时获取图片并显示的定时器
        self.liveTimer = None
        # 当前使用的相机
        self.camera = None
        # 最近一张图片
        self.lastFrame = None
        # 初始化相机
        self.__initCamera__()
        # 记录鼠标框选的起始位置
        self.mousePos0 = None
        # 鼠标选取的区域(x, y, w, h)
        self.mousePos1 = None
        # 绑定预览窗口的鼠标移动事件
        self.ui.srcImgLabel.installEventFilter(self)
        # 初始化UI
        self.__initUI__()

    def eventFilter(self, obj: QObject, e: QEvent):
        """ 记录鼠标在预览窗口上的轨迹 """
        if e.type() in (QEvent.MouseButtonPress, QEvent.MouseMove, QEvent.MouseButtonDblClick) and obj == self.ui.srcImgLabel:
            me = QMouseEvent(e)
            #scaling = 2.5
            scaling = 1
            if e.type() == QEvent.MouseButtonPress:
                # 记录鼠标移动的起始位置
                self.mousePos0 = [round(me.x() * scaling), round(me.y() * scaling)]
                self.mousePos1 = self.mousePos0
            elif e.type() == QEvent.MouseMove:
                self.mousePos1 = [round(me.x() * scaling), round(me.y() * scaling)]
                if self.uiInit and self.mousePos0 is not None and self.mousePos1 is not None:
                    # 更新图像裁切的位置和尺寸
                    x0, y0 = self.mousePos0
                    x1, y1 = self.mousePos1
                    self.ui.x0Slider.setValue(x0)
                    self.ui.y0Slider.setValue(y0)
                    self.ui.x1Slider.setValue(x1)
                    self.ui.y1Slider.setValue(y1)
            elif e.type() == QEvent.MouseButtonDblClick:
                self.mousePos0 = None
                self.mousePos1 = None
                if self.uiInit:
                    # 清空图像裁切的位置和尺寸
                    self.ui.x0Slider.setValue(0)
                    self.ui.y0Slider.setValue(0)
                    self.ui.x1Slider.setValue(0)
                    self.ui.y1Slider.setValue(0)
                    self.ui.widthLabel.setNum(0)
                    self.ui.heightLabel.setNum(0)
        return super(MainWindow, self).eventFilter(obj, e)

    def __initCamera__(self):
        """ 初始化相机参数 """
        print("init camera...")
        # 清空列表
        self.ui.cameraListComboBox.clear()
        # 打开第一个相机
        #self.startLive(0)   # 打开第一个相机

        cnt = 0
        for device in range(0, 10):
            stream = cv.VideoCapture(device)
            grabbed = stream.grab()
            stream.release()
            if grabbed:
                self.ui.cameraListComboBox.addItem(f"device_{cnt}")
            else:
                break
            cnt = cnt + 1

        if cnt > 0:
            # 打开第一个相机
            self.startLive(0)
        else:
            QMessageBox.warning(self, "警告", "未发现图像采集设备，是否要关闭程序", QMessageBox.Yes | QMessageBox.No)

    def __initUI__(self):
        # 初始化表格样式及表头数据
        self.__initTable__()
        # 把窗口移动到屏幕的中间
        self.move(0, 0)

    def __initTable__(self):
        """ 初始化查询表格 """
        # 表1 [时间， 编号]
        # table1 = self.ui.qTableWidget_1
        # # # 将表格变为禁止编辑
        # table1.setEditTriggers(QAbstractItemView.NoEditTriggers)
        # # 设置表格整行选中
        # table1.setSelectionBehavior(QAbstractItemView.SelectRows)
        # table1.setColumnWidth(0, 260)

    def __createCacheDir__(self):
        """ 创建保存文件的目录, 若存在则删除 """
        self.cacheDir = os.path.join(self.getDesktopPath(), "IFIR_100_TMP", QDate.currentDate().toString("yyyy-MM-dd"))
        if not os.path.exists(self.cacheDir):
            # 创建缓存文件夹
            os.makedirs(self.cacheDir)
        self.captureDir = os.path.join(self.getDesktopPath(), "IFIR_100_TMP", "capture")
        if not os.path.exists(self.captureDir):
            # 创建缓存文件夹
            os.mkdir(self.captureDir)

    def startLive(self, index):
        """ 实时预览图片 """
        self.camera = cv.VideoCapture(index+cv.CAP_DSHOW)
        #self.camera = cv.VideoCapture(0)
        # 打开相机
        if self.camera.isOpened():
            self.camera.set(cv.CAP_PROP_FRAME_WIDTH, 1600)
            self.camera.set(cv.CAP_PROP_FRAME_HEIGHT, 1200)
            exposure = self.camera.get(cv.CAP_PROP_EXPOSURE)
            self.ui.exposureSlider.setValue(int(exposure))
            # 开启定时器进行图片刷新
            if self.liveTimer is None:
                self.liveTimer = QTimer(self)
                self.liveTimer.timeout.connect(self.onCameraLive)
            if not self.liveTimer.isActive():
                self.liveTimer.start(20)

    def getDesktopPath(self):
        """ 获取桌面路径 """
        return QStandardPaths.writableLocation(QStandardPaths.DesktopLocation)

    def processImg(self, frame):
        """ 图片处理 """
        # cv.imshow("", frame)
        # 截取有效部分
        if frame is not None:
            # 显示获取到的图片
            ImgUtils.liveRGBImg(frame, self.ui.srcImgLabel)
            frame = ImgUtils.clahe(frame) # clahe图像增强
            # 分离通道
            chB, chG, chR = cv.split(frame)
            # white_img = np.full(chR.shape, 255, dtype=np.uint8)
            # chR = white_img - chR
            #
            # kong = np.full(chG.shape, 255, dtype=np.uint8)
            # chG = kong - chG
            # cv.imshow("r", chR)
            # cv.imshow("G", chG)
            # 对R通道进行处理
            peaksR, projectionImgR = ImgUtils.processImgChannel(chR, "R", (0, 0, 255))
            print("peaksR:", peaksR)
            ImgUtils.liveRGBImg(projectionImgR, self.ui.channelRLabel)
            # 对G通道进行处理
            peaksG, projectionImgG = ImgUtils.processImgChannel(chG, "G", (0, 255, 0))
            print("peaksG:", peaksG)
            ImgUtils.liveRGBImg(projectionImgG, self.ui.channelGLabel)
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
            self.showResult(peaksR, peaksG)
            # 保存数据
            self.saveData()

    def showResult(self, peaksR, peaksG):
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
            gVal = peaksG[i].avePix
            # rVal = peaksR[i].height
            # gVal = peaksG[i].height
            # 填充C值
            rItem = QTableWidgetItem(str(rVal))
            rItem.setTextAlignment(Qt.AlignCenter)
            table.setItem(i, 1, QTableWidgetItem(rItem))
            # 填充T值
            gItem = QTableWidgetItem(str(gVal))
            gItem.setTextAlignment(Qt.AlignCenter)
            table.setItem(i, 2, QTableWidgetItem(gItem))

    def saveData(self):
        """ 保存测量结果 """
        # 获取数据行数
        table = self.ui.resultTableWidget
        rows = table.rowCount()
        # 检测时间
        testTime = self.testTime.toString('yyyy/MM/dd hh:mm:ss')
        # 导出文件的文件名称
        filename = os.path.join(self.cacheDir, f"{self.testTime.toString('yyyy-MM-dd')}.xlsx")
        # 生成导出的数据
        dataList = [[testTime, '', ''], ['序号', 'R', 'G']]
        for row in range(rows):
            dataList.append([table.item(row, 0).text(), table.item(row, 1).text(), table.item(row, 2).text()])
        # 导出数据
        if os.path.exists(filename):
            ExcelUtil.appendData(filename, dataList)
        else:
            ExcelUtil.exportData(filename, dataList)

    @pyqtSlot()
    def onCameraLive(self):
        ret, frame = self.camera.read()
        if ret:
            # 旋转180度后返回
            self.lastFrame = cv.flip(frame, -1)
            # 裁取要显示的部分
            img = None
            if self.mousePos1 is not None:
                # 绘制图片
                img = self.lastFrame.copy()
                cv.rectangle(img, self.mousePos0, self.mousePos1, (0, 255, 0), 3)
            else:
                img = self.lastFrame
            ImgUtils.liveRGBImg(img, self.ui.srcImgLabel)

    @pyqtSlot()
    def on_mClearBtn_clicked(self):
        """ 测试页面清除按钮 """
        # 清空label
        self.ui.channelGLabel.clear()
        self.ui.channelRLabel.clear()
        # 清空表格
        self.ui.resultTableWidget.model().removeRows(0, self.ui.resultTableWidget.rowCount())

    @pyqtSlot()
    def on_measureBtn_clicked(self):
        """ 测量页面检测按钮点击事件 """
        # 初始化结果显示,清空表格
        self.ui.resultTableWidget.model().removeRows(0, self.ui.resultTableWidget.rowCount())
        # 清理界面
        if self.lastFrame is not None and self.mousePos1 is not None:
            self.testTime = QDateTime.currentDateTime()
            x0, y0 = self.mousePos0
            x1, y1 = self.mousePos1
            img = self.lastFrame[y0:y1, x0:x1]
            # img = self.lastFrame
            # 保存获取到的图片
            # 获取时间
            filename = f"{self.testTime.toString('hh-mm-ss')}.jpg"
            
            #filename = '/home/pi/Desktop/IFIR_100_TMP/2023-04-11/hh-mm-ss.jpg'
            #cv.imwrite( filename, img)
            cv.imwrite(os.path.join(self.cacheDir, filename), img)
            self.processImg(img)

    @pyqtSlot()
    def on_captureImgBtn_clicked(self):
        """ 抓图按钮 """
        if self.lastFrame is not None:
            filename = QDateTime.currentDateTime().toString("yyyy_MM_dd_hh_mm_ss")
            filename += ".jpg"
            cv.imwrite(os.path.join(self.captureDir, filename), self.lastFrame)
            QMessageBox.information(self, "提示", "保存成功", QMessageBox.Ok)

    @pyqtSlot(int)
    def on_cameraListComboBox_currentIndexChanged(self, cameraIndex):
        """ 测试页面清除按钮 """
        if cameraIndex > -1:
            # 暂停定时器
            if self.liveTimer is not None and self.liveTimer.isActive():
                self.liveTimer.stop()
            # 重新打开相机
            self.startLive(cameraIndex)

    @pyqtSlot(int)
    def on_exposureSlider_valueChanged(self, val):
        """ 调整相机亮度 """
        if self.camera is not None and self.camera.isOpened():
            self.camera.set(cv.CAP_PROP_EXPOSURE, val)

    @pyqtSlot(int)
    def on_x0Slider_valueChanged(self, val):
        """ 调整图像截取的起始位置x """
        if self.mousePos0 is not None:
            self.mousePos0[0] = val
            self.ui.widthLabel.setNum(abs(self.mousePos1[0] - self.mousePos0[0]))

    @pyqtSlot(int)
    def on_y0Slider_valueChanged(self, val):
        """ 调整图像截取的起始位置y """
        if self.mousePos0 is not None:
            self.mousePos0[1] = val
            self.ui.heightLabel.setNum(abs(self.mousePos1[1] - self.mousePos0[1]))

    @pyqtSlot(int)
    def on_x1Slider_valueChanged(self, val):
        """ 调整图像截取的宽度 """
        if self.mousePos1 is not None:
            self.mousePos1[0] = val
            self.ui.widthLabel.setNum(abs(self.mousePos1[0] - self.mousePos0[0]))

    @pyqtSlot(int)
    def on_y1Slider_valueChanged(self, val):
        """ 调整图像截取的高度 """
        if self.mousePos1 is not None:
            self.mousePos1[1] = val
            self.ui.heightLabel.setNum(abs(self.mousePos1[1] - self.mousePos0[1]))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MainWindow()
   # if platform.platform().startswith("linux"):
      #  win.show()
   # else:
       # win.showFullScreen()
    win.show()
    sys.exit(app.exec())
