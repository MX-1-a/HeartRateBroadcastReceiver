# 蓝牙心率广播接收器 - 主窗口
import os
import sys
import json
import time
import subprocess
import webbrowser
from datetime import datetime
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QStackedWidget, QMenuBar, QAction,
    QFileDialog, QMessageBox, QProgressDialog, QDialog,
    QLineEdit, QFormLayout, QLabel, QSystemTrayIcon, QMenu,
    QApplication
)
from PyQt5.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QIcon, QPixmap, QPainter, QColor
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest
from PyQt5.QtCore import QUrl

from config import APP_VERSION, GITHUB_RELEASES_API, DEFAULT_CALORIE_SETTINGS, DEFAULT_THEME, DEFAULT_CLOSE_TO_TRAY, DEFAULT_MINI_HEART_OPTIONS, DEFAULT_HOME_DISPLAY_OPTIONS
from themes import apply_theme, get_theme, THEME_DARK_HEART, THEME_AURORA_BLUE, THEME_WARM_SUN, THEME_NAMES
from mini_heart_widget import MiniHeartRateWidget, DEFAULT_DISPLAY_OPTIONS
from home_page import HomePage, CalorieSettingsDialog, OBSSettingsDialog
from record_page import RecordPage, HeartRateRecord
from stats_window import StatsWindow
from chart_window import ChartWindow
from sleep_window import SleepAnalysisWindow
from ble_scanner_dialog import BluetoothScanDialog


