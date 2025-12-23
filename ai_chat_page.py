# -*- coding: utf-8 -*-
import sys
import os
import torch
from PyQt5 import QtCore, QtGui, QtWidgets

# 導入 RAG 類別與配置
from docling_rag_v5 import DoclingRAGSystem, DoclingRAGConfig

# ---------- 後台運算執行緒 ----------
class RAGWorker(QtCore.QThread):
    """處理 AI 檢索與回答，避免介面卡頓"""
    answer_ready = QtCore.pyqtSignal(dict)

    def __init__(self, rag_system, question):
        super().__init__()
        self.rag_system = rag_system
        self.question = question

    def run(self):
        # 呼叫 docling_rag_v5 裡的 query 功能
        result = self.rag_system.query(self.question)
        self.answer_ready.emit(result)

# ---------- 介面佈局類別 ----------
class Ui_AIChatWindow(object):
    def setupUi(self, AIChatWindow):
        AIChatWindow.setObjectName("AIChatWindow")
        AIChatWindow.resize(600, 700)
        
        self.centralwidget = QtWidgets.QWidget(AIChatWindow)
        self.verticalLayout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.verticalLayout.setContentsMargins(15, 15, 15, 15)
        self.verticalLayout.setSpacing(10)

        # 頂部欄
        self.top_button_frame = QtWidgets.QFrame(self.centralwidget)
        self.top_button_layout = QtWidgets.QHBoxLayout(self.top_button_frame)
        
        self.back_home_button = QtWidgets.QPushButton("回到首頁")
        self.back_home_button.setObjectName("back_home_button")
        self.back_home_button.setFixedSize(160, 60)
        
        self.logo_label = QtWidgets.QLabel()
        self.logo_label.setPixmap(QtGui.QPixmap("dancelight_logo.jpg"))
        self.logo_label.setScaledContents(True)
        self.logo_label.setFixedSize(120, 60)
        
        self.go_model_button = QtWidgets.QPushButton("型號查詢")
        self.go_model_button.setObjectName("go_model_button")
        self.go_model_button.setFixedSize(160, 60)

        self.top_button_layout.addWidget(self.back_home_button)
        self.top_button_layout.addStretch()
        self.top_button_layout.addWidget(self.logo_label)
        self.top_button_layout.addStretch()
        self.top_button_layout.addWidget(self.go_model_button)
        self.verticalLayout.addWidget(self.top_button_frame)

        # 聊天顯示區
        self.chat_display = QtWidgets.QScrollArea(self.centralwidget)
        self.chat_display.setObjectName("chat_display")
        self.chat_display.setWidgetResizable(True)
        self.chat_display_content = QtWidgets.QWidget()
        self.chat_display_layout = QtWidgets.QVBoxLayout(self.chat_display_content)
        self.chat_display_layout.setAlignment(QtCore.Qt.AlignTop)
        self.chat_display.setWidget(self.chat_display_content)
        self.verticalLayout.addWidget(self.chat_display)

        # 輸入區
        self.input_frame = QtWidgets.QFrame(self.centralwidget)
        self.input_frame.setObjectName("input_frame")
        self.input_layout = QtWidgets.QHBoxLayout(self.input_frame)
        
        self.input_text = QtWidgets.QLineEdit()
        self.input_text.setPlaceholderText("系統初始化中...")
        self.input_layout.addWidget(self.input_text)

        self.send_button = QtWidgets.QPushButton("發送")
        self.send_button.setObjectName("send_button")
        self.input_layout.addWidget(self.send_button)
        
        self.verticalLayout.addWidget(self.input_frame)
        AIChatWindow.setCentralWidget(self.centralwidget)

