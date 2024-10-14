# -*- coding: utf-8 -*-
import cv2 as cv
import time
import numpy as np
from PyQt5.QtWidgets import QLabel
from PyQt5.QtGui import QImage, QPixmap
import os
import xlrd
os.environ['MPLCONFIGDIR'] = os.getcwd() + "/configs/"
import matplotlib.pyplot as plt
# from scipy.signal import savgol_filter
from scipy import signal
from PyQt5.QtCore import QDateTime


class Peak:
    """
        峰值的信息
        @param index    峰值的位置
        @param left     峰的起始点
        @param right    峰的结束位置
        @param width    峰的宽度
        @param height   峰的高度
    """
    def __init__(self, index, left=-1, right=-1, width=0, height=0):
        self.index = index
        self.left = left
        self.right = right
        self.width = width
        self.height = height
        self.sumPix = 0
        self.mack = 0
        self.avePix = 0

    def __repr__(self):
        return str({
            "width": self.width,
            "height": self.height,
            "index": self.index,
            "left": self.left,
            "right": self.right,
            "sumPix": self.sumPix,
            "avePix": self.avePix
        })


def liveRGBImg(img, label: QLabel):
    """ 将RGB图像显示到QLabel上 """
    size = label.size()
    # label的上下左右border各为3个像素
    width = size.width() - 6
    height = size.height() - 6
    img = cv.cvtColor(img, cv.COLOR_BGR2RGB)
    # pyqt5转换成自己能放的图片格式
    _image = QImage(img[:], img.shape[1], img.shape[0], img.shape[1] * 3, QImage.Format_RGB888)
    # 设置图片显示
    label.setPixmap(QPixmap(_image).scaled(width, height))


def liveGrayImg(img, label: QLabel):
    """ 将单通道8位图像显示到QLabel上 """
    size = label.size()
    # label的上下左右border各为3个像素
    width = size.width() - 6
    height = size.height() - 6
    # pyqt5转换成自己能放的图片格式
    _image = QImage(img[:], img.shape[1], img.shape[0], img.shape[1], QImage.Format_Indexed8)
    # 设置图片显示
    label.setPixmap(QPixmap(_image).scaled(width, height))


def normalize(srcImg, alpha=None, beta=None, norm_type=None):
    """ 对单通道图片进行归一化 """
    normImg = np.zeros(srcImg.shape, dtype=np.uint8)
    cv.normalize(srcImg, normImg, alpha, beta, norm_type)
    return normImg


def getPeaks(colPixAve: [], minHeight=5):
    """ 求一组数据中的峰值点 """
    #filterVal = signal.savgol_filter(colPixAve, 5, 1, mode='nearest')
    # 一阶导数
    col_diff = np.diff(colPixAve)
    col_diff = signal.savgol_filter(col_diff, 51, 1, mode='nearest')
    tempList = []
    for i in range(2, len(col_diff) - 2):  # 遍历一阶导数
        L_v = col_diff[i - 1]
        R_v = col_diff[i + 1]
        num = 0
        if L_v > 0 and R_v < 0:  # 寻找过零点
            R_p = i
            L_p = i
            num = num + 1
            for j in range(i, len(col_diff) - 1):  # 寻找过零点右侧最低点坐标
                if col_diff[j] > col_diff[j + 1]:
                    R_p = j + 1
                else:
                    break
            right_p = R_p
            R_p = i + 2 * (R_p - i) + 1
            if R_p > len(col_diff):
                R_p = len(col_diff)

            for j in range(i, 2, -1):  # 寻找过零点左侧最高点坐标
                if col_diff[j] < col_diff[j - 1]:
                    L_p = j - 1
                else:
                    break
            left_p = L_p
            L_p = i - 2 * (i - L_p) - 1
            if L_p < 1:
                L_p = 1
            # 计算峰宽
            peak_weidth = R_p - L_p
            #peak_weidth = right_p - left_p
            # 计算峰高
            peak_height = colPixAve[i] - 0.5 * (colPixAve[R_p] + colPixAve[L_p])
            if peak_height > minHeight:
                peak = Peak(i)
                peak.left = L_p
                peak.right = R_p
                peak.left = left_p - 10
                peak.right = right_p + 10
                peak.width = round(peak_weidth, 2)
                peak.height = round(peak_height, 2)
                # print(peak)
                tempList.append(peak)
    # 过滤相邻的点
    size = len(tempList)
    # print("temp peak list size: ", size)
    peaks = []
    if size > 0:
        for i in range(size):
            if len(peaks) > 0:
                # 比较当前的峰和peaks里最后一个峰的差值
                tempPeak = tempList[i]
                peak = peaks[len(peaks) - 1]
                if tempPeak.index - peak.index >= 5:
                    peaks.append(tempPeak)
                else:
                    # 比较两个峰那个更高
                    if tempPeak.height > peak.height:
                        peaks[len(peaks) - 1] = tempPeak
            else:
                peaks.append(tempList[i])
    return peaks


