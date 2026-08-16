# 蓝牙心率广播接收器 - 记录页
import time
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QLabel
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor


class HeartRateRecord:
    """心率记录数据类"""
    def __init__(self, heart_rate, timestamp=None):
        self.heart_rate = heart_rate
        self.timestamp = timestamp or time.time()

    def time_str(self):
        return time.strftime("%H:%M:%S", time.localtime(self.timestamp))

    def date_str(self):
        return time.strftime("%Y-%m-%d", time.localtime(self.timestamp))


class RecordPage(QWidget):
    """记录页 - 心率数据表格"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.records = []
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        # 标题
        title_label = QLabel("心率记录")
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        # 记录数
        self.count_label = QLabel("共 0 条记录")
        self.count_label.setAlignment(Qt.AlignCenter)
        self.count_label.setStyleSheet("color: #AAAAAA; font-size: 12px;")
        layout.addWidget(self.count_label)

        # 表格
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["序号", "心率(BPM)", "时间"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)

        # 深色表头样式
        self.table.horizontalHeader().setStyleSheet("""
            QHeaderView::section {
                background-color: #2D2D2D;
                color: #FFFFFF;
                padding: 4px;
                border: 1px solid #3D3D3D;
                font-weight: bold;
            }
        """)
        self.table.setStyleSheet("""
            QTableWidget {
                alternate-background-color: #1E1E1E;
                background-color: #252525;
                color: #DDDDDD;
                gridline-color: #3D3D3D;
            }
            QTableWidget::item:selected {
                background-color: #4CAF50;
            }
        """)

        layout.addWidget(self.table)

        # 按钮区
        btn_layout = QHBoxLayout()

        self.chart_btn = QPushButton("显示折线图")
        self.chart_btn.setMinimumHeight(35)
        self.chart_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border-radius: 4px;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #1976D2; }
        """)
        btn_layout.addWidget(self.chart_btn)

        self.stats_btn = QPushButton("统计面板")
        self.stats_btn.setMinimumHeight(35)
        self.stats_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border-radius: 4px;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #F57C00; }
        """)
        btn_layout.addWidget(self.stats_btn)

        self.sleep_btn = QPushButton("睡眠分析")
        self.sleep_btn.setMinimumHeight(35)
        self.sleep_btn.setStyleSheet("""
            QPushButton {
                background-color: #9C27B0;
                color: white;
                border-radius: 4px;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #7B1FA2; }
        """)
        btn_layout.addWidget(self.sleep_btn)

        self.clear_btn = QPushButton("清空记录")
        self.clear_btn.setMinimumHeight(35)
        self.clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border-radius: 4px;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #D32F2F; }
        """)
        btn_layout.addWidget(self.clear_btn)

        layout.addLayout(btn_layout)

    def add_record(self, heart_rate):
        """添加一条心率记录"""
        record = HeartRateRecord(heart_rate)
        self.records.append(record)

        row = self.table.rowCount()
        self.table.insertRow(row)

        # 序号
        idx_item = QTableWidgetItem(str(row + 1))
        idx_item.setTextAlignment(Qt.AlignCenter)
        self.table.setItem(row, 0, idx_item)

        # 心率
        hr_item = QTableWidgetItem(str(heart_rate))
        hr_item.setTextAlignment(Qt.AlignCenter)
        # 根据心率值着色
        if heart_rate > 100:
            hr_item.setForeground(QColor("#FF4444"))
        elif heart_rate < 60:
            hr_item.setForeground(QColor("#4CAF50"))
        else:
            hr_item.setForeground(QColor("#FFFFFF"))
        self.table.setItem(row, 1, hr_item)

        # 时间
        time_item = QTableWidgetItem(record.time_str())
        time_item.setTextAlignment(Qt.AlignCenter)
        self.table.setItem(row, 2, time_item)

        # 自动滚动到底部
        self.table.scrollToBottom()

        # 更新记录数
        self.count_label.setText(f"共 {len(self.records)} 条记录")

    def clear_records(self):
        """清空所有记录"""
        self.records.clear()
        self.table.setRowCount(0)
        self.count_label.setText("共 0 条记录")

    def get_records(self):
        """获取所有记录"""
        return self.records

    def get_heart_rates(self):
        """获取所有心率值列表"""
        return [r.heart_rate for r in self.records]