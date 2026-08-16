# 蓝牙心率广播接收器 - 统计面板
import time
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QGroupBox, QFormLayout, QSpinBox, QPushButton
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont


class StatsWindow(QWidget):
    """统计面板 - 心率统计信息"""
    def __init__(self, records_getter=None, parent=None):
        super().__init__(parent)
        self.records_getter = records_getter  # 获取记录的回调函数
        self.weight = 70  # 默认体重
        self._load_weight()
        self._init_ui()
        self._init_timer()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        # 标题
        title = QLabel("心率统计")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # 基本统计
        stats_group = QGroupBox("基本统计")
        stats_layout = QFormLayout()

        self.max_label = QLabel("--")
        self.max_label.setFont(QFont("Arial", 14, QFont.Bold))
        self.max_label.setStyleSheet("color: #FF4444;")
        stats_layout.addRow("最大心率:", self.max_label)

        self.min_label = QLabel("--")
        self.min_label.setFont(QFont("Arial", 14, QFont.Bold))
        self.min_label.setStyleSheet("color: #4CAF50;")
        stats_layout.addRow("最小心率:", self.min_label)

        self.avg_label = QLabel("--")
        self.avg_label.setFont(QFont("Arial", 14, QFont.Bold))
        self.avg_label.setStyleSheet("color: #2196F3;")
        stats_layout.addRow("平均心率:", self.avg_label)

        self.count_label = QLabel("0")
        self.count_label.setFont(QFont("Arial", 14))
        stats_layout.addRow("记录数:", self.count_label)

        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)

        # 心率范围
        range_group = QGroupBox("心率范围")
        range_layout = QVBoxLayout()

        self.range_label = QLabel("--")
        self.range_label.setFont(QFont("Arial", 14))
        self.range_label.setAlignment(Qt.AlignCenter)
        range_layout.addWidget(self.range_label)

        self.range_desc = QLabel("")
        self.range_desc.setAlignment(Qt.AlignCenter)
        self.range_desc.setStyleSheet("color: #AAAAAA; font-size: 11px;")
        range_layout.addWidget(self.range_desc)

        range_group.setLayout(range_layout)
        layout.addWidget(range_group)

        # 卡路里消耗
        calorie_group = QGroupBox("卡路里消耗")
        calorie_layout = QFormLayout()

        weight_layout = QHBoxLayout()
        self.weight_spin = QSpinBox()
        self.weight_spin.setRange(30, 200)
        self.weight_spin.setValue(self.weight)
        self.weight_spin.setSuffix(" kg")
        self.weight_spin.valueChanged.connect(self._on_weight_changed)
        weight_layout.addWidget(self.weight_spin)
        calorie_layout.addRow("体重:", weight_layout)

        self.calorie_label = QLabel("0.0 kcal")
        self.calorie_label.setFont(QFont("Arial", 14, QFont.Bold))
        self.calorie_label.setStyleSheet("color: #FF9800;")
        calorie_layout.addRow("总消耗:", self.calorie_label)

        self.duration_label = QLabel("00:00:00")
        self.calorie_label.setFont(QFont("Arial", 14))
        calorie_layout.addRow("运动时长:", self.duration_label)

        calorie_group.setLayout(calorie_layout)
        layout.addWidget(calorie_group)

        layout.addStretch()

    def _init_timer(self):
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self._refresh_stats)
        self.refresh_timer.start(500)

    def _refresh_stats(self):
        if not self.records_getter:
            return

        records = self.records_getter()
        if not records:
            return

        heart_rates = [r.heart_rate for r in records]

        # 基本统计
        max_hr = max(heart_rates)
        min_hr = min(heart_rates)
        avg_hr = sum(heart_rates) / len(heart_rates)

        self.max_label.setText(f"{max_hr} BPM")
        self.min_label.setText(f"{min_hr} BPM")
        self.avg_label.setText(f"{avg_hr:.1f} BPM")
        self.count_label.setText(str(len(heart_rates)))

        # 心率范围
        hr_range = max_hr - min_hr
        self.range_label.setText(f"{hr_range} BPM")

        if hr_range < 20:
            desc = "心率非常稳定"
            color = "#4CAF50"
        elif hr_range < 40:
            desc = "心率波动正常"
            color = "#8BC34A"
        elif hr_range < 60:
            desc = "心率波动较大"
            color = "#FF9800"
        else:
            desc = "心率波动剧烈"
            color = "#f44336"
        self.range_desc.setText(desc)
        self.range_desc.setStyleSheet(f"color: {color}; font-size: 11px;")

        # 卡路里计算
        if len(records) >= 2:
            time_diff = records[-1].timestamp - records[0].timestamp
            time_diff_minutes = time_diff / 60.0
            hours = int(time_diff) // 3600
            minutes = (int(time_diff) % 3600) // 60
            seconds = int(time_diff) % 60
            self.duration_label.setText(f"{hours:02d}:{minutes:02d}:{seconds:02d}")

            # 卡路里: 0.014 * weight * avg_hr * time_diff_minutes
            calorie = 0.014 * self.weight * avg_hr * time_diff_minutes
            self.calorie_label.setText(f"{calorie:.1f} kcal")

    def _on_weight_changed(self, value):
        self.weight = value
        self._save_weight()

    def _load_weight(self):
        """从设置文件加载体重"""
        try:
            import json
            import os
            settings_path = os.path.join(os.path.expanduser("~"), "HeartRateData", "settings.json")
            if os.path.exists(settings_path):
                with open(settings_path, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    self.weight = settings.get('stats_weight', 70)
        except Exception:
            self.weight = 70

    def _save_weight(self):
        """保存体重到设置文件"""
        try:
            import json
            import os
            data_dir = os.path.join(os.path.expanduser("~"), "HeartRateData")
            os.makedirs(data_dir, exist_ok=True)
            settings_path = os.path.join(data_dir, "settings.json")

            settings = {}
            if os.path.exists(settings_path):
                with open(settings_path, 'r', encoding='utf-8') as f:
                    settings = json.load(f)

            settings['stats_weight'] = self.weight

            with open(settings_path, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def set_records_getter(self, getter):
        self.records_getter = getter

    def cleanup(self):
        self.refresh_timer.stop()