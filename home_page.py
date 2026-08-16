# 蓝牙心率广播接收器 - 首页
import os
import time
import math
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QFormLayout, QSpinBox, QComboBox, QCheckBox,
    QFileDialog, QDialog, QLineEdit, QMessageBox, QTextEdit
)
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QSize, pyqtProperty, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QPainter, QPen
from config import HRV_WINDOW_SIZE, DEFAULT_CALORIE_SETTINGS, DEFAULT_HOME_DISPLAY_OPTIONS


class HeartAnimationLabel(QLabel):
    """心跳动画标签 - 跟随心率节拍缩放"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._scale = 1.0
        self.heart_text = "❤"
        self.setFont(QFont("Arial", 60))
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("color: #FF4444;")

        self.beat_animation = QPropertyAnimation(self, b"scale")
        self.beat_animation.setDuration(150)
        self.beat_animation.setKeyValueAt(0, 1.0)
        self.beat_animation.setKeyValueAt(0.3, 1.3)
        self.beat_animation.setKeyValueAt(1.0, 1.0)

        self.beat_timer = QTimer()
        self.beat_timer.timeout.connect(self._beat)

    @pyqtProperty(float)
    def scale(self):
        return self._scale

    @scale.setter
    def scale(self, value):
        self._scale = value
        self.update()

    def _beat(self):
        self.beat_animation.start()

    def set_heart_rate(self, hr):
        if hr > 0:
            interval = int(60000 / hr)
            self.beat_timer.start(interval)
        else:
            self.beat_timer.stop()

    def stop_beat(self):
        self.beat_timer.stop()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        font = self.font()
        font.setPointSize(int(60 * self._scale))
        painter.setFont(font)
        painter.setPen(QPen(QColor("#FF4444")))
        painter.drawText(self.rect(), Qt.AlignCenter, self.heart_text)
        painter.end()


class CalorieSettingsDialog(QDialog):
    """卡路里计算设置对话框"""
    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.setWindowTitle("卡路里设置")
        self.setMinimumWidth(300)
        self.settings = settings.copy()

        layout = QVBoxLayout(self)

        self.enabled_check = QCheckBox("启用卡路里计算")
        self.enabled_check.setChecked(settings.get('enabled', False))
        layout.addWidget(self.enabled_check)

        form = QFormLayout()

        self.weight_spin = QSpinBox()
        self.weight_spin.setRange(30, 200)
        self.weight_spin.setValue(int(settings.get('weight', 70)))
        self.weight_spin.setSuffix(" kg")
        form.addRow("体重:", self.weight_spin)

        self.age_spin = QSpinBox()
        self.age_spin.setRange(10, 100)
        self.age_spin.setValue(int(settings.get('age', 30)))
        self.age_spin.setSuffix(" 岁")
        form.addRow("年龄:", self.age_spin)

        self.gender_combo = QComboBox()
        self.gender_combo.addItems(["男", "女"])
        self.gender_combo.setCurrentIndex(0 if settings.get('gender', 'male') == 'male' else 1)
        form.addRow("性别:", self.gender_combo)

        layout.addLayout(form)

        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("确定")
        cancel_btn = QPushButton("取消")
        ok_btn.clicked.connect(self._save)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def _save(self):
        self.settings['enabled'] = self.enabled_check.isChecked()
        self.settings['weight'] = self.weight_spin.value()
        self.settings['age'] = self.age_spin.value()
        self.settings['gender'] = 'male' if self.gender_combo.currentIndex() == 0 else 'female'
        self.accept()

    def get_settings(self):
        return self.settings


class OBSSettingsDialog(QDialog):
    """OBS 对接设置对话框"""
    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.setWindowTitle("OBS 对接设置")
        self.setMinimumWidth(450)
        self.settings = settings.copy()

        layout = QVBoxLayout(self)

        self.enabled_check = QCheckBox("启用 OBS 对接")
        self.enabled_check.setChecked(settings.get('enabled', False))
        layout.addWidget(self.enabled_check)

        form = QFormLayout()

        self.output_type_combo = QComboBox()
        self.output_type_combo.addItems(["纯文本 (txt)", "网页 (html)"])
        self.output_type_combo.setCurrentIndex(0 if settings.get('output_type', 'txt') == 'txt' else 1)
        form.addRow("输出类型:", self.output_type_combo)

        self.file_path_edit = QLineEdit()
        self.file_path_edit.setText(settings.get('file_path', ''))
        self.file_path_edit.setPlaceholderText("选择输出文件路径...")
        path_layout = QHBoxLayout()
        path_layout.addWidget(self.file_path_edit)
        browse_btn = QPushButton("浏览")
        browse_btn.clicked.connect(self._browse_file)
        path_layout.addWidget(browse_btn)
        form.addRow("文件路径:", path_layout)

        self.icon_path_edit = QLineEdit()
        self.icon_path_edit.setText(settings.get('icon_path', ''))
        self.icon_path_edit.setPlaceholderText("可选：心率图标路径 (仅html模式)")
        icon_layout = QHBoxLayout()
        icon_layout.addWidget(self.icon_path_edit)
        icon_browse = QPushButton("浏览")
        icon_browse.clicked.connect(self._browse_icon)
        icon_layout.addWidget(icon_browse)
        form.addRow("图标路径:", icon_layout)

        layout.addLayout(form)

        info = QTextEdit()
        info.setReadOnly(True)
        info.setMaximumHeight(100)
        info.setPlainText(
            "使用说明：\n"
            "1. txt模式：输出纯数字心率值，适合OBS文本源\n"
            "2. html模式：输出带样式的HTML页面，含心跳动画，自动1秒刷新\n"
            "3. 在OBS中添加浏览器源或文本源，指向输出文件即可"
        )
        layout.addWidget(info)

        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("确定")
        cancel_btn = QPushButton("取消")
        ok_btn.clicked.connect(self._save)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def _browse_file(self):
        output_type = 'txt' if self.output_type_combo.currentIndex() == 0 else 'html'
        filter_str = "文本文件 (*.txt)" if output_type == 'txt' else "HTML文件 (*.html)"
        file_path, _ = QFileDialog.getSaveFileName(
            self, "选择输出文件", "", filter_str
        )
        if file_path:
            self.file_path_edit.setText(file_path)

    def _browse_icon(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择图标文件", "", "图片文件 (*.png *.jpg *.svg *.gif)"
        )
        if file_path:
            self.icon_path_edit.setText(file_path)

    def _save(self):
        self.settings['enabled'] = self.enabled_check.isChecked()
        self.settings['output_type'] = 'txt' if self.output_type_combo.currentIndex() == 0 else 'html'
        self.settings['file_path'] = self.file_path_edit.text()
        self.settings['icon_path'] = self.icon_path_edit.text()
        self.accept()

    def get_settings(self):
        return self.settings


class HomePage(QWidget):
    """首页 - 实时心率显示"""
    show_mini_heart = pyqtSignal()  # 弹窗心率信号

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_heart_rate = 0
        self.rr_intervals = []
        self.hrv_values = []
        self.hrv_enabled = False
        self.calorie_settings = DEFAULT_CALORIE_SETTINGS.copy()
        self.obs_settings = {
            'enabled': False,
            'output_type': 'txt',
            'file_path': '',
            'icon_path': ''
        }
        self.calorie_total = 0.0
        self.start_time = None
        self.is_running = False
        self.ble_worker = None
        self.current_theme = None  # 当前主题配置
        self.display_options = dict(DEFAULT_HOME_DISPLAY_OPTIONS)  # 首页显示选项
        self.target_address = None  # 指定连接的蓝牙设备地址

        self._init_ui()
        self._init_timers()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        # 时间显示
        self.time_label = QLabel(time.strftime("%H:%M:%S"))
        self.time_label.setFont(QFont("Arial", 16))
        self.time_label.setAlignment(Qt.AlignCenter)
        self.time_label.setStyleSheet("color: #AAAAAA;")
        layout.addWidget(self.time_label)

        # 心率区域（心跳动画 + 心率数值）- 用容器包裹以便整体显示/隐藏
        self.heart_rate_widget = QWidget()
        heart_rate_layout = QVBoxLayout(self.heart_rate_widget)
        heart_rate_layout.setContentsMargins(0, 0, 0, 0)
        heart_rate_layout.setSpacing(5)

        # 心跳动画
        heart_layout = QHBoxLayout()
        heart_layout.addStretch()

        self.heart_animation = HeartAnimationLabel()
        self.heart_animation.setFixedSize(120, 120)
        heart_layout.addWidget(self.heart_animation)

        heart_layout.addStretch()
        heart_rate_layout.addLayout(heart_layout)

        # 心率数值
        hr_layout = QHBoxLayout()
        hr_layout.addStretch()

        self.hr_label = QLabel("--")
        self.hr_label.setFont(QFont("Arial", 72, QFont.Bold))
        self.hr_label.setStyleSheet("color: #FF4444;")
        self.hr_label.setAlignment(Qt.AlignCenter)
        hr_layout.addWidget(self.hr_label)

        self.bpm_label = QLabel("BPM")
        self.bpm_label.setFont(QFont("Arial", 18))
        self.bpm_label.setStyleSheet("color: #FF8888;")
        self.bpm_label.setAlignment(Qt.AlignBottom | Qt.AlignLeft)
        hr_layout.addWidget(self.bpm_label)

        hr_layout.addStretch()
        heart_rate_layout.addLayout(hr_layout)

        layout.addWidget(self.heart_rate_widget)

        # 信息区域
        info_layout = QHBoxLayout()

        # 卡路里
        self.calorie_group = QGroupBox("卡路里")
        calorie_layout = QVBoxLayout()
        self.calorie_label = QLabel("0.0 kcal")
        self.calorie_label.setFont(QFont("Arial", 14))
        self.calorie_label.setAlignment(Qt.AlignCenter)
        calorie_layout.addWidget(self.calorie_label)
        self.calorie_group.setLayout(calorie_layout)
        info_layout.addWidget(self.calorie_group)

        # 运动时长
        self.duration_group = QGroupBox("运动时长")
        duration_layout = QVBoxLayout()
        self.duration_label = QLabel("00:00:00")
        self.duration_label.setFont(QFont("Arial", 14))
        self.duration_label.setAlignment(Qt.AlignCenter)
        duration_layout.addWidget(self.duration_label)
        self.duration_group.setLayout(duration_layout)
        info_layout.addWidget(self.duration_group)

        # HRV
        self.hrv_group = QGroupBox("HRV")
        hrv_layout = QVBoxLayout()
        self.hrv_label = QLabel("-- ms")
        self.hrv_label.setFont(QFont("Arial", 14))
        self.hrv_label.setAlignment(Qt.AlignCenter)
        hrv_layout.addWidget(self.hrv_label)
        self.hrv_status_label = QLabel("")
        self.hrv_status_label.setAlignment(Qt.AlignCenter)
        self.hrv_status_label.setStyleSheet("font-size: 11px; color: #AAAAAA;")
        hrv_layout.addWidget(self.hrv_status_label)
        self.hrv_group.setLayout(hrv_layout)
        info_layout.addWidget(self.hrv_group)

        layout.addLayout(info_layout)

        # OBS URL 显示区
        self.obs_url_label = QLabel("")
        self.obs_url_label.setAlignment(Qt.AlignCenter)
        self.obs_url_label.setStyleSheet("color: #888888; font-size: 11px;")
        layout.addWidget(self.obs_url_label)

        # 状态
        self.status_label = QLabel("未连接")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: #AAAAAA; font-size: 12px;")
        layout.addWidget(self.status_label)

        # 重连状态
        self.reconnect_label = QLabel("")
        self.reconnect_label.setAlignment(Qt.AlignCenter)
        self.reconnect_label.setStyleSheet("color: #FFAA00; font-size: 11px;")
        layout.addWidget(self.reconnect_label)

        # 按钮
        btn_layout = QHBoxLayout()
        self.start_btn = QPushButton("开始监测")
        self.start_btn.setMinimumHeight(40)
        self.start_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #45a049; }
            QPushButton:disabled { background-color: #888888; }
        """)
        self.start_btn.clicked.connect(self.toggle_monitoring)
        btn_layout.addWidget(self.start_btn)

        # 弹窗心率按钮
        self.mini_heart_btn = QPushButton("弹窗心率")
        self.mini_heart_btn.setMinimumHeight(40)
        self.mini_heart_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #1976D2; }
        """)
        self.mini_heart_btn.clicked.connect(self.show_mini_heart.emit)
        btn_layout.addWidget(self.mini_heart_btn)

        layout.addLayout(btn_layout)

    def _init_timers(self):
        self.time_timer = QTimer()
        self.time_timer.timeout.connect(self._update_time)
        self.time_timer.start(1000)

        self.duration_timer = QTimer()
        self.duration_timer.timeout.connect(self._update_duration)

    def _update_time(self):
        self.time_label.setText(time.strftime("%H:%M:%S"))

    def _update_duration(self):
        if self.start_time:
            elapsed = int(time.time() - self.start_time)
            hours = elapsed // 3600
            minutes = (elapsed % 3600) // 60
            seconds = elapsed % 60
            self.duration_label.setText(f"{hours:02d}:{minutes:02d}:{seconds:02d}")

    def toggle_monitoring(self):
        if self.is_running:
            self.stop_monitoring()
        else:
            self.start_monitoring(target_address=self.target_address)

    def start_monitoring(self, target_address=None):
        self.is_running = True
        self.start_btn.setText("停止监测")
        stop_color = self.current_theme['stop_btn'] if self.current_theme else '#f44336'
        stop_hover = self.current_theme['stop_btn_hover'] if self.current_theme else '#da190b'
        self.start_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {stop_color};
                color: white;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background-color: {stop_hover}; }}
        """)

        self.start_time = time.time()
        self.calorie_total = 0.0
        self.duration_timer.start(1000)

        from ble_worker import BleakWorker
        self.ble_worker = BleakWorker(target_address=target_address)
        self.ble_worker.heart_rate_received.connect(self.on_heart_rate)
        self.ble_worker.rr_interval_received.connect(self.on_rr_interval)
        self.ble_worker.status_changed.connect(self.on_status_changed)
        self.ble_worker.error_occurred.connect(self.on_error)
        self.ble_worker.connection_lost.connect(self.on_connection_lost)
        self.ble_worker.start()

    def stop_monitoring(self):
        self.is_running = False
        self.start_btn.setText("开始监测")
        start_color = self.current_theme['start_btn'] if self.current_theme else '#4CAF50'
        start_hover = self.current_theme['start_btn_hover'] if self.current_theme else '#45a049'
        self.start_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {start_color};
                color: white;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background-color: {start_hover}; }}
            QPushButton:disabled {{ background-color: #888888; }}
        """)

        self.duration_timer.stop()
        self.heart_animation.stop_beat()

        if self.ble_worker:
            self.ble_worker.stop()
            self.ble_worker = None

        self.status_label.setText("已停止")
        self.reconnect_label.setText("")

    def on_heart_rate(self, hr):
        self.current_heart_rate = hr
        self.hr_label.setText(str(hr))
        self.heart_animation.set_heart_rate(hr)

        # 计算卡路里
        self._update_calorie(hr)

        # 如果没有真实RR间期，用心率推算
        if self.hrv_enabled and not self.rr_intervals:
            estimated_rr = 60000.0 / hr if hr > 0 else 0
            if estimated_rr > 0:
                self._calculate_hrv([estimated_rr])

        # 写入OBS文件
        self._write_obs(hr)

        # 发射信号给主窗口记录数据
        parent = self.parent()
        while parent:
            if hasattr(parent, 'on_heart_rate_data'):
                parent.on_heart_rate_data(hr)
                break
            parent = parent.parent()

    def on_rr_interval(self, intervals):
        self.rr_intervals = intervals
        if self.hrv_enabled:
            self._calculate_hrv(intervals)

    def _calculate_hrv(self, new_intervals):
        for rr in new_intervals:
            self.hrv_values.append(rr)
        # 保持窗口大小
        while len(self.hrv_values) > HRV_WINDOW_SIZE:
            self.hrv_values.pop(0)

        if len(self.hrv_values) < 2:
            return

        # 计算 RMSSD
        sum_sq = 0
        for i in range(1, len(self.hrv_values)):
            diff = self.hrv_values[i] - self.hrv_values[i-1]
            sum_sq += diff * diff
        rmssd = math.sqrt(sum_sq / (len(self.hrv_values) - 1))

        self.hrv_label.setText(f"{rmssd:.1f} ms")

        # HRV 状态评估
        if rmssd >= 100:
            status = "优秀"
            color = "#4CAF50"
        elif rmssd >= 50:
            status = "良好"
            color = "#8BC34A"
        elif rmssd >= 20:
            status = "一般"
            color = "#FF9800"
        else:
            status = "较低"
            color = "#f44336"
        self.hrv_status_label.setText(status)
        self.hrv_status_label.setStyleSheet(f"font-size: 11px; color: {color};")

    def _update_calorie(self, hr):
        if not self.calorie_settings.get('enabled', False):
            return

        weight = self.calorie_settings.get('weight', 70)
        age = self.calorie_settings.get('age', 30)
        gender = self.calorie_settings.get('gender', 'male')

        if gender == 'male':
            cal_per_min = (-55.0969 + (0.6309 * hr) + (0.1988 * weight) + (0.2017 * age)) / 4.184
        else:
            cal_per_min = (-20.4022 + (0.4472 * hr) - (0.1263 * weight) + (0.074 * age)) / 4.184

        # 每秒累积
        cal_per_sec = cal_per_min / 60.0
        self.calorie_total += cal_per_sec
        self.calorie_label.setText(f"{self.calorie_total:.1f} kcal")

    def _write_obs(self, hr):
        if not self.obs_settings.get('enabled', False):
            return

        file_path = self.obs_settings.get('file_path', '')
        if not file_path:
            return

        output_type = self.obs_settings.get('output_type', 'txt')

        try:
            if output_type == 'txt':
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(str(hr))
            else:
                icon_html = ""
                icon_path = self.obs_settings.get('icon_path', '')
                if icon_path and os.path.exists(icon_path):
                    icon_html = f'<img src="{icon_path}" style="width:24px;height:24px;vertical-align:middle;margin-right:5px;">'

                html_content = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta http-equiv="refresh" content="1">
<style>
.heart-rate {{
    font-size: 48px;
    font-weight: bold;
    color: #FF4444;
    text-align: center;
    font-family: Arial, sans-serif;
}}
.heart-icon {{
    display: inline-block;
    animation: heartbeat 1s infinite;
}}
@keyframes heartbeat {{
    0% {{ transform: scale(1); }}
    15% {{ transform: scale(1.3); }}
    30% {{ transform: scale(1); }}
}}
</style>
</head>
<body>
<div class="heart-rate">
    <span class="heart-icon">❤</span> {icon_html}{hr} <span style="font-size:20px;color:#FF8888;">BPM</span>
</div>
</body>
</html>"""
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(html_content)
        except Exception as e:
            pass

    def on_status_changed(self, status):
        self.status_label.setText(status)

    def on_error(self, error):
        self.status_label.setText(f"错误: {error}")
        self.status_label.setStyleSheet("color: #f44336; font-size: 12px;")

    def on_connection_lost(self):
        self.stop_monitoring()
        self.hr_label.setText("--")
        self.heart_animation.stop_beat()

    def set_hrv_enabled(self, enabled):
        self.hrv_enabled = enabled
        if not enabled:
            self.hrv_label.setText("-- ms")
            self.hrv_status_label.setText("")
            self.hrv_values.clear()

    def set_calorie_settings(self, settings):
        self.calorie_settings = settings.copy()

    def set_obs_settings(self, settings):
        self.obs_settings = settings.copy()
        if settings.get('enabled', False) and settings.get('file_path', ''):
            self.obs_url_label.setText(f"OBS: {settings['file_path']}")
        else:
            self.obs_url_label.setText("")

    def update_obs_url_display(self):
        if self.obs_settings.get('enabled', False) and self.obs_settings.get('file_path', ''):
            self.obs_url_label.setText(f"OBS: {self.obs_settings['file_path']}")
        else:
            self.obs_url_label.setText("")

    def set_display_option(self, key, visible):
        """设置首页显示选项"""
        self.display_options[key] = visible
        self._apply_display_options()

    def _apply_display_options(self):
        """根据显示选项控制首页元素可见性"""
        # 心率区域
        if 'heart_rate' in self.display_options:
            self.heart_rate_widget.setVisible(self.display_options['heart_rate'])
        # 卡路里
        if 'calorie' in self.display_options:
            self.calorie_group.setVisible(self.display_options['calorie'])
        # 运动时长
        if 'duration' in self.display_options:
            self.duration_group.setVisible(self.display_options['duration'])
        # HRV
        if 'hrv' in self.display_options:
            self.hrv_group.setVisible(self.display_options['hrv'])

    def set_theme(self, theme):
        """设置当前主题配置"""
        self.current_theme = theme

    def cleanup(self):
        """清理资源"""
        if self.ble_worker:
            self.ble_worker.stop()
            self.ble_worker = None
        self.time_timer.stop()
        self.duration_timer.stop()
        self.heart_animation.stop_beat()