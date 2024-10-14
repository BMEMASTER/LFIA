import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from PIL import Image
from scipy.interpolate import griddata

# 读取图像
img = Image.open(r'C:\Users\Shinelon\Desktop\IFIR_100_TMP\popular\red1.png')

# 提取R通道的灰度值
r_channel = np.array(img)[:, :, 0]

# 创建X和Y轴数据
x = np.linspace(0, r_channel.shape[1] - 1, r_channel.shape[1])
y = np.linspace(0, r_channel.shape[0] - 1, r_channel.shape[0])
X, Y = np.meshgrid(x, y)

# 使用R通道的灰度值作为Z轴
Z = r_channel

# 插值数据，使线条更平滑
x_interp = np.linspace(0, r_channel.shape[1] - 1, r_channel.shape[1] * 10)
y_interp = np.linspace(0, r_channel.shape[0] - 1, r_channel.shape[0] * 10)
X_interp, Y_interp = np.meshgrid(x_interp, y_interp)
Z_interp = griddata((X.flatten(), Y.flatten()), Z.flatten(), (X_interp, Y_interp), method='cubic')

# 将Z轴低于90的部分替换为90
Z_interp[Z_interp < 90] = 90

# 设置x_coords
x_coords = np.linspace(0, r_channel.shape[1] - 1, 86)

# 设置颜色映射
cmap = plt.cm.inferno  # 可以根据需要选择其他颜色映射
colors = cmap(np.linspace(0, 1, len(x_coords)))

# 绘制三维图像
fig = plt.figure(figsize=(12, 6))
ax = fig.add_subplot(111, projection='3d')

# 在图中添加多条平行于Y轴的彩色线
for i, x_val in enumerate(x_coords):
    y_line = np.linspace(0, r_channel.shape[0] - 1, 100)
    z_line = griddata((X.flatten(), Y.flatten()), Z.flatten(), (np.full_like(y_line, x_val), y_line), method='cubic')
    z_line[z_line < 90] = 90  # 确保所有Z值低于90的部分替换为90
    ax.plot(np.full_like(y_line, x_val), y_line, z_line, color='black', linestyle='--', linewidth=0.5)

# 添加红色的底部围线
# 定义底部轮廓
x_bottom = np.linspace(0, r_channel.shape[1] - 1, 100)
y_bottom = np.zeros_like(x_bottom)
z_bottom = np.full_like(x_bottom, 90)  # 底部的Z值固定为135

# 绘制底部的红色线条
ax.plot(x_bottom, y_bottom, z_bottom, color='red', linewidth=1)

# 绘制Y轴方向的红色线条
y_bottom = np.linspace(0, r_channel.shape[0] - 1, 100)
x_bottom = np.zeros_like(y_bottom)
z_bottom = np.full_like(y_bottom, 90)
ax.plot(x_bottom, y_bottom, z_bottom, color='red', linewidth=1)

# 绘制右侧X轴方向的红色线条
y_bottom = np.linspace(0, r_channel.shape[0] - 1, 100)
x_bottom = np.full_like(y_bottom, r_channel.shape[1] - 1)
z_bottom = np.full_like(y_bottom, 90)
ax.plot(x_bottom, y_bottom, z_bottom, color='red', linewidth=1)

# 绘制Y轴方向顶部的红色线条
x_bottom = np.linspace(0, r_channel.shape[1] - 1, 100)
y_bottom = np.full_like(x_bottom, r_channel.shape[0] - 1)
z_bottom = np.full_like(x_bottom, 90)
ax.plot(x_bottom, y_bottom, z_bottom, color='red', linewidth=1)

# 去掉背景和坐标轴
ax.set_box_aspect([4, 2, 0.6])  # 拉长X轴比例
ax.grid(False)
ax.axis('off')
ax.set_facecolor('white')  # 设置背景为白色
ax.view_init(elev=15, azim=-65)
# 保存图像并指定分辨率
plt.savefig('D:\Taoe\论文图\条形行扫3D图黑白.png', dpi=1400)

# 显示图像
plt.show()
