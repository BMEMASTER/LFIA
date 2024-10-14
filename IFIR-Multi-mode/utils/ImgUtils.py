# -*- coding: utf-8 -*-
import time

import cv2 as cv
import numpy as np
from PyQt5.QtWidgets import QLabel
from PyQt5.QtGui import QImage, QPixmap
import os
from matplotlib.ticker import MultipleLocator
from matplotlib.collections import PolyCollection
import matplotlib.cm as cm
os.environ['MPLCONFIGDIR'] = os.getcwd() + "/configs/"
import matplotlib.pyplot as plt
import matplotlib as mpl
import matplotlib.lines as mlines
# from scipy.signal import savgol_filter
from scipy.signal import find_peaks_cwt
from scipy import signal
import pandas as pd

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
    height = size.height()/2 - 6
    # pyqt5转换成自己能放的图片格式
    _image = QImage(img[:], img.shape[1], img.shape[0], img.shape[1], QImage.Format_Indexed8)
    # 设置图片显示
    label.setPixmap(QPixmap(_image).scaled(width, height))


def normalize(srcImg, alpha=None, beta=None, norm_type=None):
    """ 对单通道图片进行归一化 """
    normImg = np.zeros(srcImg.shape, dtype=np.uint8)
    cv.normalize(srcImg, normImg, alpha, beta, norm_type)
    return normImg

def adjust_lightness(src_img, lightness_value):
    """
    :param src_img: 待调整亮度的图片
    :param lightness_value: 亮度值
    :return:
    """
    height, width, channel = src_img.shape  # 获取shape的数值，height和width、通道

    # 新建全零图片数组src2,将height和width，类型设置为原图片的通道类型(色素全为零，输出为全黑图片)
    src2 = np.zeros([height, width, channel], src_img.dtype)
    # new_img = cv2.addWeighted(src_img, a, src2, 1 - a, lightnessValue)  # 处理后的图片
    new_img = cv.addWeighted(src_img, 1, src2, 1, lightness_value)  # 处理后的图片

    return new_img

def crop_image(src_img, x_start, x_end, y_start, y_end):
    """
    图片裁剪
    :param src_img: 原始图片
    :param x_start: x 起始坐标
    :param x_end:  x 结束坐标
    :param y_start:  y 开始坐标
    :param y_end: y 结束坐标
    :return:
    """
    tmp_img = cv.cvtColor(src_img, cv.COLOR_BGR2RGB)
    tmp_img = tmp_img[y_start:y_end, x_start:x_end]  # 长，宽
    return cv.cvtColor(tmp_img, cv.COLOR_RGB2BGR)

def getPeaks(colPixAve: [], minHeight=5.0):
    """ 求一组数据中的峰值点 """
    # filterVal = signal.savgol_filter(colPixAve, 5, 1, mode='nearest')
    # 一阶导数
    col_diff = np.diff(colPixAve)
    col_diff = signal.savgol_filter(col_diff, 15, 1, mode='nearest')
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
            # right_p = R_p
            #R_p = i + 2 * (R_p - i) + 1
            R_p = i + (R_p - i) + 15
            if R_p > len(col_diff):
                R_p = len(col_diff)

            for j in range(i, 2, -1):  # 寻找过零点左侧最高点坐标
                if col_diff[j] < col_diff[j - 1]:
                    L_p = j - 1
                else:
                    break
            # left_p = L_p
            # L_p = i - 2 * (i - L_p) - 1
            L_p = i - (i - L_p) - 15
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
                #peak.left = left_p - 25
                #peak.right = right_p + 15
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


def line_slope(x1, y1, x2, y2):
    '''求基线斜率'''
    if x2 - x1 == 0:
        raise ValueError("x2 - x1 cannot be zero to avoid division by zero")
    return (y2 - y1) / (x2 - x1)

