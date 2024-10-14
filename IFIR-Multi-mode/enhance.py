import numpy as np
import cv2


class CLAHE:

    def __init__(self, clipLimit=40.0, tileGridSize=(16, 16)):
        self.clipLimit = clipLimit
        self.tileGridSize = tileGridSize

    def __call__(self, src):

        img = cv2.normalize(src, None, 0, 255, cv2.NORM_MINMAX, cv2.CV_8U)
        h, w = img.shape[:2]
        tileH, tileW = self.tileGridSize

        clipHist = np.zeros(256, dtype=np.int32)
        finalHist = np.zeros(256, dtype=np.int32)

        for j in range(0, h, tileH):
            for i in range(0, w, tileW):
                tile = img[j:j + tileH, i:i + tileW]
                hist, bins = np.histogram(tile, bins=list(range(257)), range=(0, 256))

                clipHist = np.clip(hist, 0, self.clipLimit)
                finalHist += clipHist

        finalHist = (finalHist * 255) // (h * w)

        lut = np.zeros((256, 1), dtype=np.uint8)
        for i in range(256):
            lut[i] = min(255, int(255 * i / finalHist[-1]))

        dst = cv2.LUT(img, lut)

        return dst


# 测试
img = cv2.imread(r"C:\Users\Shinelon\Desktop\IFIR_100_TMP\1 (2).png", 0)
clahe = CLAHE()
result = clahe(img)

cv2.imshow('result', result)
cv2.waitKey(0)