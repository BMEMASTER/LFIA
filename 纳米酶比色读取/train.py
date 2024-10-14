#!/usr/bin/python3
# -*- coding: utf-8
import torch
import cv2 as cv
filename = "C:\\Users\\Shinelon\\Desktop\\images\\01.jpg"
srcImg = cv.imread(filename, 1)
cv.imshow("src", srcImg)