class UpdateChecker(QThread):
    """后台检查更新线程"""
    update_available = pyqtSignal(str, str)  # version, download_url
    no_update = pyqtSignal()
    error_occurred = pyqtSignal(str)

    def run(self):
        try:
            import urllib.request
            import json as json_mod
            req = urllib.request.Request(
                GITHUB_RELEASES_API,
                headers={'User-Agent': 'HeartRateMonitor'}
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json_mod.loads(response.read().decode('utf-8'))
                latest_version = data.get('tag_name', '')
                download_url = ''
                for asset in data.get('assets', []):
                    if asset.get('name', '').endswith('.exe'):
                        download_url = asset.get('browser_download_url', '')
                        break
                if latest_version and version_compare(latest_version, APP_VERSION) > 0:
                    self.update_available.emit(latest_version, download_url)
                else:
                    self.no_update.emit()
        except Exception as e:
            self.error_occurred.emit(str(e))


def version_compare(v1, v2):
    """版本号比较，返回1/0/-1"""
    def normalize(v):
        return [int(x) for x in v.replace('v', '').split('.')]
    n1 = normalize(v1)
    n2 = normalize(v2)
    for a, b in zip(n1, n2):
        if a > b:
            return 1
        if a < b:
            return -1
    if len(n1) > len(n2):
        return 1
    elif len(n1) < len(n2):
        return -1
    return 0


class DataLocationDialog(QDialog):
    """数据存储位置设置对话框"""
    def __init__(self, current_path, parent=None):
        super().__init__(parent)
        self.setWindowTitle("数据存储位置")
        self.setMinimumWidth(450)
        self.data_path = current_path

        layout = QVBoxLayout(self)

        info = QLabel("选择心率数据的存储目录：")
        layout.addWidget(info)

        path_layout = QHBoxLayout()
        self.path_edit = QLineEdit()
        self.path_edit.setText(current_path)
        self.path_edit.setReadOnly(True)
        path_layout.addWidget(self.path_edit)

        browse_btn = QPushButton("浏览")
        browse_btn.clicked.connect(self._browse)
        path_layout.addWidget(browse_btn)
        layout.addLayout(path_layout)

        btn_layout = QHBoxLayout()
        ok_btn = QPushButton("确定")
        cancel_btn = QPushButton("取消")
        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(ok_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)

    def _browse(self):
        path = QFileDialog.getExistingDirectory(self, "选择数据存储目录")
        if path:
            self.path_edit.setText(path)
            self.data_path = path

    def get_path(self):
        return self.path_edit.text()


class HeartRateWindow(QMainWindow):
    """主窗口 - 心率广播接收器"""
    theme_changed = pyqtSignal(str)  # 主题切换信号

    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"心率广播接收器 {APP_VERSION}")
        self.setMinimumSize(900, 700)

        # 数据存储
        self.data_dir = os.path.join(os.path.expanduser("~"), "HeartRateData")
        self._load_data_dir()

        # 设置
        self.calorie_settings = DEFAULT_CALORIE_SETTINGS.copy()
        self.obs_settings = {
            'enabled': False,
            'output_type': 'txt',
            'file_path': '',
            'icon_path': ''
        }
        self.hrv_enabled = False
        self.current_theme = DEFAULT_THEME
        self.close_to_tray = DEFAULT_CLOSE_TO_TRAY
        self.mini_heart_options = dict(DEFAULT_MINI_HEART_OPTIONS)
        self.home_display_options = dict(DEFAULT_HOME_DISPLAY_OPTIONS)
        self.connected_device_address = None  # 已连接的蓝牙设备地址
        self.connected_device_name = None     # 已连接的蓝牙设备名称
        self._load_settings()

        # 当日记录
        self.current_date = datetime.now().strftime("%Y-%m-%d")
        self.daily_records = []
        self._load_daily_records()

        self._init_ui()
        self._init_menu()
        self._init_timer()
        self._init_tray()
        self._init_mini_heart()

        # 应用加载的设置到UI
        self._apply_loaded_settings()

        # 启动时检查更新
        self._check_update_at_startup()

    def _init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # 导航栏
        nav_layout = QHBoxLayout()

        self.home_btn = QPushButton("首页")
        self.home_btn.setMinimumHeight(40)
        self.home_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #45a049; }
        """)
        self.home_btn.clicked.connect(lambda: self._switch_page(0))
        nav_layout.addWidget(self.home_btn)

        self.record_btn = QPushButton("记录")
        self.record_btn.setMinimumHeight(40)
        self.record_btn.setStyleSheet("""
            QPushButton {
                background-color: #555555;
                color: white;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #666666; }
        """)
        self.record_btn.clicked.connect(lambda: self._switch_page(1))
        nav_layout.addWidget(self.record_btn)

        layout.addLayout(nav_layout)

        # 页面堆栈
        self.stack = QStackedWidget()

        # 首页
        self.home_page = HomePage()
        self.stack.addWidget(self.home_page)

        # 记录页
        self.record_page = RecordPage()
        self.stack.addWidget(self.record_page)

        layout.addWidget(self.stack)

        # 连接首页按钮信号
        self.home_page.set_calorie_settings(self.calorie_settings)
        self.home_page.set_obs_settings(self.obs_settings)

        # 连接记录页按钮信号
        self.record_page.chart_btn.clicked.connect(self._show_chart)
        self.record_page.stats_btn.clicked.connect(self._show_stats)
        self.record_page.sleep_btn.clicked.connect(self._show_sleep)
        self.record_page.clear_btn.clicked.connect(self._clear_records)

    def _init_menu(self):
        menubar = self.menuBar()

        # 设置菜单
        settings_menu = menubar.addMenu("设置")

        calorie_action = QAction("卡路里设置", self)
        calorie_action.triggered.connect(self._show_calorie_settings)
        settings_menu.addAction(calorie_action)

        hrv_action = QAction("HRV 开关", self)
        hrv_action.setCheckable(True)
        hrv_action.setChecked(self.hrv_enabled)
        hrv_action.triggered.connect(self._toggle_hrv)
        settings_menu.addAction(hrv_action)

        obs_action = QAction("OBS 对接", self)
        obs_action.triggered.connect(self._show_obs_settings)
        settings_menu.addAction(obs_action)

        data_location_action = QAction("数据存储位置", self)
        data_location_action.triggered.connect(self._show_data_location)
        settings_menu.addAction(data_location_action)

        settings_menu.addSeparator()

        update_action = QAction("检查更新", self)
        update_action.triggered.connect(self._check_update)
        settings_menu.addAction(update_action)

        # 数据菜单
        data_menu = menubar.addMenu("数据")

        csv_action = QAction("导出 CSV", self)
        csv_action.triggered.connect(self._export_csv)
        data_menu.addAction(csv_action)

        excel_action = QAction("导出 Excel", self)
        excel_action.triggered.connect(self._export_excel)
        data_menu.addAction(excel_action)

        # 主题菜单
        theme_menu = menubar.addMenu("主题")

        self.theme_actions = {}
        for theme_id, theme_name in THEME_NAMES.items():
            action = QAction(theme_name, self)
            action.setCheckable(True)
            action.setChecked(theme_id == self.current_theme)
            action.triggered.connect(lambda checked, tid=theme_id: self._switch_theme(tid))
            theme_menu.addAction(action)
            self.theme_actions[theme_id] = action

        # 关闭行为菜单
        settings_menu.addSeparator()
        self.close_to_tray_action = QAction("关闭时最小化到托盘", self)
        self.close_to_tray_action.setCheckable(True)
        self.close_to_tray_action.setChecked(self.close_to_tray)
        self.close_to_tray_action.triggered.connect(self._toggle_close_to_tray)
        settings_menu.addAction(self.close_to_tray_action)

        # 弹窗心率显示选项二级菜单
        mini_heart_menu = settings_menu.addMenu("弹窗心率")
        self.mini_heart_actions = {}
        mini_heart_labels = {
            'title': '显示标题',
            'heart': '显示心跳动画',
            'hr_number': '显示心率数字',
            'bpm': '显示BPM标签',
        }
        for key, label in mini_heart_labels.items():
            action = QAction(label, self)
            action.setCheckable(True)
            action.setChecked(self.mini_heart_options.get(key, True))
            action.triggered.connect(lambda checked, k=key: self._toggle_mini_heart_option(k, checked))
            mini_heart_menu.addAction(action)
            self.mini_heart_actions[key] = action

        # 首页显示选项二级菜单
        home_display_menu = settings_menu.addMenu("首页显示")
        self.home_display_actions = {}
        home_display_labels = {
            'heart_rate': '心率区域',
            'calorie': '卡路里',
            'duration': '运动时长',
            'hrv': 'HRV',
        }
        for key, label in home_display_labels.items():
            action = QAction(label, self)
            action.setCheckable(True)
            action.setChecked(self.home_display_options.get(key, True))
            action.triggered.connect(lambda checked, k=key: self._toggle_home_display_option(k, checked))
            home_display_menu.addAction(action)
            self.home_display_actions[key] = action

        # 连接菜单
        connect_menu = menubar.addMenu("连接")

        self.scan_action = QAction("扫描设备", self)
        self.scan_action.triggered.connect(self._scan_ble_devices)
        connect_menu.addAction(self.scan_action)

        self.disconnect_action = QAction("断开连接", self)
        self.disconnect_action.setEnabled(False)
        self.disconnect_action.triggered.connect(self._disconnect_device)
        connect_menu.addAction(self.disconnect_action)

        connect_menu.addSeparator()

        self.device_info_action = QAction("当前设备: 未连接", self)
        self.device_info_action.setEnabled(False)
        connect_menu.addAction(self.device_info_action)

    def _init_timer(self):
        # 每日重置定时器
        self.date_check_timer = QTimer()
        self.date_check_timer.timeout.connect(self._check_date_change)
        self.date_check_timer.start(60000)  # 每分钟检查

        # 自动保存定时器
        self.save_timer = QTimer()
        self.save_timer.timeout.connect(self._save_daily_records)
        self.save_timer.start(30000)  # 每30秒保存

    def _init_tray(self):
        """初始化系统托盘"""
        # 创建托盘图标（红色心形）
        pixmap = QPixmap(32, 32)
        pixmap.fill(QColor(0, 0, 0, 0))
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(231, 76, 60))  # 红色
        # 绘制简单心形
        painter.setFont(QFont("Arial", 22))
        painter.drawText(pixmap.rect(), Qt.AlignCenter, "❤")
        painter.end()
        tray_icon = QIcon(pixmap)

        self.tray = QSystemTrayIcon(tray_icon, self)
        self.tray.setToolTip(f"心率广播接收器 {APP_VERSION}")

        # 托盘菜单
        tray_menu = QMenu()
        show_action = tray_menu.addAction("显示主窗口")
        show_action.triggered.connect(self._show_window)
        tray_menu.addSeparator()
        quit_action = tray_menu.addAction("退出")
        quit_action.triggered.connect(self._quit_app)

        self.tray.setContextMenu(tray_menu)
        self.tray.activated.connect(self._tray_activated)
        self.tray.show()

    def _init_mini_heart(self):
        """初始化弹窗心率Widget"""
        self.mini_heart = MiniHeartRateWidget(display_options=self.mini_heart_options)
        # 连接首页弹窗心率信号
        self.home_page.show_mini_heart.connect(self._toggle_mini_heart)

    def _tray_activated(self, reason):
        """托盘图标激活"""
        if reason == QSystemTrayIcon.DoubleClick:
            self._show_window()

    def _show_window(self):
        """显示主窗口"""
        self.showNormal()
        self.activateWindow()
        self.raise_()

    def _quit_app(self):
        """真正退出应用"""
        self._save_daily_records()
        self.home_page.cleanup()
        self.mini_heart.stop()
        self.mini_heart.close()
        self.tray.hide()
        QApplication.instance().quit()

    def _toggle_mini_heart(self):
        """切换弹窗心率窗口"""
        if self.mini_heart.isVisible():
            self.mini_heart.hide()
        else:
            # 应用当前主题
            theme = get_theme(self.current_theme)
            self.mini_heart.apply_theme(theme)
            self.mini_heart.show()
            # 如果正在监测，同步当前心率
            if self.home_page.current_heart_rate > 0:
                self.mini_heart.update_heart_rate(self.home_page.current_heart_rate)

    def _switch_theme(self, theme_id):
        """切换主题"""
        if theme_id == self.current_theme:
            return
        self.current_theme = theme_id
        # 更新菜单选中状态
        for tid, action in self.theme_actions.items():
            action.setChecked(tid == theme_id)
        # 应用主题
        theme = apply_theme(QApplication.instance(), theme_id)
        # 更新导航按钮样式
        self._update_nav_style()
        # 更新首页控件颜色
        self._apply_home_page_colors(theme)
        # 更新弹窗心率主题
        if self.mini_heart.isVisible():
            self.mini_heart.apply_theme(theme)
        # 保存设置
        self._save_settings()
        self.theme_changed.emit(theme_id)

    def _toggle_close_to_tray(self, checked):
        """切换关闭行为"""
        self.close_to_tray = checked
        self._save_settings()

    def _toggle_mini_heart_option(self, key, checked):
        """切换弹窗心率显示选项"""
        self.mini_heart_options[key] = checked
        self.mini_heart.set_display_option(key, checked)
        self._save_settings()

    def _toggle_home_display_option(self, key, checked):
        """切换首页显示选项"""
        self.home_display_options[key] = checked
        self.home_page.set_display_option(key, checked)
        self._save_settings()

    def _scan_ble_devices(self):
        """扫描蓝牙设备"""
        dialog = BluetoothScanDialog(self)
        dialog.device_selected.connect(self._on_device_selected)
        dialog.exec_()

    def _on_device_selected(self, address, name):
        """用户选择了蓝牙设备"""
        self.connected_device_address = address
        self.connected_device_name = name
        self.home_page.target_address = address
        self.device_info_action.setText(f"当前设备: {name}")
        self.disconnect_action.setEnabled(True)
        self._save_settings()
        
        # 如果当前未在监测，自动开始监测
        if not self.home_page.is_running:
            self.home_page.start_monitoring(target_address=address)
        else:
            # 如果正在监测，先停止再用新地址重新连接
            self.home_page.stop_monitoring()
            self.home_page.start_monitoring(target_address=address)

    def _disconnect_device(self):
        """断开蓝牙设备连接"""
        if self.home_page.is_running:
            self.home_page.stop_monitoring()
        self.connected_device_address = None
        self.connected_device_name = None
        self.home_page.target_address = None
        self.device_info_action.setText("当前设备: 未连接")
        self.disconnect_action.setEnabled(False)
        self._save_settings()

    def _update_nav_style(self):
        """更新导航按钮样式（跟随主题）"""
        theme = get_theme(self.current_theme)
        current_page = self.stack.currentIndex()

        if current_page == 0:
            self.home_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {theme['nav_active_home']};
                    color: white;
                    border-radius: 6px;
                    font-size: 14px;
                    font-weight: bold;
                }}
                QPushButton:hover {{ background-color: {theme['nav_active_home']}dd; }}
            """)
            self.record_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {theme['nav_inactive']};
                    color: white;
                    border-radius: 6px;
                    font-size: 14px;
                    font-weight: bold;
                }}
                QPushButton:hover {{ background-color: {theme['nav_inactive']}cc; }}
            """)
        else:
            self.record_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {theme['nav_active_record']};
                    color: white;
                    border-radius: 6px;
                    font-size: 14px;
                    font-weight: bold;
                }}
                QPushButton:hover {{ background-color: {theme['nav_active_record']}dd; }}
            """)
            self.home_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {theme['nav_inactive']};
                    color: white;
                    border-radius: 6px;
                    font-size: 14px;
                    font-weight: bold;
                }}
                QPushButton:hover {{ background-color: {theme['nav_inactive']}cc; }}
            """)

    def _apply_home_page_colors(self, theme):
        """应用首页控件颜色"""
        self.home_page.set_theme(theme)
        self.home_page.hr_label.setStyleSheet(f"color: {theme['heart_color']};")
        self.home_page.bpm_label.setStyleSheet(f"color: {theme['bpm_color']};")
        self.home_page.heart_animation.setStyleSheet(f"color: {theme['heart_color']};")
        # 更新按钮样式
        if self.home_page.is_running:
            self.home_page.start_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {theme['stop_btn']};
                    color: white;
                    border-radius: 6px;
                    font-size: 14px;
                    font-weight: bold;
                }}
                QPushButton:hover {{ background-color: {theme['stop_btn_hover']}; }}
            """)
        else:
            self.home_page.start_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {theme['start_btn']};
                    color: white;
                    border-radius: 6px;
                    font-size: 14px;
                    font-weight: bold;
                }}
                QPushButton:hover {{ background-color: {theme['start_btn_hover']}; }}
                QPushButton:disabled {{ background-color: #888888; }}
            """)
        # 弹窗心率按钮
        self.home_page.mini_heart_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {theme['accent']};
                color: white;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background-color: {theme['accent']}cc; }}
        """)

    def _switch_page(self, index):
        self.stack.setCurrentIndex(index)
        self._update_nav_style()

    def on_heart_rate_data(self, hr):
        """收到心率数据 - 由首页调用"""
        record = HeartRateRecord(hr)
        self.daily_records.append(record)
        self.record_page.add_record(hr)
        # 同步更新弹窗心率
        if self.mini_heart.isVisible():
            self.mini_heart.update_heart_rate(hr)

    def _show_chart(self):
        chart = ChartWindow(
            records_getter=lambda: self.daily_records,
            data_dir=self.data_dir
        )
        chart.exec_() if hasattr(chart, 'exec_') else chart.show()
        chart.update_line_chart()
        chart.show()

    def _show_stats(self):
        stats = StatsWindow(records_getter=lambda: self.daily_records)
        stats.setWindowTitle("心率统计")
        stats.show()

    def _show_sleep(self):
        sleep = SleepAnalysisWindow(records_getter=lambda: self.daily_records)
        sleep.show()

    def _clear_records(self):
        reply = QMessageBox.question(
            self, "确认", "确定要清空所有记录吗？",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.daily_records.clear()
            self.record_page.clear_records()

    def _show_calorie_settings(self):
        dialog = CalorieSettingsDialog(self.calorie_settings, self)
        if dialog.exec_() == QDialog.Accepted:
            self.calorie_settings = dialog.get_settings()
            self.home_page.set_calorie_settings(self.calorie_settings)
            self._save_settings()

    def _toggle_hrv(self, checked):
        self.hrv_enabled = checked
        self.home_page.set_hrv_enabled(checked)
        self._save_settings()

    def _show_obs_settings(self):
        dialog = OBSSettingsDialog(self.obs_settings, self)
        if dialog.exec_() == QDialog.Accepted:
            self.obs_settings = dialog.get_settings()
            self.home_page.set_obs_settings(self.obs_settings)
            self.home_page.update_obs_url_display()
            self._save_settings()

    def _show_data_location(self):
        dialog = DataLocationDialog(self.data_dir, self)
        if dialog.exec_() == QDialog.Accepted:
            new_path = dialog.get_path()
            if new_path != self.data_dir:
                self.data_dir = new_path
                os.makedirs(self.data_dir, exist_ok=True)
                self._save_data_dir()
                QMessageBox.information(self, "提示", f"数据存储位置已更改为:\n{self.data_dir}")

    def _check_update(self):
        self.update_checker = UpdateChecker()
        self.update_checker.update_available.connect(self._on_update_available)
        self.update_checker.no_update.connect(lambda: QMessageBox.information(self, "检查更新", "当前已是最新版本"))
        self.update_checker.error_occurred.connect(lambda e: QMessageBox.warning(self, "检查更新", f"检查更新失败: {e}"))
        self.update_checker.start()

    def _check_update_at_startup(self):
        self.startup_checker = UpdateChecker()
        self.startup_checker.update_available.connect(self._on_update_available)
        self.startup_checker.start()

    def _on_update_available(self, version, download_url):
        reply = QMessageBox.question(
            self, "发现新版本",
            f"新版本 {version} 已发布，是否前往下载？",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes
        )
        if reply == QMessageBox.Yes:
            if download_url:
                webbrowser.open(download_url)
            else:
                webbrowser.open(f"https://github.com/{GITHUB_REPO}/releases/latest")

    def _export_csv(self):
        if not self.daily_records:
            QMessageBox.warning(self, "提示", "没有可导出的数据")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出 CSV",
            f"heart_rate_{time.strftime('%Y%m%d_%H%M%S')}.csv",
            "CSV 文件 (*.csv)"
        )
        if not file_path:
            return

        try:
            with open(file_path, 'w', encoding='utf-8-sig') as f:
                f.write("序号,心率(BPM),时间\n")
                for i, r in enumerate(self.daily_records, 1):
                    time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(r.timestamp))
                    f.write(f"{i},{r.heart_rate},{time_str}\n")
            QMessageBox.information(self, "成功", f"数据已导出到:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出失败: {str(e)}")

    def _export_excel(self):
        if not self.daily_records:
            QMessageBox.warning(self, "提示", "没有可导出的数据")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出 Excel",
            f"heart_rate_{time.strftime('%Y%m%d_%H%M%S')}.xlsx",
            "Excel 文件 (*.xlsx)"
        )
        if not file_path:
            return

        try:
            from openpyxl import Workbook
            wb = Workbook()
            ws = wb.active
            ws.title = "心率数据"

            # 表头
            ws.append(["序号", "心率(BPM)", "时间"])

            # 数据
            for i, r in enumerate(self.daily_records, 1):
                time_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(r.timestamp))
                ws.append([i, r.heart_rate, time_str])

            wb.save(file_path)
            QMessageBox.information(self, "成功", f"数据已导出到:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出失败: {str(e)}")

    # === 数据持久化 ===

    def _get_daily_file_path(self):
        return os.path.join(self.data_dir, f"heart_rate_{self.current_date}.json")

    def _load_daily_records(self):
        """加载当日记录"""
        os.makedirs(self.data_dir, exist_ok=True)
        file_path = self._get_daily_file_path()

        if not os.path.exists(file_path):
            return

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            for item in data:
                if isinstance(item, list) and len(item) >= 2:
                    # 紧凑格式 [timestamp, heart_rate]
                    self.daily_records.append(HeartRateRecord(item[1], item[0]))
                elif isinstance(item, dict):
                    # 兼容旧格式
                    self.daily_records.append(
                        HeartRateRecord(item.get('heart_rate', 0), item.get('timestamp', 0))
                    )

            # 恢复到记录页
            for r in self.daily_records:
                self.record_page.add_record(r.heart_rate)

        except Exception as e:
            print(f"加载记录失败: {e}")

    def _save_daily_records(self):
        """保存当日记录（紧凑格式）"""
        if not self.daily_records:
            return

        os.makedirs(self.data_dir, exist_ok=True)
        file_path = self._get_daily_file_path()

        try:
            data = [[r.timestamp, r.heart_rate] for r in self.daily_records]
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False)
        except Exception as e:
            print(f"保存记录失败: {e}")

    def _check_date_change(self):
        """检查日期变更，自动切换到新的一天"""
        today = datetime.now().strftime("%Y-%m-%d")
        if today != self.current_date:
            # 保存旧日期记录
            self._save_daily_records()
            # 重置
            self.current_date = today
            self.daily_records.clear()
            self.record_page.clear_records()
            # 加载新日期记录
            self._load_daily_records()

    def _load_settings(self):
        """加载设置"""
        settings_path = os.path.join(self.data_dir, "settings.json")
        if os.path.exists(settings_path):
            try:
                with open(settings_path, 'r', encoding='utf-8') as f:
                    settings = json.load(f)

                if 'calorie_settings' in settings:
                    self.calorie_settings.update(settings['calorie_settings'])
                if 'obs_settings' in settings:
                    self.obs_settings.update(settings['obs_settings'])
                if 'hrv_enabled' in settings:
                    self.hrv_enabled = settings['hrv_enabled']
                if 'theme' in settings:
                    self.current_theme = settings['theme']
                if 'close_to_tray' in settings:
                    self.close_to_tray = settings['close_to_tray']
                if 'mini_heart_options' in settings:
                    self.mini_heart_options.update(settings['mini_heart_options'])
                if 'home_display_options' in settings:
                    self.home_display_options.update(settings['home_display_options'])
                if 'connected_device_address' in settings:
                    self.connected_device_address = settings['connected_device_address']
                if 'connected_device_name' in settings:
                    self.connected_device_name = settings['connected_device_name']
            except Exception:
                pass

        # 应用首页显示选项（如果UI已初始化）
        if hasattr(self, 'home_page'):
            for key, visible in self.home_display_options.items():
                self.home_page.set_display_option(key, visible)

        # 恢复已连接设备信息（如果UI已初始化）
        if self.connected_device_address and hasattr(self, 'device_info_action'):
            self.home_page.target_address = self.connected_device_address
            self.device_info_action.setText(f"当前设备: {self.connected_device_name or self.connected_device_address}")
            self.disconnect_action.setEnabled(True)

    def _apply_loaded_settings(self):
        """将加载的设置应用到UI（在UI初始化后调用）"""
        # 应用首页显示选项
        for key, visible in self.home_display_options.items():
            self.home_page.set_display_option(key, visible)

        # 恢复已连接设备信息
        if self.connected_device_address:
            self.home_page.target_address = self.connected_device_address
            self.device_info_action.setText(f"当前设备: {self.connected_device_name or self.connected_device_address}")
            self.disconnect_action.setEnabled(True)

    def _save_settings(self):
        """保存设置"""
        os.makedirs(self.data_dir, exist_ok=True)
        settings_path = os.path.join(self.data_dir, "settings.json")

        settings = {
            'calorie_settings': self.calorie_settings,
            'obs_settings': self.obs_settings,
            'hrv_enabled': self.hrv_enabled,
            'theme': self.current_theme,
            'close_to_tray': self.close_to_tray,
            'mini_heart_options': self.mini_heart_options,
            'home_display_options': self.home_display_options,
            'connected_device_address': self.connected_device_address,
            'connected_device_name': self.connected_device_name
        }

        try:
            with open(settings_path, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _load_data_dir(self):
        """加载数据目录设置"""
        settings_path = os.path.join(self.data_dir, "settings.json")
        if os.path.exists(settings_path):
            try:
                with open(settings_path, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
                    if 'data_dir' in settings:
                        self.data_dir = settings['data_dir']
            except Exception:
                pass

    def _save_data_dir(self):
        """保存数据目录设置"""
        os.makedirs(self.data_dir, exist_ok=True)
        settings_path = os.path.join(self.data_dir, "settings.json")

        settings = {}
        if os.path.exists(settings_path):
            try:
                with open(settings_path, 'r', encoding='utf-8') as f:
                    settings = json.load(f)
            except Exception:
                pass

        settings['data_dir'] = self.data_dir

        try:
            with open(settings_path, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def closeEvent(self, event):
        """关闭窗口时处理"""
        if self.close_to_tray:
            # 最小化到系统托盘
            event.ignore()
            self.hide()
            self.tray.showMessage(
                "心率广播接收器",
                "程序已最小化到系统托盘，双击图标可恢复窗口",
                QSystemTrayIcon.Information,
                2000
            )
        else:
            # 真正退出
            self._save_daily_records()
            self.home_page.cleanup()
            self.mini_heart.stop()
            self.mini_heart.close()
            event.accept()


def main():
    app = QApplication(sys.argv)

    # 加载保存的主题，默认暗夜红心
    settings_path = os.path.join(os.path.expanduser("~"), "HeartRateData", "settings.json")
    saved_theme = DEFAULT_THEME
    if os.path.exists(settings_path):
        try:
            with open(settings_path, 'r', encoding='utf-8') as f:
                settings = json.load(f)
                saved_theme = settings.get('theme', DEFAULT_THEME)
        except Exception:
            pass

    # 应用主题
    theme = apply_theme(app, saved_theme)

    window = HeartRateWindow()
    # 确保窗口使用保存的主题
    window.current_theme = saved_theme
    if saved_theme in window.theme_actions:
        window.theme_actions[saved_theme].setChecked(True)
    # 应用首页颜色
    window._apply_home_page_colors(theme)
    window._update_nav_style()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()