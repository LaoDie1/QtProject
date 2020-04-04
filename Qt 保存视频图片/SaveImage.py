#！/usr/bin/env python3
# coding: utf-8

import cv2, os, threading
import numpy as np
from skimage.measure import compare_ssim

"""视频转为图片

@date: 2020-04-04
@version: 1.0
@author: 1693619798@qq.com
"""


class VideoToImage(threading.Thread):

    def __init__(self, filename, ssim=0.99, externalFun=None):
        """保存视频为图片<br>
        @filename: 文件路径<br>
        @ssim: 图片相似度（相似度超过这个值则不保存）
        @externalFun: 更新图像时调用这个函数
        """
        try:
            threading.Thread.__init__(self)  # 没有该语句的话则会出现 RuntimeError: thread.__init__() not called
            self._fileName = filename       # 文件路径
            self._path = os.path.dirname(filename) + "/"   # 文件夹路径
            self._name = os.path.basename(filename)  # 文件
            self._savePath = self._path + self._name.split(".")[0] + "/"   # 保存图片路径
            self.SSIM = ssim                # 相似度
            self._Saving = False            # 运行保存图片的状态（是否在保存图片）
            self._lastFrame = np.array([])
            self.externalFun = externalFun  # 外部用于更新显示图像的函数
        except Exception as e:
            print("设置相关数据时出现错误", str(e))

    def run(self):
        print("开始运行线程")
        self._saveToImage(self.externalFun)
        print("线程结束")

    def setFileName(self, filename):
        """设置当前要保存的文件路径"""
        self._fileName = filename

    def _saveToImage(self, externalFun=None):
        """保存为图片<br>
        @externalFun: 图片保存成功后调用的函数
        """
        if not os.path.exists(self._fileName):
            print(self._fileName, "文件不存在")
            # self._Saving = True
            # while(self._Saving):
            #     print("等待退出", "Test:", self.SSIM)
            #     time.sleep(1)
            return
        try:
            cap = cv2.VideoCapture(self._fileName)
            if not cap.isOpened():
                return
            print("开始保存图片 (视频：%s)" % self._fileName)
            ret, self._lastFrame = cap.read()  # 上一帧图片
            count = 0               # 已保存的图片个数
            self._Saving = True     # 开启保存状态
            if not os.path.exists(self._savePath): # 不存在则创建
                os.mkdir(self._savePath)
            print("保存到", self._savePath)
            while (True):
                ret, frame = cap.read()

                if ret:
                    if not self._Saving:    # 如果停止了保存状态
                        break

                    xsd = self.compareImage(self._lastFrame, frame)  # 相似度
                    if xsd <= self.SSIM:
                        print("相似度：", xsd)
                        count += 1
                        self._lastFrame = frame
                        filename = str.format("%s%05d%s" % (self._savePath, count, ".jpg"))
                        # cv2.imwrite(filename, frame)      # 路径带中文返回 False
                        cv2.imencode('.jpg', frame)[1].tofile(filename)  # 路径带中文需要这样
                        if externalFun is not None:    # 如果外部函数不为空
                            externalFun("保存图片：", filename,  "| 帧位置：", cap.get(cv2.CAP_PROP_POS_FRAMES)) # 传入当前帧位置
                        print("保存图片", filename, "完成")
                else:
                    break
            cap.release()
            externalFun("保存完成。共保存 %d 张图片" % count)
        except Exception as e:
            print("保存视频转为图片时出现了错误", str(e))

    @staticmethod
    def compareImage(image1, image2) -> float:
        """图片相似度"""
        grayA = cv2.cvtColor(image1, cv2.COLOR_BGR2GRAY)  # 图片灰度化
        grayB = cv2.cvtColor(image2, cv2.COLOR_BGR2GRAY)  # 图片灰度化
        (score, diff) = compare_ssim(grayA, grayB, full=True)  # 相似度
        return score  # 返回相似度

    def stop(self):
        """停止保存图片"""
        self._Saving = False

    def isSaving(self):
        """是否正在保存"""
        return self._Saving

    def getLastImage(self):
        """获取上一次的帧"""
        return self._lastFrame


# if __name__ == "__main__":
#     vi = VideoToImage("null", 0.90)
#     vi.start()
#     while (True):
#         a = input("输入字符(输入 q 停止保存图片)")
#         if a == "q":
#             vi.stop()
#             break
