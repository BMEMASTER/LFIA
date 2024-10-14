# -*- coding: utf-8 -*-
import sys
from PyQt5.QtWidgets import QDialog, QPushButton, QApplication
from PyQt5.QtGui import QPixmap, QMovie
from PyQt5.QtCore import QTimer, Qt, pyqtSlot, pyqtSignal
from Ui_WaitDialog import Ui_WaitDialog
from Ui_MessageBox import Ui_MessageBox
from Ui_KeyboardDialog import Ui_KeyboardDialog


class WaitDialog(QDialog):
    """ 等待对话框 """
    def __init__(self, parent=None, msg="请稍后..."):
        super(WaitDialog, self).__init__(parent)
        self.ui = Ui_WaitDialog()
        self.ui.setupUi(self)
        self.timer = QTimer()
        # this->setWindowFlags(Qt::Dialog | Qt::FramelessWindowHint);
        # if (parent != nullptr) {
        # this->setWindowTitle(parent->windowTitle());
        # }
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        if parent is not None:
            self.setWindowTitle(parent.windowTitle())
        movie = QMovie(":/images/wait.gif")
        self.ui.label.setMovie(movie)
        self.ui.titleLabel.setText(msg)
        movie.start()

    def start(self, timeVal: int):
        if timeVal > 0:
            self.timer.timeout.connect(self.accept)
            self.timer.start(timeVal)
        self.exec()


class MessageBox(QDialog):
    """ 消息对话框 """
    def __init__(self, icon: QPixmap,  parent=None, title="", text="", acceptBtn=None, rejectBtn=None):
        super().__init__(parent)
        self.ui = Ui_MessageBox()
        self.ui.setupUi(self)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.ui.logoLabel.setPixmap(icon)
        self.ui.titleLabel.setText(title)
        self.ui.msgLabel.setText(text)
        if acceptBtn is not None:
            self.ui.acceptBtn.setText(acceptBtn)
        else:
            self.ui.acceptBtn.hide()
        if rejectBtn is not None:
            self.ui.rejectBtn.setText(rejectBtn)
        else:
            self.ui.rejectBtn.hide()

    @staticmethod
    def information(parent=None, title="", text="", acceptBtn=None, rejectBtn=None):
        icon = QPixmap(":/images/info.svg")
        box = MessageBox(icon, parent, title, text, acceptBtn, rejectBtn)
        return box.exec()

    @staticmethod
    def warning(parent=None, title="", text="", acceptBtn=None, rejectBtn=None):
        icon = QPixmap(":/images/warning.svg")
        box = MessageBox(icon, parent, title, text, acceptBtn, rejectBtn)
        return box.exec()

    @staticmethod
    def error(parent=None, title="", text="", acceptBtn=None, rejectBtn=None):
        icon = QPixmap(":/images/error.svg")
        box = MessageBox(icon, parent, title, text, acceptBtn, rejectBtn)
        return box.exec()

    @staticmethod
    def question(parent=None, title="", text="", acceptBtn=None, rejectBtn=None):
        icon = QPixmap(":/images/question.svg")
        box = MessageBox(icon, parent, title, text, acceptBtn, rejectBtn)
        return box.exec()


class KeyboardDialog(QDialog):
    """ 小键盘 """
    # 定义信号
    inputKey = pyqtSignal(str)

    def __init__(self, parent=None):
        super(KeyboardDialog, self).__init__(parent)
        self.ui = Ui_KeyboardDialog()
        self.ui.setupUi(self)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        # 记录键盘输入的数据
        self.text = ""
        # 连接信号与槽函数
        self.__connectSlot__()

    def __connectSlot__(self):
        btns = self.ui.frame.findChildren(QPushButton)
        for btn in btns:
            btn.clicked.connect(self.btnClicked)

    def show(self):
        if self.isVisible() is False:
            parent = self.parent()
            if parent is not None:
                parentPos = parent.pos()
                parentSize = parent.size()
                size = self.size()
                self.move(0, parentSize.height() - size.height())
            super().show()
        self.text = ""

    @pyqtSlot()
    def btnClicked(self):
        # pushButton_25 ←
        # pushButton_12 确定
        # 获取当前点击的按钮
        btn = self.sender()
        # 获取按钮的名称
        btnName = btn.objectName()
        if btnName.endswith("25"):  # 删除按钮
            self.inputKey.emit("delete")
        elif btnName.endswith("12"):    # 确定
            self.accept()
        elif btnName.endswith("11"):    # 清空
            self.inputKey.emit("clear")
        else:
            # 获取按钮上的符号
            self.inputKey.emit(btn.text())


if __name__ == "__main__":
    app = QApplication(sys.argv)
    dlg = KeyboardDialog()
    dlg.exec()
    sys.exit(app.exec())