def getPeaks_val(colPixAve: [], minHeight=5):
    """ 求一组数据中的峰值点 """
    colPixAve = signal.savgol_filter(colPixAve, 5, 1, mode='nearest')
    # 一阶导数
    col_diff = np.diff(colPixAve)
    col_diff = signal.savgol_filter(col_diff, 21, 1, mode='nearest')
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
            # right_p = R_p
            # R_p = i + 2 * (R_p - i) + 1
            #R_p = i + 2*(R_p - i) + 1
            R_p = i + (R_p - i)+9
            if R_p > len(col_diff):
                R_p = len(col_diff)

            for j in range(i, 2, -1):  # 寻找过零点左侧最高点坐标
                if col_diff[j] < col_diff[j - 1]:
                    L_p = j - 1
                else:
                    break
            # left_p = L_p
            #L_p = i - 2 * (i - L_p) - 1
            L_p = i - (i - L_p)-9
            if L_p < 1:
                L_p = 1
            slope = line_slope(L_p, colPixAve[L_p], R_p, colPixAve[R_p])
            # print(slope)
            # if abs(slope) < 45:
            # 计算峰宽
            peak_weidth = R_p - L_p
            #peak_weidth = right_p - left_p
            # 计算峰高
            peak_height = colPixAve[i] - 0.5 * (colPixAve[R_p] + colPixAve[L_p])
            if peak_height > minHeight:
                peak = Peak(i)
                peak.left = L_p
                peak.right = R_p
                #peak.left = left_p - 25
                #peak.right = right_p + 15
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
    # else:
    #     tempList = Peak(1)
    #     tempList.index = len(colPixAve)/2
    #     tempList.left = 1
    #     tempList.right = len(colPixAve) - 1
    #     peaks.append(tempList)
    return peaks

