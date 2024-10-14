import numpy as np
import cv2
from matplotlib import pyplot as plt
from sklearn import svm
from sklearn.model_selection import train_test_split
# 加载样品数据
def SVM():
    X = np.array([...])
    # 特征矩阵，每一行代表图片的像素矩阵
    y = np.array([...])
    # 类别标签，0表示背景，1表示前景

    # 对样本进行预处理
    #X = preprocess(X)

    #划分训练集和测试集
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)

    # 训练SVM
    clf = svm.SVC()
    clf.fit(X_train, y_train)
# 伽马变换
def gamma(image):
    fgamma = 2
    image_gamma = np.uint8(np.power((np.array(image) / 255.0), fgamma) * 255.0)
    cv2.normalize(image_gamma, image_gamma, 0, 255, cv2.NORM_MINMAX)
    cv2.convertScaleAbs(image_gamma, image_gamma)
    return image_gamma

# 限制对比度自适应直方图均衡化CLAHE
def clahe(image):
    b, g, r = cv2.split(image)
    clahe = cv2.createCLAHE(clipLimit=5, tileGridSize=(5, 5))
    b = clahe.apply(b)
    g = clahe.apply(g)
    r = clahe.apply(r)
    image_clahe = cv2.merge([b, g, r])
    kernel = (5, 5)
    image_clahe = cv2.GaussianBlur(image_clahe, kernel, sigmaX=15, sigmaY=15)
    return image_clahe

# 鼠标事件的回调函数
def on_mouse(event, x, y, flag, param):
    global rect
    global leftButtonDowm
    global leftButtonUp

    # 鼠标左键按下
    if event == cv2.EVENT_LBUTTONDOWN:
        rect[0] = x
        rect[2] = x
        rect[1] = y
        rect[3] = y
        leftButtonDowm = True
        leftButtonUp = False

    # 移动鼠标事件
    if event == cv2.EVENT_MOUSEMOVE:
        if leftButtonDowm and not leftButtonUp:
            rect[2] = x
            rect[3] = y

    # 鼠标左键松开
    if event == cv2.EVENT_LBUTTONUP:
        if leftButtonDowm and not leftButtonUp:
            x_min = min(rect[0], rect[2])
            y_min = min(rect[1], rect[3])

            x_max = max(rect[0], rect[2])
            y_max = max(rect[1], rect[3])

            rect[0] = x_min
            rect[1] = y_min
            rect[2] = x_max
            rect[3] = y_max
            leftButtonDowm = False
            leftButtonUp = True

img = cv2.imread(r'C:\Users\Shinelon\Desktop\IFIR_100_TMP\circle.jpg')
img = cv2.resize(img, (900, 350))
#img = gamma(img)
#img = clahe(img)
mask = np.zeros(img.shape[:2], np.uint8)
#cv2.imshow('MASK', mask)
bgdModel = np.zeros((1, 65), np.float64)  # 背景模型
fgdModel = np.zeros((1, 65), np.float64)  # 前景模型
rect = [0, 0, 0, 0]  # 设定需要分割的图像范围

leftButtonDowm = False  # 鼠标左键按下
leftButtonUp = True  # 鼠标左键松开

cv2.namedWindow('img')  # 指定窗口名来创建窗口
cv2.setMouseCallback('img', on_mouse)  # 设置鼠标事件回调函数 来获取鼠标输入
cv2.imshow('img', img)  # 显示图片

while cv2.waitKey(1) == -1:
    # 左键按下，画矩阵
    if leftButtonDowm and not leftButtonUp:
        img_copy = img.copy()
        cv2.rectangle(img_copy, (rect[0], rect[1]), (rect[2], rect[3]), (0, 255, 0), 2)
        cv2.imshow('img', img_copy)
        #cv2.imwrite("wq.jpg", img)
    # 左键松开，矩形画好
    elif not leftButtonDowm and leftButtonUp and rect[2] - rect[0] != 0 and rect[3] - rect[1] != 0:
        rect[2] = rect[2] - rect[0]
        rect[3] = rect[3] - rect[1]
        rect_copy = tuple(rect.copy())
        rect = [0, 0, 0, 0]
        # 物体分割
        grabcut = cv2.grabCut(img, mask, rect_copy, bgdModel, fgdModel, 6, cv2.GC_INIT_WITH_RECT)

        mask2 = np.where((mask == 2) | (mask == 0), 0, 1).astype('uint8')
        img_show = img * mask2[:, :, np.newaxis]
        # 显示图片分割后结果--显示原图
        cv2.imshow('grabcut', img_show)
        cv2.imshow('img', img)
        #cv2.imwrite("wq.png", img_copy)
        rows, cols, chs = img_show.shape
        #分离通道
        chB, chG, chR = cv2.split(img_show)
        sontours, hierarchy = cv2.findContours(chR, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
        # 创建结果图,拷贝原图
        result = img_show.copy()
        # # 计算区域像素和
        circle_num = 1
        list_roi = []
        for cnt in sontours:
            area = cv2.contourArea(cnt)
            x, y, w, h = cv2.boundingRect(cnt)
            if area > 2000:
                # 绘制边界框和文本
                cv2.rectangle(result, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.putText(result, "ROI: {:}".format(circle_num),
                (x+w+8, y+h-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                imgROI = img[y:y + h, x:x + w].copy()
                list_roi.append(imgROI)
                cv2.imshow('result', result)
                #cv2.imwrite("wq6.png", imgROI)
                #cv2.imshow('imgROI', imgROI)
                circle_num += 1
        list_mask = []
        list_red = []
        list_green = []

        # for x in range(len(list_roi)):
        #     cv2.imwrite("2.jpg", list_roi[1])
        # for i in range(len(list_roi)):
        #     plt.subplot(2, 4, i + 1), plt.imshow(list_roi[i], 'gray')
        #     plt.title([i+1])
        #     plt.xticks([]), plt.yticks([])
        for j in range(len(list_mask)):
            plt.subplot(2, 5, j + 1), plt.imshow(list_mask[j], cmap='gray')
            plt.title([j + 1])
            plt.xticks([]), plt.yticks([])
        for n in range(len(list_red)):
            print("ROI:", str(n+1) + "  R:", list_red[n], "  G:", list_green[n])
        plt.show()
        # 如果按下q键，则退出循环
    if cv2.waitKey(1) & 0xFF == ord(' '):
        break
cv2.waitKey(0)
cv2.destroyAllWindows()
