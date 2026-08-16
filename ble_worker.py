# 蓝牙心率广播接收器 - BLE 工作线程
import asyncio
import time
from PyQt5.QtCore import QThread, pyqtSignal
from bleak import BleakClient, BleakScanner
from config import HEART_RATE_SERVICE_UUID, HEART_RATE_MEASUREMENT_UUID, MAX_RECONNECT_ATTEMPTS, HEART_RATE_TIMEOUT


class BleakWorker(QThread):
    """BLE 蓝牙心率设备工作线程"""
    heart_rate_received = pyqtSignal(int)
    rr_interval_received = pyqtSignal(list)
    status_changed = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    connection_lost = pyqtSignal()

    def __init__(self, target_address=None):
        super().__init__()
        self.running = False
        self.client = None
        self.reconnect_count = 0
        self.max_reconnect_attempts = MAX_RECONNECT_ATTEMPTS
        self.last_heart_rate_time = 0
        self.heart_rate_timeout = HEART_RATE_TIMEOUT
        self.target_address = target_address  # 指定设备地址，跳过自动扫描

    def run(self):
        self.running = True
        asyncio.run(self._run_ble())

    async def _run_ble(self):
        # 如果指定了目标地址，直接连接
        if self.target_address:
            device_address = self.target_address
            device_name = self.target_address
            self.status_changed.emit(f"正在连接指定设备: {device_name}")
        else:
            # 自动扫描找到设备
            self.status_changed.emit("正在扫描心率设备...")
            device = await BleakScanner.find_device_by_filter(
                lambda d, ad: HEART_RATE_SERVICE_UUID.lower() in [s.lower() for s in ad.service_uuids]
            )

            if not device:
                self.error_occurred.emit("未找到心率设备，请确保设备已开启并靠近电脑")
                return

            device_address = device.address
            device_name = device.name or device_address
            self.status_changed.emit(f"已找到设备: {device_name}")

        # 循环尝试连接同一个设备
        while self.running:
            try:
                async with BleakClient(device_address) as client:
                    self.client = client
                    self.status_changed.emit(f"已连接: {device_name}")
                    self.reconnect_count = 0
                    self.last_heart_rate_time = time.time()

                    await client.start_notify(
                        HEART_RATE_MEASUREMENT_UUID,
                        self._heart_rate_handler
                    )

                    while self.running:
                        # 检查心率数据是否超时
                        if time.time() - self.last_heart_rate_time > self.heart_rate_timeout:
                            raise Exception("心率数据超时，设备可能已断连")
                        await asyncio.sleep(1)

                    await client.stop_notify(HEART_RATE_MEASUREMENT_UUID)
                    break

            except Exception as e:
                if not self.running:
                    break

                self.reconnect_count += 1
                if self.reconnect_count > self.max_reconnect_attempts:
                    self.error_occurred.emit(f"连接失败: 已尝试重连{self.max_reconnect_attempts}次，请检查设备状态")
                    self.connection_lost.emit()
                    break

                self.status_changed.emit(f"连接断开，正在尝试重连... ({self.reconnect_count}/{self.max_reconnect_attempts})")
                await asyncio.sleep(2)

        self.status_changed.emit("已断开连接")

    def _heart_rate_handler(self, sender, data):
        # 更新最后收到心率数据的时间
        self.last_heart_rate_time = time.time()

        if len(data) < 2:
            return

        flags = data[0]
        offset = 1

        if flags & 0x01:
            heart_rate = int.from_bytes(data[offset:offset+2], byteorder='little')
            offset += 2
        else:
            heart_rate = data[offset]
            offset += 1

        if flags & 0x08:
            offset += 2

        rr_intervals = []
        if flags & 0x10:
            while offset + 1 < len(data):
                rr_raw = int.from_bytes(data[offset:offset+2], byteorder='little')
                rr_ms = rr_raw * (1000.0 / 1024.0)
                if rr_ms > 0:
                    rr_intervals.append(rr_ms)
                offset += 2

        self.heart_rate_received.emit(heart_rate)

        if rr_intervals:
            self.rr_interval_received.emit(rr_intervals)

    def stop(self):
        self.running = False
        self.wait()