def drawLine(Peaks: [], colPixAves):
    """ 绘制曲线图 """
    filterVal = signal.savgol_filter(colPixAves, 20, 1, mode='nearest')
    # 一阶导数
    # col_diff = np.diff(filterVal)
    # col_diff = signal.savgol_filter(col_diff, 5, 1, mode='nearest')
    peakXList, peakYList = [], []
    xList, yList = [], []
    for peak in Peaks:
        # 左边点
        xList.append(peak.left)
        yList.append(round(filterVal[peak.left], 2))
        # 右边点
        xList.append(peak.right)
        yList.append(round(filterVal[peak.right], 2))
        # 峰值点
        peakXList.append(peak.index)
        peakYList.append(round(filterVal[peak.index], 2))
    plt.figure(figsize=(10, 3))
    plt.plot(filterVal, "b", label="S(t)")
    # plt.scatter(peakXList, peakYList, c="red")  # 显示峰值点
    # plt.plot(xList, yList, 'go', markersize=8, label='troughs')
    #plt.title("fluorescent (S(t))")
    # plt.legend()
    # print("[", len(xList), "]", xList)
    # print("[", len(yList), "]", yList)
    # print(len(peakXList))
    # 绘制原始图
    # 基线校正
    # baseline = signal.savgol_filter(filterVal, 71, 1, mode='nearest')
    # baseline_correct = filterVal - baseline

    #plt.figure(figsize=(5, 4))
    # img = plt.imread(r"C:\Users\Shinelon\Desktop\IFIR_100_TMP\123\003.png")
    # erode = plt.imread(r"C:\Users\Shinelon\Desktop\IFIR_100_TMP\123\002.png")
    # 绘制滤波后的图
    # plt.figure(figsize=(10, 6))
    # 设置全局字体属性
    mpl.rcParams['font.family'] = 'serif'
    mpl.rcParams['font.serif'] = 'Times New Roman'
    mpl.rcParams['axes.labelweight'] = 'bold'
    mpl.rcParams['axes.titleweight'] = 'bold'
    mpl.rcParams['axes.labelsize'] = 'x-large'  # 调整标签的大小
    mpl.rcParams['axes.titlesize'] = 'x-large'  # 调整标题的大小
    mpl.rcParams['xtick.labelsize'] = 'x-large'  # 调整刻度标签的大小
    mpl.rcParams['ytick.labelsize'] = 'x-large'  # 调整刻度标签的大小


    # plt.subplot(4, 1, 1)
    # plt.imshow(img)
    # plt.title('Original Image_3line', fontweight='bold')
    # # 获取当前的刻度标签
    # xticks = plt.gca().get_xticklabels()
    # yticks = plt.gca().get_yticklabels()
    #
    # # 设置刻度标签的字体粗细
    # for label in (xticks + yticks):
    #     label.set_fontweight('bold')
    #
    # plt.subplot(2, 1, 1)
    # plt.imshow(erode)
    # plt.title('threshold segmentation', fontweight='bold')
    # # 获取当前的刻度标签
    # xticks = plt.gca().get_xticklabels()
    # yticks = plt.gca().get_yticklabels()
    #
    # # 设置刻度标签的字体粗细
    # for label in (xticks + yticks):
    #     label.set_fontweight('bold')

    # 行扫描二维图
    # plt.subplot(2, 1, 1)
    # for i in range(len(colPixAves)):
    #      # plt.plot(filterVal, label="Signal", color='purple', linewidth=2)
    #     filterVal = signal.savgol_filter(colPixAves[i], 45, 1, mode='nearest')
    #     plt.plot(filterVal)
    # # plt.scatter(xList, yList, c="y", markersize=8, label='troughs')  # 显示峰值点
    # # plt.plot(peakXList, peakYList, 'ro', markersize=8, label='Peaks')
    # # plt.plot(xList, yList, 'go', markersize=8, label='troughs')
    # plt.title("Line Scan Formation Waveforms ", fontsize=15, fontweight='bold')
    # plt.legend(prop={'size': 'large', 'weight': 'bold'})  # 设置标签字体大小和加粗
    #
    # plt.subplot(2, 1, 2)
    # for j in range(len(Peaks)):
    #     # peaksVal = signal.savgol_filter(Peaks[j], 45, 1, mode='nearest')
    #     plt.plot(Peaks[j])
    # plt.title("Line Scan Formation Waveforms ", fontsize=15, fontweight='bold')
    # 获取当前的刻度标签
    # xticks = plt.gca().get_xticklabels()
    # yticks = plt.gca().get_yticklabels()
    # 行扫描三维图
    # 创建一个三维图形对象
    # fig = plt.figure(figsize=(10, 6))  # 设置图形大小
    # ax = fig.add_subplot(111, projection='3d')
    # # 颜色列表，可以根据需要调整
    # colors = ['r', 'g', 'b', 'c', 'm', 'y', 'purple', 'orangered', 'teal', 'brown']
    #
    # # 绘制三维线条
    # for i in range(len(colPixAves)):
    #     filterVal = signal.savgol_filter(colPixAves[i], 45, 1, mode='nearest')
    #     x = list(range(len(filterVal)))
    #     y = [i for _ in range(len(filterVal))]
    #     ax.plot(x, y, filterVal, color=colors[i % len(colors)], linewidth=2, alpha=0.7)
    # # 去除 x 和 y 轴上的网格线
    # ax.grid(False)
    # # 调整视角角度
    # ax.view_init(elev=15, azim=65)
    # # 隐藏坐标轴刻度
    # plt.xticks(())  # 隐藏x轴刻度
    # plt.yticks(())  # 隐藏y轴刻度
    # ax.set_zticks([])
    # ax.zaxis.set_ticklabels([])
    # # 设置Z轴坐标范围
    # ax.set_box_aspect((10, 4, 2))
    # 保存图像并指定分辨率
    # plt.savefig('D:\Taoe\论文图\条形行扫描图.png', dpi=900)
    # 设置刻度标签的字体粗细
    # for label in (xticks + yticks):
    #     label.set_fontweight('bold')
    # x = np.linspace(1, len(filterVal), len(filterVal))
    # peaks_cwt = find_peaks_cwt(filterVal, 40)
    # troughs_cwt = find_peaks_cwt(-filterVal, 20)
    # peaks = []
    # troughs = []
    # effective_peaks = []
    # # 判断是否为有效峰
    # for i in range(len(peaks_cwt)):
    #     for j in range(len(troughs_cwt) - 1):
    #         if troughs_cwt[j] < peaks_cwt[i] < troughs_cwt[j + 1]:
    #             baseline = (filterVal[troughs_cwt[j]] + filterVal[troughs_cwt[j + 1]]) * 0.5
    #             if filterVal[peaks_cwt[i]] - baseline > 1:
    #                 peaks.append(peaks_cwt[i])
    #                 troughs.append(troughs_cwt[j])
    #                 troughs.append(troughs_cwt[j+1])
    # # print(peaks)
    # # print(troughs)
    # troughs = sorted(list(set(troughs)))
    # effective_troughs = troughs
    # for k in range(1, len(peaks)-1):
    #     for n in range(len(troughs) - 1):
    #         if troughs[n] < peaks[k] < troughs[n + 1] and peaks[k] > troughs[n] > troughs[n-1] > peaks[k - 1]:
    #             effective_peaks.append(peaks[k])
    # if len(peaks) != 0:
    #     effective_peaks.append(peaks[0])
    #     effective_peaks.append(peaks[len(peaks)-1])
    # # print(effective_peaks)
    # # print(effective_troughs)
    # # 绘制数据和峰值
    # plt.subplot(2, 1, 2)
    # plt.plot(x, filterVal, color='purple', label='Signal', linewidth=2)  # 设置线条颜色为蓝色
    # # plt.plot(x[effective_peaks], filterVal[effective_peaks], 'ro', markersize=8, label='Peaks')  # 设置峰值标记为红色圆点
    # # plt.plot(x[effective_troughs], filterVal[effective_troughs], 'go', markersize=8, label='troughs')  # 设置波谷标记为黄色圆点
    # plt.plot(x[peaks], filterVal[peaks], 'ro', markersize=8, label='Peaks')  # 设置峰值标记为红色圆点
    # plt.plot(x[troughs], filterVal[troughs], 'go', markersize=8, label='troughs')  # 设置波谷标记为黄色圆点
    # plt.title('wavelet transform peak finding', fontsize=15, fontweight='bold')  # 设置标题字体大小
    # plt.legend(prop={'size': 'large', 'weight': 'bold'})  # 设置标签字体大小和加粗
    # # 获取当前的刻度标签
    # xticks = plt.gca().get_xticklabels()
    # yticks = plt.gca().get_yticklabels()
    #
    # # 设置刻度标签的字体粗细
    # for label in (xticks + yticks):
    #     label.set_fontweight('bold')
    # # 绘制一阶导数图
    # plt.subplot(3, 1, 2)
    # plt.plot(col_diff, label="S'(t)")
    # plt.scatter(peakXList, peakYList, c="red")  # 显示峰值点
    # plt.title("First Derivative (S'(t))")
    # plt.legend()
    #
    # # 绘制二阶导数图
    # plt.subplot(3, 1, 3)
    # plt.plot(col2_diff, label="S''(t)")
    # plt.title("Second Derivative (S''(t))")
    # plt.legend()
    plt.grid(False)
    plt.axis('off')
    plt.tight_layout()
    plt.show()

