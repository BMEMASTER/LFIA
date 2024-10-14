# -*- coding: utf-8 -*-
import cv2 as cv
import numpy as np
from PyQt5.QtWidgets import QLabel
from PyQt5.QtGui import QImage, QPixmap
#import matplotlib.pyplot as plt
# from scipy.signal import savgol_filter
from scipy import signal


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

    def __repr__(self):
        return str({
            "width": self.width,
            "height": self.height,
            "index": self.index,
            "left": self.left,
            "right": self.right,
            "sumPix": self.sumPix
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


def getPeaks(colPixAve: []):
    """ 求一组数据中的峰值点 """
    filterVal = signal.savgol_filter(colPixAve, 5, 1, mode='nearest')
    # 一阶导数
    col_diff = np.diff(filterVal)
    col_diff = signal.savgol_filter(col_diff, 5, 1, mode='nearest')
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
            R_p = i + 2 * (R_p - i) + 1
            if R_p > len(col_diff):
                R_p = len(col_diff)

            for j in range(i, 2, -1):  # 寻找过零点左侧最高点坐标
                if col_diff[j] < col_diff[j - 1]:
                    L_p = j - 1
                else:
                    break
            L_p = i - 2 * (i - L_p) - 1
            if L_p < 1:
                L_p = 1
            # 计算峰宽
            peak_weidth = 2 * (R_p - L_p)
            # 计算峰高
            peak_height = colPixAve[i] - 0.5 * (colPixAve[R_p] + colPixAve[L_p])
            if peak_height > 5:
                peak = Peak(i)
                peak.left = L_p
                peak.right = R_p
                peak.width = round(peak_weidth, 2)
                peak.height = round(peak_height, 2)
                # print(peak)
                tempList.append(peak)
    # 过滤相邻的点
    size = len(tempList)
    print("temp peak list size: ", size)
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


def getROI(srcImg):
    """ 截取图片的有效区域 """
    img = srcImg[180: 310, 140: 470]
    # cv.imshow("1", img)
    gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
    kernel = cv.getStructuringElement(cv.MORPH_RECT, (5, 5))
    dst = cv.erode(gray, kernel, 3)
    dst = cv.dilate(dst, kernel, 3)
    ret, binaryImg = cv.threshold(dst, 30, 255, cv.THRESH_BINARY)
    # cv.imshow("b", binaryImg)
    # 找轮廓，最大的那个轮廓则为有效区域
    contours, hierarchy = cv.findContours(binaryImg, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)
    if len(contours) > 0:
        maxContour = None
        maxArea = 0
        for contour in contours:
            area = cv.contourArea(contour)
            if area > maxArea:
                maxArea = area
                maxContour = contour
        # 返回四个值，分别是x，y，w，h。 x，y是矩阵左上点的坐标，w，h是矩阵的宽和高
        imgArea = img.shape[0] * img.shape[1]
        print(maxArea / imgArea)
        if maxArea > 0.15 * imgArea:
            x, y, w, h = cv.boundingRect(maxContour)
            dt_y = int(0.1 * h)
            dt_x = int(0.1 * w)
            dstImg = img[y+dt_y:y+h-dt_y, x+dt_x:x+w-dt_x]
            # cv.imshow("d", dstImg)
            return dstImg
    # return None


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


def createProjectionImg(colPixAve:[], color=(255, 255, 255)):
    # 去基线
    filterVal = signal.savgol_filter(colPixAve, 9, 1, mode='nearest')
    # baseline = signal.savgol_filter(filterVal, 71, 1, mode='nearest')
    # baselineCorrect = filterVal - baseline
    maxVal = max(filterVal)
    minVal = min(filterVal)
    print("maxVal:{}, minVal:{}, range:{}".format(maxVal, minVal, maxVal - minVal))
    # 将列和列的平均值映射成点坐标
    points = []
    # 设定图片的高度为60，将0-255归一化到0-60
    rows, cols = int(maxVal - minVal + 50), len(filterVal)
    img = np.zeros((rows, cols, 3), dtype=np.uint8)
    print(img.shape)
    for x in range(cols):
        y = np.uint8(rows - (filterVal[x] - minVal))
        points.append([x, y])
    points = np.array(points)
    # 如果第三个参数为False，将获得连接所有点的折线，而不是闭合形状。
    img = cv.polylines(img, [points.reshape((-1, 1, 2))], False, color, 1)
    return img, points


def processImgChannel(grayImg, text="", color=(255, 255, 255)):
    """ 灰度图 """
    # 求灰度图中列的平均值
    colPixAve = np.mean(grayImg, 0)
    # 寻找峰值
    peaks = getPeaks(colPixAve)
    # 计算峰宽内像素值
    for peak in peaks:
        rows, cols = grayImg.shape
        i = peak.index - 3
        for row in range(rows):
            for col in range(i, i + 6):
                peak.sumPix += grayImg[row, col]
    # drawLine(peaks, colPixAve)
    projectionImg, points = createProjectionImg(colPixAve, color)
    for i in range(len(peaks)):
        peak = peaks[i]
        cv.circle(projectionImg, (peak.index, points[peak.index][1]), 2, (255, 255, 255), -1)
        lPoint = (peak.left, points[peak.left][1])
        rPoint = (peak.right, points[peak.right][1])
        cv.line(projectionImg, lPoint, rPoint, (255, 255, 255), 1)
        # 绘制编号
        drawText(projectionImg, (peak.index - 5, points[peak.index][1] - 5), str(i + 1))
    drawText(projectionImg, (5, 15), text, color)
    return peaks, projectionImg


class ImageProcessor:

    def __init__(self, minBackgroundVal, minPeakHeight):
        self.__minBackgroundVal = minBackgroundVal
        self.__minPeakHeight = minPeakHeight


if __name__ == "__main__":
    filename = "/home/tao/Desktop/IMG_VISION/2023_08_14_14_51_22_.jpg"
    srcImg = cv.imread(filename, 1)
    img = getROI(srcImg)
    img = cv.resize(img, (640,150))
    cv.imshow("i", img)
    # 分离通道
    chB, chG, chR = cv.split(img)
    # cv.imwrite("C:/Users/xhc/Desktop/r.png", chR)
    # cv.imwrite("C:/Users/xhc/Desktop/g.png", chG)
    # cv.imshow("r", chR)
    cv.imshow("g", chG)
    # # 创建曲线图
    peaksG, projectionImgG = processImgChannel(chG, "G", (0, 255, 0))
    print(peaksG)
    cv.imshow("G", projectionImgG)
    # peaksR, projectionImgR = processImgChannel(chR, "R", (0, 0, 255))
    # cv.imshow("R", projectionImgR)
    # cv.imwrite("C:/Users/xhc/Desktop/result_r.png", projectionImgR)
    # cv.imwrite("C:/Users/xhc/Desktop/result_g.png", projectionImgG)
    cv.waitKey(0)