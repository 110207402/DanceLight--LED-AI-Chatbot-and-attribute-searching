# -*- coding: utf-8 -*-
import os
import sys

# 【修正 WinError 1114】環境補丁
# 強制禁用 GPU，避免 torch 試圖加載 CUDA 相關 DLL 導致初始化失敗
os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
# 確保 Python 優先在當前目錄尋找依賴項
if hasattr(os, 'add_dll_directory'):
    current_dir = os.path.dirname(os.path.abspath(__file__))
    os.add_dll_directory(current_dir)

from PyQt5 import QtCore, QtGui, QtWidgets

# 延遲導入，避免循環引用
def get_home_page():
    try:
        from homePage import MainWindow
        return MainWindow
    except ImportError:
        return None

def get_ai_chat_page():
    try:
        from ai_chat_page import AIChatPage
        return AIChatPage
    except ImportError:
        return None

class Ui_ModelSearchWindow(object):
    def setupUi(self, ModelSearchWindow):
        ModelSearchWindow.setObjectName("ModelSearchWindow")
        ModelSearchWindow.resize(600, 700)
        self.centralwidget = QtWidgets.QWidget(ModelSearchWindow)
        
        # 主垂直布局
        self.verticalLayout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.verticalLayout.setContentsMargins(15, 15, 15, 15)
        self.verticalLayout.setSpacing(15)

        # 頂部導航欄
        self.top_frame = QtWidgets.QFrame(self.centralwidget)
        self.top_layout = QtWidgets.QHBoxLayout(self.top_frame)
        self.top_layout.setContentsMargins(0, 0, 0, 0)

        self.back_home_button = QtWidgets.QPushButton("回到首頁")
        self.back_home_button.setObjectName("back_home_button")
        self.back_home_button.setFixedSize(160, 60)
        
        self.logo_label = QtWidgets.QLabel()
        self.logo_label.setPixmap(QtGui.QPixmap("dancelight_logo.jpg"))
        self.logo_label.setScaledContents(True)
        self.logo_label.setFixedSize(120, 60)
        
        self.go_ai_button = QtWidgets.QPushButton("AI 客服")
        self.go_ai_button.setObjectName("go_ai_button")
        self.go_ai_button.setFixedSize(160, 60)

        self.top_layout.addWidget(self.back_home_button, alignment=QtCore.Qt.AlignLeft)
        self.top_layout.addStretch()
        self.top_layout.addWidget(self.logo_label, alignment=QtCore.Qt.AlignCenter)
        self.top_layout.addStretch()
        self.top_layout.addWidget(self.go_ai_button, alignment=QtCore.Qt.AlignRight)

        self.verticalLayout.addWidget(self.top_frame)

        # 搜尋區
        self.search_frame = QtWidgets.QFrame(self.centralwidget)
        self.search_layout = QtWidgets.QHBoxLayout(self.search_frame)
        self.search_layout.setContentsMargins(0, 0, 0, 0)

        self.search_input = QtWidgets.QLineEdit()
        self.search_input.setPlaceholderText("請輸入型號 (例如: LED-15W)...")
        self.search_input.setFixedHeight(60)
        self.search_input.setFixedWidth(350)
        self.search_input.setObjectName("search_input")
        
        self.search_button = QtWidgets.QPushButton("查詢")
        self.search_button.setObjectName("search_button")
        self.search_button.setFixedSize(100, 60)
        
        self.search_layout.addWidget(self.search_input)
        self.search_layout.addWidget(self.search_button)

        # 初始置中空間
        self.top_spacer = QtWidgets.QSpacerItem(20, 0, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.bottom_spacer = QtWidgets.QSpacerItem(20, 0, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.verticalLayout.addItem(self.top_spacer)
        self.verticalLayout.addWidget(self.search_frame, alignment=QtCore.Qt.AlignCenter)
        self.verticalLayout.addItem(self.bottom_spacer)

        # 結果區
        self.result_area = QtWidgets.QScrollArea(self.centralwidget)
        self.result_area.setObjectName("result_area")
        self.result_area.setWidgetResizable(True)
        self.result_content = QtWidgets.QWidget()
        self.result_layout = QtWidgets.QVBoxLayout(self.result_content)
        self.result_layout.setAlignment(QtCore.Qt.AlignTop)
        self.result_area.setWidget(self.result_content)
        self.result_area.hide()

        self.verticalLayout.addWidget(self.result_area)
        self.verticalLayout.setStretchFactor(self.result_area, 1)

        ModelSearchWindow.setCentralWidget(self.centralwidget)

class ModelSearchPage(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_ModelSearchWindow()
        self.ui.setupUi(self)
        self.apply_style()

        # 綁定事件
        self.ui.search_button.clicked.connect(self.run_search)
        self.ui.search_input.returnPressed.connect(self.run_search)
        self.ui.back_home_button.clicked.connect(self.go_home)
        self.ui.go_ai_button.clicked.connect(self.go_ai_chat)

    def apply_style(self):
        qss = """
        QWidget { background-color: white; font-family: "Microsoft JhengHei"; font-size: 16px; }
        #search_input { border: 2px solid #cccccc; border-radius: 12px; padding: 12px; font-size: 16px; }
        #search_input:focus { border: 2px solid #185ca1; }
        #search_button { background-color: #185ca1; color: white; border-radius: 12px; font-weight: bold; }
        #search_button:hover { background-color: #f17039; }
        #result_area { background-color: #f9f9f9; border-radius: 12px; border: 1px solid #dddddd; }
        #result_card { background-color: #f7f7f7; border-radius: 12px; padding: 10px; border: 1px solid #dddddd; margin-bottom: 10px; }
        #result_title { font-size: 16px; font-weight: bold; color: #185ca1; }
        #result_desc { font-size: 14px; color: #444444; }
        #back_home_button, #go_ai_button {
            background-color: white; color: #185ca1; border: 2px solid white; border-radius: 8px;
            font-size: 19px; font-weight: bold;
        }
        #back_home_button:hover, #go_ai_button:hover {
            border: 2px solid #ccc; color: #f17039;
            background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #cccccc, stop:1 #ffffff);
        }
        """
        self.setStyleSheet(qss)

    def run_search(self):
        keyword = self.ui.search_input.text().strip()
        if not keyword: return

        # 動態效果
        self.animate_search_and_results()

        # 清除舊結果
        for i in reversed(range(self.ui.result_layout.count())):
            widget = self.ui.result_layout.itemAt(i).widget()
            if widget: widget.deleteLater()

        self.ui.result_area.show()

        # 這裡可以串接你的資料庫或型號 CSV
        fake_results = [
            {"name": f"{keyword} 節能燈組", "desc": "舞光高效能系列，省電 50%", "img": "dancelight_logo.jpg"},
            {"name": f"{keyword} 智慧平板燈", "desc": "支援遙控調光調色，適合辦公室", "img": "dancelight_logo.jpg"},
        ]

        for item in fake_results:
            card = self.create_result_card(item["name"], item["desc"], item["img"])
            self.ui.result_layout.addWidget(card)

    def animate_search_and_results(self):
        """搜尋框上滑動畫"""
        start_rect = self.ui.search_frame.geometry()
        top_btn_bottom = self.ui.top_frame.geometry().bottom()
        end_y = top_btn_bottom + 20
        end_rect = QtCore.QRect(start_rect.x(), end_y, start_rect.width(), start_rect.height())

        self.anim = QtCore.QPropertyAnimation(self.ui.search_frame, b"geometry")
        self.anim.setDuration(500)
        self.anim.setStartValue(start_rect)
        self.anim.setEndValue(end_rect)
        self.anim.setEasingCurve(QtCore.QEasingCurve.OutCubic)
        self.anim.start()

    def create_result_card(self, title, desc, image_path):
        frame = QtWidgets.QFrame()
        frame.setObjectName("result_card")
        layout = QtWidgets.QHBoxLayout(frame)
        
        img_label = QtWidgets.QLabel()
        pixmap = QtGui.QPixmap(image_path) if os.path.exists(image_path) else QtGui.QPixmap(100, 100)
        img_label.setPixmap(pixmap)
        img_label.setScaledContents(True)
        img_label.setFixedSize(80, 80)

        text_layout = QtWidgets.QVBoxLayout()
        t_label = QtWidgets.QLabel(f"📦 {title}")
        t_label.setObjectName("result_title")
        d_label = QtWidgets.QLabel(f"💡 {desc}")
        d_label.setObjectName("result_desc")
        d_label.setWordWrap(True)

        text_layout.addWidget(t_label)
        text_layout.addWidget(d_label)
        layout.addWidget(img_label)
        layout.addLayout(text_layout)
        return frame

    def go_home(self):
        Home = get_home_page()
        if Home:
            self.home_window = Home()
            self.home_window.show()
            self.close()

    def go_ai_chat(self):
        Chat = get_ai_chat_page()
        if Chat:
            self.chat_window = Chat()
            self.chat_window.show()
            self.close()

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = ModelSearchPage()
    window.show()
    sys.exit(app.exec_())