def drawLine_3D(colPixAve, colPixAve2, colPixAve3):
    """ 绘制曲线3D图 """
    filterVal = signal.savgol_filter(colPixAve, 55, 1, mode='nearest')
    filterVal2 = signal.savgol_filter(colPixAve2, 55, 1, mode='nearest')
    filterVal3 = signal.savgol_filter(colPixAve3, 55, 1, mode='nearest')
    # 设置图例字号
    mpl.rcParams['legend.fontsize'] = 10

    # 方式2：设置三维图形模式
    fig = plt.figure(figsize=(10, 6))  # 设置图形大小
    ax = fig.add_subplot(111, projection='3d')

    # R通道波形
    x = list(range(len(filterVal)))
    y = [5 for _ in range(len(filterVal))]
    z = filterVal - [13 for _ in range(len(filterVal))]
    # G通道波形
    x2 = list(range(len(filterVal2)))
    y2 = [4 for _ in range(len(filterVal2))]
    z2 = filterVal2 - [65 for _ in range(len(filterVal2))]
    # B通道波形
    x3 = list(range(len(filterVal3)))
    y3 = [3 for _ in range(len(filterVal3))]
    z3 = filterVal3 - [140 for _ in range(len(filterVal3))]
    # B/R 通道波形
    x4 = list(range(len(filterVal)))
    y4 = [2 for _ in range(len(filterVal))]
    z4 = z3 / z
    # G/R 通道波形
    x5 = list(range(len(filterVal)))
    y5 = [4 for _ in range(len(filterVal))]
    z5 = z2 / z

    # 绘制波形
    # line, = ax.plot(x, y, z, linewidth=2, color='r')
    # line2, = ax.plot(x2, y2, z2, linewidth=2, color='g')
    # line3, = ax.plot(x3, y3, z3, linewidth=2, color='b')
    line4, = ax.plot(x4, y4, z4, label='P channel', linewidth=2, color='purple')
    line4, = ax.plot(x5, y5, z5, label='Y channel', linewidth=2, color='orange')
    # 填充波形下面
    # ax.plot(x, y, np.zeros_like(z), color='r', alpha=0.2)  # 绘制基线R
    # ax.plot(x2, y2, np.zeros_like(z2), color='g', alpha=0.2)  # 绘制基线G
    # ax.plot(x3, y3, np.zeros_like(z3), color='b', alpha=0.2)  # 绘制基线B
    ax.plot(x4, y4, np.zeros_like(z4), color='purple', alpha=0.2)  # 绘制基线P
    ax.plot(x5, y5, np.zeros_like(z5), color='orange', alpha=0.2)  # 绘制基线Y
    # verts = [list(zip(x, y, z))]  # 构建波形数据
    # cmap = cm.get_cmap('viridis')
    # poly = PolyCollection(verts, facecolors=[cmap(0.5)]*len(verts), alpha=0.5)  # 创建PolyCollection对象
    # ax.add_collection3d(poly)  # 添加到3D坐标轴上

    # 设置图形标题和坐标轴标签
    ax.set_xlabel('Weight', fontsize=12, weight='bold')
    ax.set_ylabel('channel', fontsize=12, weight='bold')
    ax.set_zlabel('discolouration ratio', fontsize=12, weight='bold')
    # ax.set_zlabel('fluorescence intensity', fontsize=12, weight='bold')
    # 设置坐标轴刻度标记字体大小
    # ax.tick_params(axis='x', labelsize=10)
    # ax.tick_params(axis='y', labelsize=10)
    # ax.tick_params(axis='z', labelsize=10)
    # 设置坐标轴刻度标记字体大小和加粗
    for tick in ax.get_xticklabels():
        tick.set_fontsize(11)
        tick.set_weight('bold')
    for tick in ax.get_yticklabels():
        tick.set_fontsize(11)
        tick.set_weight('bold')
    for tick in ax.get_zticklabels():
        tick.set_fontsize(11)
        tick.set_weight('bold')

    # 设置X轴主刻度间隔
    ax.xaxis.set_major_locator(MultipleLocator(130))  # 设置X轴主刻度间隔为50
    # 设置Y轴主刻度间隔
    ax.yaxis.set_major_locator(MultipleLocator(1))  # 设置Y轴主刻度间隔为1
    # 设置Z轴主刻度间隔
    #ax.zaxis.set_major_locator(MultipleLocator(13))  # 设置Z轴主刻度间隔为50
    # 显示图例
    # line1 = mlines.Line2D([], [], color='red')
    # line2 = mlines.Line2D([], [], color='green')
    # line3 = mlines.Line2D([], [], color='blue')
    #line4 = mlines.Line2D([], [], color='purple', label='P channel')
    #line5 = mlines.Line2D([], [], color='orange', label='Y channel')
    #ax.legend(handles=[line1, line2, line3], loc='upper left', fontsize=12)
    # ax.legend(handles=[line1, line2, line3], loc='upper left', fontsize=12)
    # 去除 x 和 y 轴上的网格线
    ax.grid(False)
    # 设置背景颜色为白色
    ax.set_facecolor('none')
    # 设置Y轴坐标标签
    plt.yticks(np.arange(1, 6, 1))
    ax.set_yticks([2, 4])
    #ax.set_yticklabels(['B', 'G', 'R'])
    ax.set_yticklabels(['P', 'Y'])
    # 调整视角角度
    ax.view_init(elev=30, azim=-45)
    # 显示图形
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
    colPixAve_mean = np.mean(grayImg, 0)
    colPixAve_mean = signal.savgol_filter(colPixAve_mean, 9, 1, mode='nearest')
    peak_mean = getPeaks(colPixAve_mean, 2)  # 同列平均求波谷
    getPeakVal(grayImg, colPixAve_mean, peak_mean)
    # print(peak_mean)
    Peaks = []
    colPixAves = []
    # 获取图像每一行的信号
    for i in range(rows):
        srccolPixAve = grayImg[i, :]
        # 平滑数据
        colPixAve = signal.savgol_filter(srccolPixAve, 45, 1, mode='nearest')
        # 寻找峰值
        peaks = getPeaks(colPixAve, 1)
        Peaks.append(peaks)
        colPixAves.append(colPixAve)
        # 绘制变换波形
        # drawLine_3D(colPixAve, colPixAve2, colPixAve3)
        # 计算峰宽内亮度值
        getPeakVal(grayImg, colPixAve, peaks)
    signal_val = Waveform_homography(Peaks, peak_mean)
    drawLine(peak_mean, colPixAve_mean)
    projectionImg, points = createProjectionImg(colPixAve_mean, rows, color)
    for i in range(len(peak_mean)):
        peak = peak_mean[i]
        cv.circle(projectionImg, (peak.index, points[peak.index][1]), 2, (255, 255, 255), -1)
        lPoint = (peak.left, points[peak.left][1])
        rPoint = (peak.right, points[peak.right][1])
        cv.line(projectionImg, lPoint, rPoint, (255, 255, 255), 1)
        # 绘制编号
        drawText(projectionImg, (peak.index - 5, points[peak.index][1] - 5), str(i + 1))
    drawText(projectionImg, (5, 15), text, color)

    return signal_val, projectionImg

