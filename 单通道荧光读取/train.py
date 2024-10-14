#!/usr/bin/python3
# -*- coding: utf-8 -*-
import cv2
import numpy as np
import math


def replaceZeroes(data):
    min_nonzero = min(data[np.nonzero(data)])
    data[data == 0] = min_nonzero
    return data


def simple_color_balance(input_img, s1, s2):
    h, w = input_img.shape[:2]
    out_img = np.zeros([h, w])
    sort_img = input_img.copy()
    one_dim_array = sort_img.flatten()  # 转化为一维数组
    sort_array = sorted(one_dim_array)  # 对一维数组按升序排序

    per1 = int((h * w) * s1 / 100)
    minvalue = sort_array[per1]

    per2 = int((h * w) * s2 / 100)
    maxvalue = sort_array[(h * w) - 1 - per2]

    # 实施简单白平衡算法
    if (maxvalue <= minvalue):
        for i in range(h):
            for j in range(w):
                out_img[i, j] = maxvalue
    else:
        scale = 255.0 / (maxvalue - minvalue)
        for m in range(h):
            for n in range(w):
                if (input_img[m, n] < minvalue):
                    out_img[m, n] = 0
                elif (input_img[m, n] > maxvalue):
                    out_img[m, n] = 255
                else:
                    out_img[m, n] = scale * (input_img[m, n] - minvalue)  # 映射中间段的图像像素

    out_img = cv2.convertScaleAbs(out_img)
    return out_img


def MSRCR(img, scales, s1, s2):
    h, w = img.shape[:2]
    # print(h, w)
    scles_size = len(scales)
    img = np.array(img, dtype=np.float64)
    # print(img)
    log_R = np.zeros((h, w), dtype=np.float64)
    img_sum = np.add(img[:, :, 0], img[:, :, 1], img[:, :, 2])
    # print(img_sum)
    # print("11111111111111111111111111111111")
    img_sum = replaceZeroes(img_sum)
    # print(img_sum)
    gray_img = []

    for j in range(3):
        img[:, :, j] = replaceZeroes(img[:, :, j])
        for i in range(0, scles_size):
            L_blur = cv2.GaussianBlur(img[:, :, j], (scales[i], scales[i]), 0)
            L_blur = replaceZeroes(L_blur)

            dst_img = cv2.log(img[:, :, j])
            dst_Lblur = cv2.log(L_blur)
            # dst_ixl = cv2.multiply(dst_img, dst_Lblur)
            log_R += cv2.subtract(dst_img, dst_Lblur)
            # print(i)
        # print(scles_size)
        MSR = log_R / 3.0
        '''
            img_sum_log = np.zeros((h, w))
            for i in range(0, h):
                for k in range(0, w):
                    img_sum_log[i,k] = 125.0*math.log(img[i,k,j]) - math.log(img_sum[i,k])
            MSRCR = MSR * (img_sum_log[:, :])
            print(img_sum)
            # x = cv2.log(img_sum)
            '''
        MSRCR = MSR * (cv2.log(125.0 * img[:, :, j]) - cv2.log(img_sum))
        gray = simple_color_balance(MSRCR, s1, s2)
        gray_img.append(gray)

    return gray_img



if __name__ == '__main__':
    scales = [15, 101, 301]
    s1, s2 = 2, 3
    src_img = cv2.imread('C:/Users/Shinelon/Desktop/IFIR_100_TMP/18.png')
    src_img = cv2.cvtColor(src_img, cv2.COLOR_BGR2RGB)
    cv2.imshow('img', src_img)
    MSRCR_Out = MSRCR(src_img, scales, s1, s2)

    result = cv2.merge([MSRCR_Out[0], MSRCR_Out[1], MSRCR_Out[2]])

    cv2.imshow('MSR_result', result)
    cv2.waitKey(0)
    cv2.destroyAllWindows()