def drawLine(peaks: [], colPixAve):
    """ 绘制曲线图 """
    filterVal = signal.savgol_filter(colPixAve, 5, 1, mode='nearest')
    # 一阶导数
    col_diff = np.diff(filterVal)
    col_diff = signal.savgol_filter(col_diff, 5, 1, mode='nearest')
    peakXList, peakYList = [], []
    xList, yList = [], []
    for peak in peaks:
        # 左边点
        xList.append(peak.left)
        yList.append(round(filterVal[peak.left], 2))
        # 右边点
        xList.append(peak.right)
        yList.append(round(filterVal[peak.right], 2))
        # 峰值点
        peakXList.append(peak.index)
        peakYList.append(round(col_diff[peak.index], 2))
    # print("[", len(xList), "]", xList)
    # print("[", len(yList), "]", yList)
    # print(len(peakXList))
    # 绘制原始图
    # 基线校正
    baseline = signal.savgol_filter(filterVal, 71, 1, mode='nearest')
    baseline_correct = filterVal - baseline
    plt.subplot(3, 1, 1)
    plt.plot(baseline_correct)
    plt.title("初始值")
    # 绘制滤波后的图
    plt.subplot(3, 1, 2)
    plt.plot(filterVal)
    plt.title("平滑后")
    # plt.scatter(xList, yList, c="red")
    plt.plot(xList, yList, c="red")
    # 绘制倒数图
    plt.subplot(3, 1, 3)
    plt.plot(col_diff)
    plt.title("倒数")
    plt.scatter(peakXList, peakYList, c="purple")
    plt.show()


def getMaxContour(contours):
    """ 查找最大的轮廓 """
    if len(contours) > 0:
        maxArea, maxContour = 0, None
        for contour in contours:
            contourArea = cv.contourArea(contour)
            if contourArea > maxArea:
                maxArea = contourArea
                maxContour = contour
        return maxContour, maxArea
    return None, None


def countPixValue(grayImg):
    """ 计算灰度图的像素值 """
    rows, cols = grayImg.shape
    sumPixVal = 0
    for row in range(rows):
        for col in range(cols):
            sumPixVal += grayImg[row, col]
    return sumPixVal


def drawText(img, point: tuple, text, color=(255, 255, 255)):
    fontFace = cv.FONT_HERSHEY_SIMPLEX
    fontScale = 0.5
    thickness = 1
    cv.putText(img, text, point, fontFace, fontScale, color, thickness)


def createProjectionImg(colPixAve: [], height: int, color=(255, 255, 255)):
    """
        创建投影图
        @param colPixAve 原灰度图像每一列的平均亮度
        @param height   原图像的高度
        @param color    投影曲线的颜色
    """
    # 去基线
    # baseline = signal.savgol_filter(colPixAve, 71, 1, mode='nearest')
    # baselineCorrect = colPixAve - baseline
    # maxVal = max(colPixAve)
    # minVal = min(colPixAve)
    # 将列和列的平均值映射成点坐标
    points = []
    rows, cols = height, len(colPixAve)
    img = np.zeros((rows, cols, 3), dtype=np.uint8)
    # 绘制图像
    for x in range(cols):
        y = round(colPixAve[x] / 255 * height)
        y = np.uint8(rows - y)
        points.append([x, y])
    points = np.array(points)
    # 如果第三个参数为False，将获得连接所有点的折线，而不是闭合形状。
    img = cv.polylines(img, [points.reshape((-1, 1, 2))], False, color, 1)
    return img, points


def processImgChannel(grayImg, text="", color=(255, 255, 255)):
    """ 灰度图 """
    # 求灰度图中列的平均值
    rows, cols = grayImg.shape
    srccolPixAve = np.mean(grayImg, 0)
    # 平滑数据
    colPixAve = signal.savgol_filter(srccolPixAve, 11, 1, mode='nearest')
    # 寻找峰值
    peaks = getPeaks(colPixAve, 1)
    # 计算峰宽内亮度值
    getPeakVal(grayImg, srccolPixAve, peaks)
    # drawLine(peaks, colPixAve)
    projectionImg, points = createProjectionImg(colPixAve, rows, color)
    for i in range(len(peaks)):
        peak = peaks[i]
        cv.circle(projectionImg, (peak.index, points[peak.index][1]), 2, (255, 255, 255), -1)
        lPoint = (peak.left, points[peak.left][1])
        rPoint = (peak.right, points[peak.right][1])
        cv.line(projectionImg, lPoint, rPoint, (255, 255, 255), 1)
        # 绘制编号
        # drawText(projectionImg, (peak.index - 5, points[peak.index][1] - 5), str(i + 1))
    drawText(projectionImg, (5, 15), text, color)
    return peaks, projectionImg