def Waveform_homography(Peaks, peak_mean):
    """波形同区域归类"""
    index = []
    avePix = []
    left = []
    right = []
    fluorescent_val = []
    for i in range(len(Peaks)):
        if len(Peaks[i]) == 0:  # 遇到空数组
            pass
        else:  # 如果遇到非空数组
            for peak in Peaks[i]:
                index.append(peak.index)
                avePix.append(peak.avePix)
    for peak_region in peak_mean:
        left.append(peak_region.left)
        right.append(peak_region.right)
    classified_data = []
    classified_val = []
    data, Val = classify_similar_values(index, avePix, left, right)
    # 将数组按图像荧光区域从左往右的顺序排列
    n = len(data)
    for i in range(n):
        if data[i] is None:
            pass
        else:
            for j in range(0, n-i-1):
                if data[j][0] > data[j+1][0]:
                    data[j], data[j+1] = data[j+1], data[j]
                    Val[j], Val[j+1] = Val[j+1], Val[j]
    classified_data.extend(data)
    classified_val.extend(Val)
    # print(classified_data)
    # print(classified_val)
    for Area_val in classified_val:
        if len(Area_val) > 65:
            Area_val = signal.savgol_filter(Area_val, 15, 1, mode='nearest')
            # 寻找峰值
            peaks_val = getPeaks_val(Area_val, 300)
            getVal(Area_val, peaks_val)
            fluorescent_val.append(peaks_val)
            # drawLine(peaks_val, Area_val)
    return fluorescent_val

