# 蓝牙心率广播接收器 - 蓝牙扫描对话框
import asyncio
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QLabel, QMessageBox
)
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from bleak import BleakScanner
from config import HEART_RATE_SERVICE_UUID


class BleScanWorker(QThread):
    """蓝牙扫描线程"""
    device_found = pyqtSignal(str, str)  # address, name
    scan_finished = pyqtSignal(int)      # 设备数量
    scan_error = pyqtSignal(str)         # 错误信息
    status_changed = pyqtSignal(str)     # 状态信息

    def __init__(self, scan_time=10):
        super().__init__()
        self.scan_time = scan_time
        self.running = False

    def run(self):
        self.running = True
        asyncio.run(self._scan())

    async def _scan(self):
        try:
            self.status_changed.emit("正在扫描蓝牙设备...")
            devices = await BleakScanner.discover(
                timeout=self.scan_time,
                return_adv=True
            )

            count = 0
            for device, adv in devices.values():
                if not self.running:
                    break
                # 过滤出有心率服务的设备，但也显示所有设备
                has_hr_service = HEART_RATE_SERVICE_UUID.lower() in [s.lower() for s in adv.service_uuids]
                name = device.name or "未知设备"
                address = device.address
                
                # 标记心率设备
                if has_hr_service:
                    name = f"[心率] {name}"
                
                self.device_found.emit(address, name)
                count += 1

            self.scan_finished.emit(count)
        except Exception as e:
            self.scan_error.emit(str(e))

    def stop(self):
        self.running = False
        self.wait()


class BluetoothScanDialog(QDialog):
    """蓝牙设备扫描对话框"""
    device_selected = pyqtSignal(str, str)  # address, name

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("蓝牙设备扫描")
        self.setMinimumSize(500, 400)
        self.selected_address = None
        self.selected_name = None
        self.scan_worker = None
        self.devices = {}  # address -> name

        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        # 标题
        title_label = QLabel("扫描附近的蓝牙设备")
        title_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(title_label)

        # 状态标签
        self.status_label = QLabel("点击\"扫描设备\"开始搜索")
        self.status_label.setStyleSheet("color: #888888; font-size: 12px;")
        layout.addWidget(self.status_label)

        # 设备列表
        self.device_list = QListWidget()
        self.device_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #555555;
                border-radius: 4px;
                padding: 5px;
                font-size: 13px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #333333;
            }
            QListWidget::item:selected {
                background-color: #2196F3;
                color: white;
            }
            QListWidget::item:hover {
                background-color: #333333;
            }
        """)
        self.device_list.itemDoubleClicked.connect(self._on_device_double_clicked)
        layout.addWidget(self.device_list)

        # 提示
        hint_label = QLabel("带有 [心率] 标记的设备支持心率监测服务")
        hint_label.setStyleSheet("color: #AAAAAA; font-size: 11px;")
        layout.addWidget(hint_label)

        # 按钮区域
        btn_layout = QHBoxLayout()

        self.scan_btn = QPushButton("扫描设备")
        self.scan_btn.setMinimumHeight(36)
        self.scan_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border-radius: 6px;
                font-size: 13px;
                font-weight: bold;
                padding: 0 20px;
            }
            QPushButton:hover { background-color: #45a049; }
            QPushButton:disabled { background-color: #888888; }
        """)
        self.scan_btn.clicked.connect(self._start_scan)
        btn_layout.addWidget(self.scan_btn)

        self.connect_btn = QPushButton("连接选中设备")
        self.connect_btn.setMinimumHeight(36)
        self.connect_btn.setEnabled(False)
        self.connect_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border-radius: 6px;
                font-size: 13px;
                font-weight: bold;
                padding: 0 20px;
            }
            QPushButton:hover { background-color: #1976D2; }
            QPushButton:disabled { background-color: #888888; }
        """)
        self.connect_btn.clicked.connect(self._on_connect)
        btn_layout.addWidget(self.connect_btn)

        cancel_btn = QPushButton("取消")
        cancel_btn.setMinimumHeight(36)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #555555;
                color: white;
                border-radius: 6px;
                font-size: 13px;
                font-weight: bold;
                padding: 0 20px;
            }
            QPushButton:hover { background-color: #666666; }
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        layout.addLayout(btn_layout)

        # 设备列表选中变化
        self.device_list.itemSelectionChanged.connect(self._on_selection_changed)

    def _start_scan(self):
        """开始扫描蓝牙设备"""
        self.device_list.clear()
        self.devices.clear()
        self.connect_btn.setEnabled(False)
        self.scan_btn.setEnabled(False)
        self.scan_btn.setText("扫描中...")

        # 创建扫描线程
        self.scan_worker = BleScanWorker(scan_time=10)
        self.scan_worker.device_found.connect(self._on_device_found)
        self.scan_worker.scan_finished.connect(self._on_scan_finished)
        self.scan_worker.scan_error.connect(self._on_scan_error)
        self.scan_worker.status_changed.connect(self._on_status_changed)
        self.scan_worker.start()

    def _on_device_found(self, address, name):
        """发现设备"""
        # 去重
        if address in self.devices:
            return
        self.devices[address] = name
        item = QListWidgetItem(f"{name}  ({address})")
        item.setData(Qt.UserRole, address)
        item.setData(Qt.UserRole + 1, name)
        self.device_list.addItem(item)

    def _on_scan_finished(self, count):
        """扫描完成"""
        self.scan_btn.setEnabled(True)
        self.scan_btn.setText("重新扫描")
        self.status_label.setText(f"扫描完成，发现 {count} 个设备")

    def _on_scan_error(self, error):
        """扫描出错"""
        self.scan_btn.setEnabled(True)
        self.scan_btn.setText("扫描设备")
        self.status_label.setText(f"扫描失败: {error}")
        QMessageBox.warning(self, "扫描错误", f"蓝牙扫描失败:\n{error}")

    def _on_status_changed(self, status):
        """状态变化"""
        self.status_label.setText(status)

    def _on_selection_changed(self):
        """选中设备变化"""
        has_selection = len(self.device_list.selectedItems()) > 0
        self.connect_btn.setEnabled(has_selection)

    def _on_device_double_clicked(self, item):
        """双击设备直接连接"""
        self._on_connect()

    def _on_connect(self):
        """连接选中设备"""
        items = self.device_list.selectedItems()
        if not items:
            return

        item = items[0]
        self.selected_address = item.data(Qt.UserRole)
        self.selected_name = item.data(Qt.UserRole + 1)
        
        # 清理 [心率] 标记
        if self.selected_name and self.selected_name.startswith("[心率] "):
            self.selected_name = self.selected_name[5:]

        self.device_selected.emit(self.selected_address, self.selected_name)
        self.accept()

    def closeEvent(self, event):
        """关闭对话框时停止扫描"""
        if self.scan_worker and self.scan_worker.isRunning():
            self.scan_worker.stop()
        event.accept()