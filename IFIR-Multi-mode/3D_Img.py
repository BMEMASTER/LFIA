import numpy as np
import matplotlib.pyplot as plt
import cv2
from matplotlib import cm
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.ticker import MultipleLocator
def gamma(image):
    fgamma = 1.75
    image_gamma = np.uint8(np.power((np.array(image) / 255.0), fgamma) * 255.0)
    cv2.normalize(image_gamma, image_gamma, 0, 255, cv2.NORM_MINMAX)
    cv2.convertScaleAbs(image_gamma, image_gamma)
    return image_gamma
filename = r"D:\Taoe\Image\wsdianzhen\20240930114305.jpg"
srcImg = cv2.imread(filename, 1)
srcImg = cv2.resize(srcImg, (600, 250))
srcImg = gamma(srcImg)
cv2.imshow("src", srcImg)
kernel = (5, 5)
srcImg = cv2.GaussianBlur(srcImg, kernel, sigmaX=15)
chB, chG, chR = cv2.split(srcImg)
# 创建600x250的全白掩膜 (值为255)
mask = np.ones((250, 600), dtype=np.uint8) * 3
# 将掩膜和图像逐点相乘（点乘）
# R = mask + chR
R = cv2.multiply(chR, mask)
#cv2.imshow("chR", chR)
# cv2.imwrite('C:\\Users\\Shinelon\\Desktop\\IFIR_100_TMP\\123\\003.png', srcImg)
# cv2.imwrite('C:\\Users\\Shinelon\\Desktop\\IFIR_100_TMP\\123\\004.png', chR)
# gray = cv2.cvtColor(srcImg, cv2.COLOR_BGR2GRAY)
# white_img = np.full(gray.shape, 255, dtype=np.uint8)
# gray = white_img - gray
# 生成示例数据
t = np.linspace(0, 600, 600)  # 时间
x = np.linspace(0, 250, 250)    # 位置
t, x = np.meshgrid(t, x)
# data = gray

# 创建一个三维图形对象
fig = plt.figure(figsize=(10, 8))
ax = fig.add_subplot(111, projection='3d')

# 定义分段的彩色图
cmap = plt.get_cmap('jet')  # 蓝->白->红

# 绘制三维曲面
surf = ax.plot_surface(-t, x, chR, cmap=cmap, linewidth=0, antialiased=False)

# 设置颜色映射
surf.set_clim(vmin=np.min(R), vmax=np.max(R))  # 设置颜色映射的最小值和最大值

# 添加颜色条
# colorbar = fig.colorbar(surf, shrink=0.5, aspect=12)
# 隐藏颜色条刻度值
# colorbar.set_ticks([])
# 隐藏坐标轴刻度
plt.xticks(())  # 隐藏x轴刻度
plt.yticks(())  # 隐藏y轴刻度
ax.set_zticks([])
ax.zaxis.set_ticklabels([])
# 设置亚坐标
# 设置亚坐标
# ax.xaxis.set_major_locator(MultipleLocator(100))  # 设置X轴主刻度间隔为100
# ax.xaxis.set_minor_locator(MultipleLocator(50))  # 设置X轴次刻度间隔为50
#
# ax.yaxis.set_major_locator(MultipleLocator(100))  # 设置Y轴主刻度间隔为50
# ax.yaxis.set_minor_locator(MultipleLocator(50))  # 设置Y轴次刻度间隔为10
#
# ax.zaxis.set_major_locator(MultipleLocator(100))  # 设置Z轴主刻度间隔为50
# ax.zaxis.set_minor_locator(MultipleLocator(50))  # 设置Z轴次刻度间隔为10
# 设置Z轴坐标范围
ax.set_box_aspect((6, 2, 1))
# 去除 x 和 y 轴上的网格线
ax.grid(False)
ax.axis('off')
# 调整视角角度
# ax.view_init(elev=51, azim=-52)
# 调整视角角度
ax.view_init(elev=51, azim=90)
# 保存图像并指定分辨率
plt.savefig('D:\Taoe\论文图\三维点阵荧光图.png', dpi=900)
# 显示图形
plt.show()
cv2.waitKey()