# ---------- 主程式邏輯 ----------
class AIChatPage(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_AIChatWindow()
        self.ui.setupUi(self)
        
        # 1. 載入 QSS 樣式
        self.load_qss()

        # 2. 初始介面狀態
        self.ui.input_text.setEnabled(False)
        self.ui.send_button.setEnabled(False)

        # 3. 綁定按鈕事件
        self.ui.send_button.clicked.connect(self.send_message)
        self.ui.input_text.returnPressed.connect(self.send_message) # 按下 Enter 也能發送

        # 4. 延遲載入 RAG (讓視窗先出現)
        QtCore.QTimer.singleShot(100, self.init_rag_after_show)

    def load_qss(self):
        # 這裡直接嵌入你提供的 QSS 內容
        qss = """
        QWidget { background-color: white; font-family: "Microsoft JhengHei"; font-size: 16px; }
        #chat_display { background-color: #f7f7f7; border-radius: 12px; padding: 10px; border: 1px solid #e0e0e0; }
        QWidget#chat_display_content { background-color: #f7f7f7; }
        .user_message { background-color: #185ca1; color: white; border-radius: 12px; padding: 8px 12px; margin: 5px; }
        .ai_message { background-color: #f17039; color: white; border-radius: 12px; padding: 8px 12px; margin: 5px; }
        #input_frame { background-color: #ffffff; border-radius: 12px; border: 1px solid #cccccc; padding: 8px; }
        QLineEdit { border: none; font-size: 16px; padding: 6px; }
        #send_button { background-color: #185ca1; color: white; border-radius: 12px; padding: 8px 16px; font-weight: bold; }
        #send_button:hover { background-color: #f17039; }
        #back_home_button, #go_model_button { background-color: white; color: #185ca1; border: 2px solid #185ca1; border-radius: 8px; font-size: 18px; font-weight: bold; }
        #back_home_button:hover, #go_model_button:hover { color: #f17039; border-color: #f17039; }
        """
        self.setStyleSheet(qss)

    def init_rag_after_show(self):
        """初始化 RAG 系統"""
        print("正在載入 RAG 系統與模型...")
        config = DoclingRAGConfig(
            pdf_path="2025舞光LED21st(單頁水印可搜尋).pdf",
            enable_ocr=True,
            enable_query_expansion=False
        )
        self.rag_system = DoclingRAGSystem(config)
        self.rag_system.initialize()
        
        # 解鎖介面
        self.ui.input_text.setEnabled(True)
        self.ui.send_button.setEnabled(True)
        self.ui.input_text.setPlaceholderText("請輸入訊息...")
        self.ai_reply("您好！我是舞光 LED 客服 AI。已經為您載入最新 2025 型錄，請問想找什麼燈具嗎？")
        print("系統就緒")

    def send_message(self):
        msg = self.ui.input_text.text().strip()
        if msg:
            self.display_message(msg, is_user=True)
            self.ui.input_text.clear()
            self.ui.send_button.setEnabled(False)
            self.ui.input_text.setPlaceholderText("AI 正在檢索 388 頁型錄中...")

            # 啟動背景執行緒
            self.worker = RAGWorker(self.rag_system, msg)
            self.worker.answer_ready.connect(self.handle_ai_response)
            self.worker.start()

    def go_home(self):
        from homePage import MainWindow
        self.home_window = MainWindow()
        self.home_window.show()
        self.close()
    
    def handle_ai_response(self, result):
        self.ui.send_button.setEnabled(True)
        self.ui.input_text.setPlaceholderText("請輸入訊息...")
        answer = result.get("answer", "抱歉，目前連線不穩定。")
        self.ai_reply(answer)

    def display_message(self, text, is_user=True):
        h_layout = QtWidgets.QHBoxLayout()
        label = QtWidgets.QLabel(text)
        label.setWordWrap(True)
        label.setMaximumWidth(400)
        
        if is_user:
            h_layout.addStretch()
            label.setProperty("class", "user_message")
        else:
            label.setProperty("class", "ai_message")
            h_layout.addStretch()
            
        h_layout.addWidget(label)
        self.ui.chat_display_layout.addLayout(h_layout)
        
        # 強制滾動到底部
        QtCore.QTimer.singleShot(50, lambda: self.ui.chat_display.verticalScrollBar().setValue(
            self.ui.chat_display.verticalScrollBar().maximum()
        ))

    def ai_reply(self, text):
        h_layout = QtWidgets.QHBoxLayout()
        label = QtWidgets.QLabel("")
        label.setWordWrap(True)
        label.setMaximumWidth(400)
        label.setProperty("class", "ai_message")
        h_layout.addWidget(label)
        h_layout.addStretch()
        self.ui.chat_display_layout.addLayout(h_layout)

        # 打字機動畫
        self.typing_index = 0
        self.typing_text = text
        self.typing_label = label
        self.typing_timer = QtCore.QTimer()
        self.typing_timer.setInterval(25)
        self.typing_timer.timeout.connect(self.type_next_character)
        self.typing_timer.start()

    def type_next_character(self):
        if self.typing_index < len(self.typing_text):
            self.typing_label.setText(self.typing_label.text() + self.typing_text[self.typing_index])
            self.typing_index += 1
            self.ui.chat_display.verticalScrollBar().setValue(self.ui.chat_display.verticalScrollBar().maximum())
        else:
            self.typing_timer.stop()

if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    window = AIChatPage()
    window.show()
    sys.exit(app.exec_())