def classify_similar_values(arr, val, left, right):
    """峰值索引引导荧光值归类"""
    classified_data = [[] for _ in left]
    classified_val = [[] for _ in left]
    for i in range(len(left)):
        for j in range(len(arr)):
            if left[i] < arr[j] < right[i]:
                classified_data[i].append(arr[j])
                classified_val[i].append(val[j])

    return classified_data, classified_val


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

def getVal(imgColsVal: [], peaks):
    """ 求aveVal峰宽内的亮度值 """
    if len(peaks) > 0:
        for peak in peaks:
            baseVal = 0.5 * (imgColsVal[peak.left] + imgColsVal[peak.right])
            val = 0
            #for col in range(peak.index - 2, peak.index + 2):
                #val = val + (imgColsVal[col] - baseVal) * rows
            for col in range(peak.left, peak.right):
                val = val + (imgColsVal[col] - baseVal)
            ave = val/(peak.right - peak.left)  # 峰内平均荧光亮度
            peak.sumPix = int(val)
            peak.avePix = int(ave)


def discolourationVal(peaksR, peaksG, peaksB):
    """变色荧光强度计算值"""
    R_index = []
    R_left = []
    R_right = []
    R_avePix = []
    for peak in peaksR:
        R_index.append(peak.index)
        R_left.append(peak.left)
        R_right.append(peak.right)
        R_avePix.append(peak.avePix)
    G_index = []
    G_left = []
    G_right = []
    G_avePix = []
    for peak in peaksG:
        G_index.append(peak.index)
        G_left.append(peak.left)
        G_right.append(peak.right)
        G_avePix.append(peak.avePix)
    B_index = []
    B_left = []
    B_right = []
    B_avePix = []
    for peak in peaksB:
        B_index.append(peak.index)
        B_left.append(peak.left)
        B_right.append(peak.right)
        B_avePix.append(peak.avePix)

    Y_val = []
    P_val = []
    for i in range(len(G_index)):
        for j in range(len(R_left)):
            if G_index[i] > R_left[j] and G_index[i] < R_right[j] and R_avePix[j] != 0:
                Y_val.append(int(G_avePix[i]/R_avePix[j]*1000))
    for i in range(len(B_index)):
        for j in range(len(R_left)):
            if B_index[i] > R_left[j] and B_index[i] < R_right[j] and R_avePix[j] != 0:
                P_val.append(int(B_avePix[i]/R_avePix[j]*1000))
    return Y_val, P_val


