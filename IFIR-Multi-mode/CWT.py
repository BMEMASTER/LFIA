import numpy as np
import matplotlib.pyplot as plt
import cv2 as cv
import pywt
from scipy.signal import find_peaks, savgol_filter
import pandas as pd

def salt_pepper_noise(image, salt_prob, pepper_prob):
    '''添加椒盐噪声'''
    noisy_image = np.copy(image)
    total_pixels = image.shape[0] * image.shape[1]

    num_salt = int(total_pixels * salt_prob)
    salt_coords = [np.random.randint(0, i - 1, num_salt) for i in image.shape]
    noisy_image[salt_coords[0], salt_coords[1]] = 255

    num_pepper = int(total_pixels * pepper_prob)
    pepper_coords = [np.random.randint(0, i - 1, num_pepper) for i in image.shape]
    noisy_image[pepper_coords[0], pepper_coords[1]] = 0

    return noisy_image

def boSong_nosie(image):
    '''添加泊松噪声'''
    noise = np.random.poisson(image / 255.0) * 255
    noisy_image = np.clip(image + noise, 0, 255).astype('uint8')
    return noisy_image

def plot_gaussian_waveform(amplitude=1, center=0, std_dev=1, t_range=(-5, 5), num_points=1000):
    """
    绘制高斯波形。

    参数：
    amplitude (float): 波峰的高度（幅度）。
    center (float): 波峰的中心位置。
    std_dev (float): 标准差，控制波形的宽度。
    t_range (tuple): 自变量 t 的范围，以 (min, max) 形式表示。
    num_points (int): 用于绘图的点数。

    返回：
    None
    """
    # 定义自变量 t
    t = np.linspace(t_range[0], t_range[1], num_points)

    # 定义高斯函数
    wavelet = amplitude * np.exp(- (t - center)**2 / (2 * std_dev**2))
    return wavelet

# 读取图像并处理
img = cv.imread(r"D:\Taoe\Image\wzm\linmingdu\images\001_02.jpg", 1)
# 生成伽马噪声
# shape, scale = 4.0, 12.0  # 设置伽马分布的参数
# gamma_noise = np.random.gamma(shape, scale, img.shape).astype('uint8')
# img = cv.add(img, gamma_noise)
# 添加噪声
# img = salt_pepper_noise(img, salt_prob=0.03, pepper_prob=0.011)
# img = boSong_nosie(img)
# cv.imshow('noise', img)
_, _, chR = cv.split(img)
chR = cv.resize(chR, (945, 175))
rows, cols = chR.shape
x = np.linspace(1, 945, 945)
y = np.mean(chR, 0)

# 将一维荧光信号数据保存到Excel
df = pd.DataFrame({'X': x, 'Y': y})
df.to_excel(r'D:\Taoe\Image\wzm\linmingdu\images\fluorescent_signal_lowlight.xlsx', index=False)
# y = savgol_filter(y, 53, 1, mode='nearest')
# 对信号进行镜像延拓以减小边界效应
y_extended = np.concatenate([y[::-1], y, y[::-1]])

# 对 y_extended 进行求导

y_derivative = np.gradient(y)
# y_derivative = savgol_filter(y_derivative, 73, 1, mode='nearest')
# 找到 y_peaks 的峰值位置
y_peaks, _ = find_peaks(y, distance=20, prominence=1.5)

# 进行连续小波变换
wavelet = 'gaus2'  # 选择小波基函数
scales = np.arange(1, 128)  # 尺度范围
coefficients, frequencies = pywt.cwt(y_extended, scales, wavelet, method='conv')

# 选择一个尺度来表示变换后的信号，并截取原始信号对应的部分
selected_scale = 42
selected_coefficient = coefficients[selected_scale, len(y):2*len(y)]
# 对选定的小波变换系数进行求导
derivative = np.gradient(selected_coefficient)
# 将 y_derivative 的数据保存到 Excel
df_derivative = pd.DataFrame({'selected_coefficient': selected_coefficient})
df_derivative.to_excel(r'D:\Taoe\Image\wzm\linmingdu\images\selected_coefficient.xlsx', index=False)
# 找到小波变换系数的峰值位置，增加筛选条件
peaks, _ = find_peaks(selected_coefficient, distance=200, prominence=2)
# 提取正值分段
positive_segments = []
current_segment = []
for i, value in enumerate(selected_coefficient):
    if value > 0:
        current_segment.append((x[i], value))
    else:
        if current_segment:
            positive_segments.append(current_segment)
            current_segment = []

# 如果最后一个segment未结束，添加它
if current_segment:
    positive_segments.append(current_segment)

# 手动实现峰值检测和距离过滤
def find_peaks_with_distance(segments, distance):
    peaks = []
    for segment in segments:
        segment_x, segment_y = zip(*segment)
        max_index = np.argmax(segment_y)
        max_x = segment_x[max_index]
        max_y = segment_y[max_index]

        # 只标记高度大于 5.7 的最大值
        if max_y > 5.7:
            if not peaks or max_x - peaks[-1][0] >= distance:
                peaks.append((max_x, max_y))

    return peaks

# 设置图形布局
fig = plt.figure(figsize=(9, 12))
gs = fig.add_gridspec(5, 1, height_ratios=[1, 1, 1, 1, 1])

# 绘制 y 的求导结果及其峰值
ax1 = fig.add_subplot(gs[0, 0])
ax1.plot(y_derivative, 'b', label='Derivative of y_extended')
ax1.plot(y_peaks, y_derivative[y_peaks], 'ro', label='Peaks')
ax1.set_title("Derivative of y_extended and Peaks")
ax1.set_xticks([])
ax1.set_yticks([])
ax1.spines['top'].set_visible(False)
ax1.spines['right'].set_visible(False)
ax1.spines['bottom'].set_visible(False)
ax1.spines['left'].set_visible(False)

# 绘制一维荧光信号
ax2 = fig.add_subplot(gs[1, 0])
ax2.plot(x, y, 'b', label='Fluorescent Signal')
ax2.set_xticks([])
ax2.set_yticks([])
ax2.spines['top'].set_visible(False)
ax2.spines['right'].set_visible(False)
ax2.spines['bottom'].set_visible(False)
ax2.spines['left'].set_visible(False)

# 绘制小波变换系数
ax3 = fig.add_subplot(gs[2, 0])
ax3.plot(x, selected_coefficient, 'b', label='Detail Coefficient')
ax3.plot(x, coefficients[0, len(y):2*len(y)], 'orange', label='Approximation Coefficient', linestyle='-')
# ax3.set_xticks([])
# ax3.set_yticks([])
# ax3.spines['top'].set_visible(False)
# ax3.spines['right'].set_visible(False)
# ax3.spines['bottom'].set_visible(False)
# ax3.spines['left'].set_visible(False)

# 绘制求导后的信号及其极值点
ax4 = fig.add_subplot(gs[3, 0])
ax4.plot(x, derivative, 'b', label='Derivative of Detail Coefficient')
ax4.plot(x[peaks], derivative[peaks], 'ro', label='Peaks')
ax4.set_xticks([])
ax4.set_yticks([])
ax4.spines['top'].set_visible(False)
ax4.spines['right'].set_visible(False)
ax4.spines['bottom'].set_visible(False)
ax4.spines['left'].set_visible(False)

# 保存图像并指定分辨率
# plt.savefig('D:\Taoe\论文图\算法原理示意图3.png', dpi=900)
plt.tight_layout()
plt.show()
