import numpy as np
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestRegressor
from sklearn.svm import SVR, SVC
import pandas as pd
from scipy.signal import savgol_filter
from scipy import signal
# 从Excel文件中读取数据
df = pd.read_excel(r'C:\Users\Shinelon\Desktop\SVR.xlsx', header=None)  # 假设数据没有标题行，所以header=None

nan_check = df.isnull().sum().sum()
if nan_check > 0:
    # 删除包含 NaN 值或者无穷大值的行
    df = df.dropna()
# 假设数据是一列一列的，将每一列的数据提取到对应的变量中

X_train = df.iloc[:, 0].values.reshape(-1, 1)
y_train = df.iloc[:, 3].values.reshape(-1, 1)

# 创建SVR模型
# svr_rbf = SVR(kernel='rbf', C=1000, gamma=0.5, epsilon=0.5)
# 创建随机森林回归模型
svr_rbf = RandomForestRegressor(n_estimators=11, random_state=23)
# 拟合数据
svr_rbf.fit(X_train, y_train)

# 生成拟合曲线
# X_fit = np.linspace(0, 15, 100)[:, np.newaxis]
X_fit = X_train
y_fit = svr_rbf.predict(X_fit)
# 使用 Savitzky-Golay 滤波器进行平滑处理
y_fit = signal.savgol_filter(y_fit, 5, 1, mode='nearest')
# 绘制原始数据点和拟合曲线
plt.scatter(X_train, y_train, color='black', marker='s', label='Data')  # 数据点用黑色方块
plt.plot(X_fit, y_fit, '-', color='red', label='SVR Fit (RBF kernel)')  # 拟合曲线用红色

# 添加亚坐标
plt.gca().xaxis.set_minor_locator(plt.MultipleLocator(1))  # 设置X轴次刻度间隔为0.5
plt.gca().yaxis.set_minor_locator(plt.MultipleLocator(500))  # 设置Y轴次刻度间隔为500

plt.xlabel('Consentration(NCU/mL)')
plt.ylabel('R/G intensity(a.u.)')
#plt.title('Support Vector Regression')
plt.legend()
plt.grid(False)  # 添加网格线
# 计算拟合精度
score = svr_rbf.score(X_train, y_train)
print("SVR模型拟合精度：", score)
plt.show()