# 伽马变换
def gamma(image):
    fgamma = 1.75
    image_gamma = np.uint8(np.power((np.array(image) / 255.0), fgamma) * 255.0)
    cv.normalize(image_gamma, image_gamma, 0, 255, cv.NORM_MINMAX)
    cv.convertScaleAbs(image_gamma, image_gamma)
    return image_gamma


# 限制对比度自适应直方图均衡化CLAHE结合Gamma矫正
def clahe_gamma(image):
    b, g, r = cv.split(image)
    clahe = cv.createCLAHE(clipLimit=5, tileGridSize=(6, 6))
    #b = clahe.apply(b)
    #g = clahe.apply(g)
    #r = clahe.apply(r)
    r_gamma = gamma(r)
    image_clahe_gamma = cv.merge([b, g, r_gamma])

    return image_clahe_gamma


def hist(image):
    '''直方图均衡'''
    r, g, b = cv.split(image)
    r = cv.equalizeHist(r)
    g = cv.equalizeHist(g)
    b = cv.equalizeHist(b)
    image_equal_clo = cv.merge([r, g, b])
    return image_equal_clo


def laplacian(image):
    '''laplacian增强'''
    kernel = np.array([[0, -1, 0], [-1, 6, -1], [0, -1, 0]])
    image_lap = cv.filter2D(image, cv.CV_8UC3, kernel)
    return image_lap


def salt_pepper_noise(image, salt_prob, pepper_prob):
    '''椒盐噪声'''
    noisy_image = np.copy(image)
    total_pixels = image.shape[0] * image.shape[1]  # 计算图像的总像素数

    num_salt = int(total_pixels * salt_prob)  # 通过将总像素数与指定的椒盐噪声比例相乘，得到要添加的椒盐噪声的数量。
    salt_coords = [np.random.randint(0, i - 1, num_salt) for i in image.shape]
    noisy_image[salt_coords[0], salt_coords[1]] = 255

    num_pepper = int(total_pixels * pepper_prob)
    pepper_coords = [np.random.randint(0, i - 1, num_pepper) for i in image.shape]
    noisy_image[pepper_coords[0], pepper_coords[1]] = 0

    return noisy_image

def boSong_nosie(image):
    # 生成泊松噪声
    noise = np.random.poisson(image / 255.0) * 255
    noisy_image = np.clip(image + noise, 0, 255).astype('uint8')
    return noisy_image


