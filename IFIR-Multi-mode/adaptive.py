import cv2
import numpy as np
# 限制对比度自适应直方图均衡化CLAHE
def clahe(image):
    b, g, r = cv2.split(image)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(5, 5))
    #b = clahe.apply(b)
    #g = clahe.apply(g)
    r = clahe.apply(r)
    image_clahe = cv2.merge([b, g, r])
    kernel = (3, 3)
    image_clahe = cv2.GaussianBlur(image_clahe, kernel, sigmaX=5, sigmaY=5)
    return image_clahe
# 读取测试纸条图像
#img = cv2.imread('C:\\Users\\Shinelon\\Desktop\\IFIR_100_TMP\\16.jpg')
def mask(img):
    #img = cv2.resize(img, (400, 600))

    #img = clahe(img)
    #cv2.imshow('img', img)
    # 分离通道
    chB, chG, chR = cv2.split(img)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    white_img = np.full(gray.shape, 255, dtype=np.uint8)
    gray = white_img - gray
    #ret, thresh = cv2.threshold(chR, 115, 255, cv2.THRESH_BINARY)
    #ret, thresh2 = cv2.threshold(chB, 110, 255, cv2.THRESH_BINARY)
    thresh = cv2.adaptiveThreshold(chR, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 671, -35)
    # thresh2 = cv2.Canny(chB, 90, 100)
    # 腐蚀操作
    kernel = np.ones((11, 11), np.uint8)
    kernel1 = np.ones((10, 10), np.uint8)
    erode = cv2.erode(thresh, kernel, iterations=1)
    erode = cv2.dilate(erode, kernel1)
    cv2.imshow("erode", erode)
    cv2.imwrite('C:\\Users\\Shinelon\\Desktop\\IFIR_100_TMP\\123\\002.png', erode)
    # 检测轮廓
    contours, hierarchy = cv2.findContours(erode, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    #contours1, _ = cv2.findContours(erode1, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    # 创建结果图,拷贝原图
    result = img.copy()
    # 绘制所有轮廓
    # for i, cnt in enumerate(contours):
    #     cv2.drawContours(result, cnt, -1, (0, 255, 0), 2)
    # cv2.imshow("result", result)
    img_mask = cv2.bitwise_and(result, result, mask=erode)
    #chR_mask = cv2.bitwise_and(gray, gray, mask=erode)
    gray_mask = cv2.bitwise_and(gray, gray, mask=erode)
    return contours, img_mask, img, chR

def getval(contours, img_mask, img, chR):
    circle_num = 0
    ROI = []
    R = []
    G = []
    B = []
    for cnt in contours:
        area = cv2.contourArea(cnt)
        x, y, w, h = cv2.boundingRect(cnt)
        perimeter = cv2.arcLength(cnt, True)
        # 计算圆形度
        circularity = (4 * np.pi * area) / (perimeter ** 2)
        rect_area = w * h
        # 判断是否类似圆形
        if 0.75 < circularity < 1.25 and area > 750 and abs(area - rect_area) / area < 0.9:
            cv2.drawContours(img_mask, cnt, -1, (0, 255, 0), 2)
            # 绘制边界框和文本

            #cv2.rectangle(img, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(img_mask, "ROI:{:}".format(circle_num), (x + w, y + h-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
            #cv2.putText(img, "ROI:{:}".format(circle_num), (x + w, y + h - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5,(0, 255, 0), 1)
            cv2.imshow("src", img)
            # cv2.imshow('img_mask', img_mask)
            #roi_gray = gray[y:y + h, x:x + w]
            #roi_gray = cv2.rotate(roi_gray, cv2.ROTATE_90_COUNTERCLOCKWISE)
            #roi_g = chG[y:y + h, x:x + w]
            #roi_B = chB[y:y + h, x:x + w]
            roi_r = chR[y:y + h, x:x + w]
            #cv2.imshow('roi_r', roi_r)
            #circle_R = np.sum(roi_r)
            sum_gray = 0
            for i in range(w):
                for j in range(h):
                    if roi_r[j, i] != 0:
                        sum_gray = sum_gray + roi_r[j, i]
            # circle_G = np.sum(roi_g)
            # circle_B = np.sum(roi_B)
            ROI.append(circle_num)
            R.append(int(sum_gray/w))
            # G.append(circle_G/w)
            # B.append(circle_B/w-di_B/w)
            #print('ROI ' + str(circle_num) + ' R:', int(circle_gray/w))
            circle_num += 1
    return ROI, R
if __name__ == "__main__":
    # 读取测试纸条图像
    img = cv2.imread(r'C:\\Users\\Shinelon\\Desktop\\IFIR_100_TMP\\123\\003.png')
    img = cv2.resize(img, (945, 150))
    cv2.imwrite('C:\\Users\\Shinelon\\Desktop\\IFIR_100_TMP\\123\\004.png', img)
    #cv2.imshow("src", img)
    contours, img_mask, chR_mask, gray = mask(img)

    num, val = getval(contours, img_mask, chR_mask, gray)
    cv2.imshow("img_mask", img_mask)
    # cv2.imshow("chR_mask", chR_mask)
    for x in range(len(val)):
        print('ROI {}:{}'.format(x, val[x]-3201))

        #cv2.destroyAllWindows()
    #cv2.imshow('img_mask', img_mask)
    cv2.waitKey()