import numpy as np
import matplotlib.pyplot as plt
import cv2 as cv

def mexican_hat_wavelet(t, s):
    """
    生成Mexican Hat小波函数。

    参数：
    t : array_like
        时间序列
    s : float
        小波尺度

    返回：
    array_like
        Mexican Hat小波函数值
    """
    # 计算Mexican Hat小波函数
    t = t / s  # 归一化时间轴
    wavelet = (2 / (np.sqrt(3 * s) * np.pi ** 0.25)) * (1 - (t ** 2)) * np.exp(-t ** 2 / 2)
    return wavelet


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
img = cv.imread(r"D:\Taoe\wzm\linmingdu\images\001_03.jpg", 1)
_, _, chR = cv.split(img)
chR = cv.resize(chR, (945, 175))
rows, cols = chR.shape
x = np.linspace(1, 945, 945)
y = np.mean(chR, 0)

# 对信号进行镜像延拓以减小边界效应
# y_extended = np.concatenate([y[::-1], y, y[::-1]])

# 定义时间范围和尺度
t_range = np.linspace(-5, 5, 1000)
scales = np.arange(1, 128)

# 初始化保存小波变换系数的数组
coefficients = np.zeros((len(scales), len(y)))

# 逐尺度计算小波变换
for i, scale in enumerate(scales):
    # 缩放时间范围
    t_scaled = t_range * scale
    # 计算缩放后的高斯小波
    wavelet = plot_gaussian_waveform(amplitude=1, center=0, std_dev=1, t_range=(-5, 5), num_points=945)
    # 计算卷积来获得小波变换系数
    coefficients[i, :] = np.convolve(y, wavelet, mode='same')

# 选择几个不同的尺度来展示变换后的波形
selected_scales = [90]  # 可以根据需要选择不同的尺度
plt.figure(figsize=(12, 6))
plt.plot(y, label='Original Signal', color='blue', linewidth=1.5)
plt.show()
for scale in selected_scales:
    plt.plot(coefficients[scale, :], label=f'Scale {scale}', linewidth=1)

plt.xlabel('Time')
plt.ylabel('Amplitude')
plt.title('Waveform of CWT Coefficients at Selected Scales')
plt.legend()
plt.show()