def generate_periodic_noise(image_shape, frequency):
    x = np.arange(image_shape[1])
    y = np.arange(image_shape[0])
    xx, yy = np.meshgrid(x, y)
    noise = np.sin(2 * np.pi * frequency * xx / image_shape[1])
    return noise

class ImageProcessor:
    def __init__(self, minBackgroundVal, minPeakHeight):
        self.__minBackgroundVal = minBackgroundVal
        self.__minPeakHeight = minPeakHeight

if __name__ == "__main__":
    start = time.time()
    filename = r"D:\Taoe\Image\ZS\8.png"
    srcImg = cv.imread(filename, 1)
    srcImg = cv.resize(srcImg, (645, 125))
    cv.imshow("src", srcImg)
    # 弱光增强
    # srcImg = clahe_gamma(srcImg)
    # kernel = (9, 9)
    # srcImg = cv.GaussianBlur(srcImg, kernel, sigmaX=5)
    # cv.imshow("Clamassian", srcImg)
    # 添加噪声
    #srcImg = salt_pepper_noise(srcImg, salt_prob=0.1, pepper_prob=0)
    #srcImg = boSong_nosie(srcImg)
    # # 生成伽马噪声
    # shape, scale = 4.0, 16.0  # 设置伽马分布的参数
    # gamma_noise = np.random.gamma(shape, scale, srcImg.shape).astype('uint8')
    # 将噪声叠加到图像上
    # srcImg = cv.add(srcImg, gamma_noise)
    # cv.imshow("noise", srcImg)
    rows, cols, chs = srcImg.shape
    # 分离通道
    chB, chG, chR = cv.split(srcImg)
    # cv.imshow("chR", chR)
    # cv.imshow("chG", chG)
    # cv.imshow("chB", chB)
    # 取反求比色试纸条
    gray = cv.cvtColor(srcImg, cv.COLOR_BGR2GRAY)
    # white_img = np.full(gray.shape, 255, dtype=np.uint8)
    # gray = white_img - gray
    # cv.imshow("gray", gray)
    # # 创建曲线图
    k = 0
    signalR, projectionImgR = processImgChannel(chR, "R", (0, 0, 255))
    for i in range(len(signalR)):
        for j in range(len(signalR[i])):
            k = k + 1
            # print(signalR[i][j].avePix)
            print('Val {}:{}'.format(k, signalR[i][j].avePix))
    end = time.time()
    duration = end - start
    print(f"代码运行时长: {duration}秒")
    # peaksG, projectionImgG = processImgChannel(chG, "G", (0, 255, 0))
    # peaksB, projectionImgB = processImgChannel(chB, "B", (255, 0, 0))
    # print("peaksR:", peaksR)
    # print("peaksG:", peaksG)
    # print("peaksB:", peaksB)
    # cv.imshow("projectR", projectionImgR)
    # cv.imshow("projectG", projectionImgG)
    # cv.imshow("projectB", projectionImgB)
    # Y_val, P_val = discolourationVal(peaksR, peaksG, peaksB)
    # for i in range(len(Y_val)):
    #     print('Y: ', Y_val[i])
    # for i in range(len(P_val)):
    #      print('P: ', P_val[i])
    # for peak in peaksB:
    #     print(peak.avePix)
    # for peak in peaksR:
    #     print(peak)
    #     cv.line(srcImg, (int(peak.left), int(0)), (int(peak.left), int(rows)), (0, 255, 0), 2)
    #     cv.line(srcImg, (int(peak.right), int(0)), (int(peak.right), int(rows)), (0, 255, 0), 2)

    # peaksR, projectionImgR = processImgChannel(chR, "R", (0, 0, 255))
    # cv.imshow("R", projectionImgR)
    # cv.imwrite(r"D:\Taoe\wsdianzhen\17chR.png", chR)
    # cv.imwrite(r"C:\Users\Shinelon\Desktop\paper img\chG.png", chG)
    # cv.imwrite(r"C:\Users\Shinelon\Desktop\paper img\chB.png", chB)
    #cv.imwrite("C:/Users/Shinelon/Desktop/src_r.png", srcImg)
    #cv.imwrite("C:/Users/xhc/Desktop/result_g.png", projectionImgG)
    cv.waitKey()