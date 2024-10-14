# -*- coding: utf-8 -*-
import cv2 as cv
import os


img = cv.imread("/home/pi/Desktop/1.bmp")
cv.imshow("src", img)
cv.waitKey()