def getPeakVal(grayImg, imgColsVal: [], peaks):
    """ 求峰宽内的亮度值 """
    if len(peaks) > 0:
        rows, cols = grayImg.shape
        for peak in peaks:
            baseVal = 0.5 * (imgColsVal[peak.left] + imgColsVal[peak.right])
            val = 0
            #for col in range(peak.index - 2, peak.index + 2):
                #val = val + (imgColsVal[col] - baseVal) * rows
            for col in range(peak.left, peak.right):
                val = val + (imgColsVal[col] - baseVal) * rows
            ave = val/(peak.right - peak.left)  # 峰内平均荧光亮度
            peak.sumPix = int(val)
            peak.avePix = int(ave)


# 伽马变换
def gamma(image):
    fgamma = 2
    image_gamma = np.uint8(np.power((np.array(image) / 255.0), fgamma) * 255.0)
    cv.normalize(image_gamma, image_gamma, 0, 255, cv.NORM_MINMAX)
    cv.convertScaleAbs(image_gamma, image_gamma)
    return image_gamma


# 限制对比度自适应直方图均衡化CLAHE
def clahe(image):
    b, g, r = cv.split(image)
    clahe = cv.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    b = clahe.apply(b)
    g = clahe.apply(g)
    r = clahe.apply(r)
    image_clahe = cv.merge([b, g, r])
    return image_clahe


def hist(image):
    '''直方图均衡'''
    r, g, b = cv.split(image)
    r1 = cv.equalizeHist(r)
    g1 = cv.equalizeHist(g)
    b1 = cv.equalizeHist(b)
    image_equal_clo = cv.merge([r1, g1, b1])
    return image_equal_clo


def laplacian(image):
    '''laplacian增强'''
    kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
    image_lap = cv.filter2D(image, cv.CV_8UC3, kernel)
    return image_lap


class ImageProcessor:

    def __init__(self, minBackgroundVal, minPeakHeight):
        self.__minBackgroundVal = minBackgroundVal
        self.__minPeakHeight = minPeakHeight


if __name__ == "__main__":
    filename = r"D:\Taoe\Image\wzm\linmingdu\images\001_02.jpg"
    srcImg = cv.imread(filename, 1)
    srcImg = cv.resize(srcImg, (650, 125), interpolation=cv.INTER_LINEAR)
    # Img =clahe(srcImg)
    # kernel = (5, 5)
    # srcImg = cv.GaussianBlur(srcImg, kernel, sigmaX=15)
    # Img = cv.GaussianBlur(Img, kernel, sigmaX=15)
    cv.imshow("src", srcImg)
    # cv.imshow("Img enhancement", Img)
    rows, cols, chs = srcImg.shape
    #rows, cols, chs = Img.shape
    # 分离通道
    chB, chG, chR = cv.split(srcImg)
    #B, G, R = cv.split(Img)
    #cv.imshow("src-R", chR)
    #cv.imshow("enh-R", R)
    #pR, ImgR = processImgChannel(R, "enh-R", (0, 0, 225))
    start = time.time()
    peaksR, projectionImgR = processImgChannel(chR, "R", (0, 0, 225))
    end = time.time()
    duration = end - start
    print(f"函数运行时长: {duration}秒")
    cv.imshow("chR", projectionImgR)
    # for peak in peaksR:
    #     print("red", peak)
    # print("-----------------------------------------------------------------------------------------------------------")
    # for green in peaksG:
    #     print("green", green)
    for j in range(len(peaksR)):
        print(peaksR[j].avePix)
    # print("----------------------------")
    # for i in range(len(pR)):
    #     print("green en", pR[i].avePix)





    # for peak in peaksR:
    #     print(peak.sumPix)
    #     cv.line(srcImg, (int(peak.left), int(0)), (int(peak.left), int(rows)), (0, 255, 0), 2)
    #     cv.line(srcImg, (int(peak.right), int(0)), (int(peak.right), int(rows)), (0, 255, 0), 2)

    # peaksR, projectionImgR = processImgChannel(chR, "R", (0, 0, 255))
    # cv.imshow("R", projectionImgR)
    #cv.imwrite("C:/Users/Shinelon/Desktop/src_r.png", srcImg)
    #cv.imwrite("C:/Users/Shinelon/Desktop/result_g.png", projectionImgG)
    cv.waitKey()