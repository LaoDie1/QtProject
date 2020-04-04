#!/usr/bin/env python3
# coding: utf-8

import cv2, os, threading, time
from PyQt5.QtCore import pyqtSlot, Qt
from PyQt5.QtWidgets import QApplication, QMainWindow, QGraphicsScene, QGraphicsPixmapItem, QFileDialog, QMessageBox
from PyQt5.QtGui import QImage, QPixmap

import Ui_picshow
import SaveImage


setting = os.getcwd() + "/" + "setting.ini"  # 配置文件


class videoShow(QMainWindow, Ui_picshow.Ui_MainWindow):

    def __init__(self, parent=None):
        """Constructor<br>
        @param parent reference to the parent widget
        @type QMainWindow
        """
        super(videoShow, self).__init__(parent)
        self.setAcceptDrops(True)       # 接收拖拽
        self.scene = QGraphicsScene()   # 创建场景
        self.setupUi(self)
        self.cap = None                 # 读取的视频
        self.currentIndex = -1          # 当前第几帧
        self.filename = ""              # 当前视频路径
        self.frameCount = 0             # 视频帧数
        self.second = 0                 # 秒数
        self.fps = 0                    # 帧率
        self.lastFrame = None           # 上一个帧（用于比较相似度）
        if self.getSetting() == "":
            self.lastFileDir = os.getcwd() + "/"  # 打开文件的初始路径
        else:
            self.lastFileDir = self.getSetting()
        self.SSIM = 0.99                # 保存图片相似度
        self.vi = None                  # 保存视频帧操控器

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls:
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        """接收拖拽数据"""
        try:
            filename = event.mimeData().urls()[0].toLocalFile()
            if os.path.exists(filename):
                self.readVideo(filename)
        except Exception as e:
            print("dropEvent:", e)

    # =========================================
    #  自定义方法
    # =========================================
    def readVideo(self, filename):
        """读取视频<br>
        @filename 文件名
        @index 视频帧
        """
        try:
            if self.cap is not None:
                self.cap.release()  # 释放上一个视频
                self.scene.deleteLater()    # 清空上次显示的图片（否则有残留）
                self.scene = QGraphicsScene()  # 创建场景
            self.filename = filename
            self.cap = cv2.VideoCapture(self.filename)  # 读取视频
            self.frameCount = self.cap.get(cv2.CAP_PROP_FRAME_COUNT) - 2  # 视频帧数
            self.fps = self.cap.get(cv2.CAP_PROP_FPS)  # 帧速
            self.second = int(self.frameCount / self.fps)
            self.timeLine.setValue(0)
            self.frameBox.setValue(0)
            self.timeLine.setMaximum(self.frameCount)  # 滑条最大值
            self.frameBox.setMaximum(self.frameCount)
            self.showMessage("读取视频:", self.filename)
            self.showMessage("视频信息：\n - 帧数：%d\n - 秒数：%d\n - 帧速率：%d" % (self.frameCount, self.second, self.fps))
            self.readFrame()
            return True
        except Exception as e:
            self.showMessage("读取视频时出现错误", str(e))
            return False

    def readFrame(self, index=0) -> bool:
        """读取某一帧"""
        if self.filename == "":  # 没有文件则退出
            return
        try:
            if self.cap is None:
                self.cap = cv2.VideoCapture(self.filename)  # 读取视频
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, index)  # 定位到某一帧图片
            ret, img = self.cap.read()
            if ret:
                img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)  # BGR 转换为 RGB 颜色
                # 更新变量
                self.currentIndex = index
                self.timeLabel.setText(str(index) + " | " + str(self.frameCount))
                if self.timeLine.value() != index:
                    self.timeLine.setValue(index)
                if self.frameBox.value() != index:
                    self.frameBox.setValue(index)
            else:  # 没有读取到图片，退出
                self.cap.release()  # 释放内存
                return False
        except Exception as e:
            print("读取视频出现问题", str(e))
            return False
        # finally:
        #     self.cap.release()
        # 显示图像
        self.showGraphView(img)

    def showGraphView(self, img):
        """展示图片到图形视图中
        @img: 展示的图片
        """
        try:
            x = img.shape[1]
            y = img.shape[0]
            f = QImage(img, x, y, QImage.Format_RGB888)
            pix = QPixmap.fromImage(f)
            item = QGraphicsPixmapItem(pix)  # 创建像素图元
            self.scene.addItem(item)
            self.graphicsView.setScene(self.scene)  # 将场景添加至视图
            self.showMessage("当前帧位置：", self.currentIndex)
            return True
        except AttributeError as e:
            self.showMessage("显示图像时出现错误：", str(e))
            return False

    # =========================================
    #  控件操作
    # =========================================
    @pyqtSlot()
    def on_last_clicked(self):
        """点击上一帧图片"""
        if self.frameCount == 0:
            return

        if self.currentIndex > 0:
            self.currentIndex -= 1
            self.readFrame(self.currentIndex)
        else:
            self.showMessage("没有图片了")

    @pyqtSlot()
    def on_next_clicked(self):
        """点击下一帧图片"""
        if self.frameCount == 0:
            return

        if self.currentIndex < self.frameCount - 1:
            self.currentIndex += 1
            self.readFrame(self.currentIndex)
        else:
            self.showMessage("没有图片了")

    @pyqtSlot()
    def on_lastSecond_clicked(self):
        """上一秒"""
        if self.currentIndex == 0:
            print("上一秒没有帧了", self.currentIndex)
            return
        if self.currentIndex < self.fps:
            self.currentIndex = 0
        else:
            self.currentIndex -= self.fps
        self.readFrame(self.currentIndex)

    @pyqtSlot()
    def on_nextSecond_clicked(self):
        """下一秒"""
        if self.currentIndex == self.frameCount - 1:
            print("下一秒没有帧了")
            return
        if self.currentIndex > self.frameCount - self.fps:
            self.currentIndex = int(self.frameCount - 1)
        else:
            self.currentIndex += int(self.fps)
        self.readFrame(self.currentIndex)

    @pyqtSlot(int)
    def on_timeLine_valueChanged(self, value):
        try:
            if self.currentIndex == value:
                return
            self.currentIndex = value
            self.readFrame(self.currentIndex)
        except Exception as e:
            print("滚动条时出现问题", e)

    @pyqtSlot(float)
    def on_doubleSpinBox_valueChanged(self, value):
        s = str.format("%.2f" % value)  # 保留两位小数
        self.doubleSpinBox.setValue(float(s))
        print("更改相似度阈值", s)

    # =========================================
    #  菜单 - 文件
    # =========================================
    @pyqtSlot()
    def on_actionOpen_triggered(self):
        """菜单 - 打开文件"""
        # try:
        f = QFileDialog()
        f.setWindowModality(Qt.WindowModal)
        print(self.lastFileDir)
        t, _ = f.getOpenFileName(self, caption="选取文件", filter="MP4(*.mp4);AVI(*.avi);FLV(*.flv);;All files(*.*)",
                                 directory=self.lastFileDir)
        if t:
            self.showMessage(self, "打开文件", t)
            self.lastFileDir = getDir(t)
            self.updateSetting(t)
            print("下一次打开的位置", self.lastFileDir)
            self.readVideo(t)
        # except Exception as e:
        #     print("出现问题", str(e))


    @pyqtSlot()
    def on_actionSave_triggered(self):
        """菜单 - 保存所有视频帧"""
        if self.filename == "":
            print("没有文件")
            return
        path = os.path.dirname(self.filename) + "/" + os.path.basename(self.filename).split(".")[0]
        if os.path.exists(path):    # 如果文件已存在
            reply = QMessageBox.information(self, '重新保存', '文件已经保存过，是否覆盖上次保存的内容？',
                                            QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
            if reply == QMessageBox.No:
                print("取消保存")
                return
        try:
            # 保存图片控制器
            self.showMessage("> 开始保存图片(刚开始可能会等待几秒)(视频越大识别图片相似度时间越长)")
            self.vi = SaveImage.VideoToImage(self.filename, self.doubleSpinBox.value(), self.showMessage)
            self.vi.start()
        except Exception as e:
            self.showMessage("开始保存图片时出现错误", str(e))

    @pyqtSlot()
    def on_actionStop_triggered(self):
        """停止保存视频为图片"""
        try:
            if self.vi is None:
                return
            self.vi.stop()
            self.showMessage("> 停止保存视频帧")
        except Exception as e:
            self.showMessage("停止时出现错误", str(e))

    # =========================================
    #  菜单 - 视频帧
    # =========================================
    @pyqtSlot()
    def on_action_H_triggered(self):
        """菜单 - 上一秒"""
        self.on_lastSecond_clicked()
        self.showMessage("菜单：上一秒")

    @pyqtSlot()
    def on_action_L_triggered(self):
        """菜单 - 下一秒"""
        self.on_nextSecond_clicked()
        self.showMessage("菜单：下一秒")

    @pyqtSlot()
    def on_action_J_triggered(self):
        """菜单 - 上一帧"""
        self.on_last_clicked()
        self.showMessage("菜单：上一帧")

    @pyqtSlot()
    def on_action_K_triggered(self):
        """菜单 - 下一帧"""
        self.on_next_clicked()
        self.showMessage("菜单：下一帧")

    # =========================================
    #  方法
    # =========================================
    def showMessage(self, *text):
        """显示信息"""
        msg = " ".join([str(i) for i in text])
        self.statusBar.showMessage(msg)
        print(msg)

    def toSecond(self, sec=0) -> int:
        """返回第几秒"""
        if self.fps == 0:
            return 0
        if sec == 0:
            sec = self.currentIndex
        return sec / self.fps

    def releaseCap(self):
        """释放当前视频"""
        if self.cap is not None:
            self.cap.release()

    def getSetting(self):
        """获取上一次路径"""
        if not os.path.exists(setting):
            return ""
        with open(setting, 'r') as f:
            t = f.read()
        return t

    def updateSetting(self, filePath=""):
        """更新配置文件路径"""
        with open(setting, 'w') as f:
            if filePath == "":
                f.write(self.lastFileDir)
            else:
                f.write(filePath)

def getDir(fileName):
    """获取路径<br>
    @fileName: 文件路径
    """
    if fileName == "" and fileName is None:
        return
    return os.path.dirname(fileName)


def main():
    import sys
    app = QApplication(sys.argv)
    win = videoShow()
    # win.readVideo(r"E:\官方推荐视频教程\godot.fps.mp4")  # 读取视频中的帧
    win.showMaximized()
    win.show()
    win.releaseCap()  # 释放内存
    app.exec_()


if __name__ == "__main__":
    main()
