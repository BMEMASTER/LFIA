import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

# 创建示例数据
x = np.linspace(-5, 5, 100)
y = np.linspace(-5, 5, 100)
X, Y = np.meshgrid(x, y)
Z = np.exp(-0.1*(X**2 + Y**2))  # 使用高斯函数生成圆形底部的峰

# 绘制三维表面
fig = plt.figure(figsize=(10, 6))
ax = fig.add_subplot(111, projection='3d')
#ax.plot_surface(X, Y, Z, cmap='viridis', alpha=0.8)

# 高亮显示波峰曲线
theta = np.linspace(0, 2*np.pi, 100)
x_peak = 5 * np.cos(theta)
y_peak = 5 * np.sin(theta)
z_peak = np.exp(-0.1*(x_peak**2 + y_peak**2))
ax.plot(x_peak, y_peak, z_peak, 'r', linewidth=2)

# 在圆内部绘制多条与Y轴平行的直线
x_coords = np.arange(-5, 6, 0.2)
for x_val in x_coords:
    max_y = np.sqrt(25 - x_val**2)
    y_line = np.linspace(-max_y, max_y, 100)
    z_line = np.exp(-0.1*(x_val**2 + y_line**2))
    ax.plot([x_val] * 100, y_line, z_line,  color='black', linestyle='--', linewidth=0.5)
    # 计算并绘制交点
    #ax.scatter([x_val, x_val], [-max_y, max_y], [np.exp(-0.1*(x_val**2 + max_y**2)), np.exp(-0.1*(x_val**2 + max_y**2))], color='b', s=15)

# 绘制一条平行于X轴的直线
y_fixed = 0
x_line = np.linspace(-5, 5, 100)
z_line_x = np.exp(-0.1*(x_line**2 + y_fixed**2))
#ax.plot(x_line, [y_fixed] * 100, z_line_x, 'b', linewidth=3)
# 计算并绘制与圆的交点
#ax.scatter([-5, 5], [y_fixed, y_fixed], [np.exp(-0.1*(25)), np.exp(-0.1*(25))], color='black', s=15)

# 计算并绘制直线与直线之间的交点
for x_val in x_coords:
    if x_val != 0:
        z_intersection = np.exp(-0.1*(x_val**2))
        #ax.scatter([x_val], [y_fixed], [z_intersection], color='red', s=15)
ax.set_box_aspect((1, 1, 0.4))
# 去掉网格
ax.grid(False)
ax.axis('off')
# 调整视角角度
ax.view_init(elev=32, azim=-60)
# 保存图像并指定分辨率
plt.savefig('D:\Taoe\论文图\点阵行扫3D图黑白弱.png', dpi=900)
plt.show()
