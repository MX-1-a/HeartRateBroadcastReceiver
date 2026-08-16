# 蓝牙心率广播接收器 - 图表窗口
import os
import json
import time
from datetime import datetime, timedelta
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QTabWidget, QLabel
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
import pyqtgraph as pg
import numpy as np


class ChartWindow(QWidget):
    """图表窗口 - 折线图/心率热图/趋势图"""
    def __init__(self, records_getter=None, data_dir=None, parent=None):
        super().__init__(parent)
        self.records_getter = records_getter
        self.data_dir = data_dir or os.path.join(os.path.expanduser("~"), "HeartRateData")
        self.setWindowTitle("心率图表")
        self.setMinimumSize(800, 600)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        self.tab_widget = QTabWidget()

        # 折线图
        self.line_chart_widget = QWidget()
        self.line_chart_layout = QVBoxLayout(self.line_chart_widget)
        self.line_plot = pg.PlotWidget()
        self.line_plot.setBackground('#1E1E1E')
        self.line_plot.setTitle("心率折线图", color='#FFFFFF', size='14pt')
        self.line_plot.setLabel('left', '心率 (BPM)', color='#AAAAAA')
        self.line_plot.setLabel('bottom', '时间', color='#AAAAAA')
        self.line_plot.showGrid(x=True, y=True, alpha=0.3)
        self.line_chart_layout.addWidget(self.line_plot)
        self.tab_widget.addTab(self.line_chart_widget, "折线图")

        # 心率热图
        self.heatmap_widget = QWidget()
        self.heatmap_layout = QVBoxLayout(self.heatmap_widget)
        self.heatmap_plot = pg.PlotWidget()
        self.heatmap_plot.setBackground('#1E1E1E')
        self.heatmap_plot.setTitle("心率热图", color='#FFFFFF', size='14pt')
        self.heatmap_plot.setLabel('left', '小时', color='#AAAAAA')
        self.heatmap_plot.setLabel('bottom', '日期', color='#AAAAAA')
        self.heatmap_layout.addWidget(self.heatmap_plot)
        self.tab_widget.addTab(self.heatmap_widget, "心率热图")

        # 趋势图
        self.trend_widget = QWidget()
        self.trend_layout = QVBoxLayout(self.trend_widget)

        # 周/月切换
        trend_btn_layout = QVBoxLayout()
        self.trend_info_label = QLabel("点击标签页查看趋势图")
        self.trend_info_label.setAlignment(Qt.AlignCenter)
        self.trend_info_label.setStyleSheet("color: #AAAAAA; font-size: 12px;")
        trend_btn_layout.addWidget(self.trend_info_label)
        self.trend_layout.addLayout(trend_btn_layout)

        self.trend_plot = pg.PlotWidget()
        self.trend_plot.setBackground('#1E1E1E')
        self.trend_plot.setTitle("心率趋势", color='#FFFFFF', size='14pt')
        self.trend_plot.setLabel('left', '平均心率 (BPM)', color='#AAAAAA')
        self.trend_plot.setLabel('bottom', '日期', color='#AAAAAA')
        self.trend_plot.showGrid(x=True, y=True, alpha=0.3)
        self.trend_layout.addWidget(self.trend_plot)
        self.tab_widget.addTab(self.trend_widget, "趋势图")

        self.tab_widget.currentChanged.connect(self._on_tab_changed)
        layout.addWidget(self.tab_widget)

    def _on_tab_changed(self, index):
        if index == 0:
            self.update_line_chart()
        elif index == 1:
            self.update_heatmap()
        elif index == 2:
            self.update_trend_chart(7)

    def update_line_chart(self):
        """更新折线图"""
        if not self.records_getter:
            return

        records = self.records_getter()
        if not records:
            return

        self.line_plot.clear()

        heart_rates = [r.heart_rate for r in records]
        timestamps = [r.timestamp for r in records]

        # 使用相对时间（秒）
        start_time = timestamps[0]
        x = [(t - start_time) / 60.0 for t in timestamps]  # 分钟
        y = heart_rates

        # 绘制线条
        self.line_plot.plot(x, y, pen=pg.mkPen(color='#FF4444', width=2))

        # 绘制数据点
        self.line_plot.plot(x, y, pen=None, symbol='o', symbolSize=5,
                           symbolBrush='#FF4444', symbolPen=None)

    def update_heatmap(self):
        """更新心率热图"""
        self.heatmap_plot.clear()

        # 收集所有数据（当前记录+历史文件）
        all_data = self._collect_all_data()
        if not all_data:
            return

        # 按日期+小时分组
        date_hours = {}
        for timestamp, hr in all_data:
            dt = datetime.fromtimestamp(timestamp)
            date_str = dt.strftime("%m-%d")
            hour = dt.hour
            key = (date_str, hour)
            if key not in date_hours:
                date_hours[key] = []
            date_hours[key].append(hr)

        # 计算每格平均值
        dates = sorted(set(k[0] for k in date_hours.keys()))
        hours = list(range(24))

        scatter_data = []
        colors = []
        for i, date_str in enumerate(dates):
            for hour in hours:
                key = (date_str, hour)
                if key in date_hours:
                    avg_hr = sum(date_hours[key]) / len(date_hours[key])
                    scatter_data.append((i, hour, avg_hr))

        if not scatter_data:
            return

        # 绘制散点图模拟热图
        for x, y, hr in scatter_data:
            # 心率到颜色映射：蓝色(低) → 红色(高)
            ratio = max(0, min(1, (hr - 40) / 120.0))
            r = int(255 * ratio)
            b = int(255 * (1 - ratio))
            g = int(100 * (1 - abs(ratio - 0.5) * 2))
            color = (r, g, b, 200)

            scatter = pg.ScatterPlotItem()
            scatter.addPoints([{'x': x, 'y': y, 'size': 20, 'brush': color}])
            self.heatmap_plot.addItem(scatter)

        # 设置坐标轴
        x_ticks = [(i, dates[i]) for i in range(len(dates))]
        y_ticks = [(h, f"{h}:00") for h in range(0, 24, 3)]
        ax = self.heatmap_plot.getAxis('bottom')
        ax.setTicks([x_ticks])
        ay = self.heatmap_plot.getAxis('left')
        ay.setTicks([y_ticks])

    def update_trend_chart(self, days=7):
        """更新趋势图"""
        self.trend_plot.clear()

        # 读取历史数据
        daily_avgs = self._get_daily_averages(days)
        if not daily_avgs:
            self.trend_info_label.setText("暂无历史数据")
            return

        dates = list(daily_avgs.keys())
        avgs = list(daily_avgs.values())

        x = list(range(len(dates)))
        y = avgs

        self.trend_plot.plot(x, y, pen=pg.mkPen(color='#2196F3', width=2))
        self.trend_plot.plot(x, y, pen=None, symbol='o', symbolSize=8,
                           symbolBrush='#2196F3', symbolPen=None)

        # 设置x轴日期标签
        x_ticks = [(i, dates[i]) for i in range(len(dates))]
        ax = self.trend_plot.getAxis('bottom')
        ax.setTicks([x_ticks])

        mode = "周" if days <= 7 else "月"
        self.trend_info_label.setText(f"最近{days}天平均心率趋势 ({mode}视图)")

    def _collect_all_data(self):
        """收集所有数据（当前记录+历史文件）"""
        all_data = []

        # 当前记录
        if self.records_getter:
            records = self.records_getter()
            for r in records:
                all_data.append((r.timestamp, r.heart_rate))

        # 历史文件
        try:
            if os.path.exists(self.data_dir):
                for filename in os.listdir(self.data_dir):
                    if filename.startswith("heart_rate_") and filename.endswith(".json"):
                        filepath = os.path.join(self.data_dir, filename)
                        with open(filepath, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            for item in data:
                                if isinstance(item, list) and len(item) >= 2:
                                    all_data.append((item[0], item[1]))
                                elif isinstance(item, dict):
                                    all_data.append((item.get('timestamp', 0), item.get('heart_rate', 0)))
        except Exception:
            pass

        return all_data

    def _get_daily_averages(self, days):
        """获取每日平均心率"""
        all_data = self._collect_all_data()
        if not all_data:
            return {}

        daily = {}
        for timestamp, hr in all_data:
            date_str = datetime.fromtimestamp(timestamp).strftime("%m-%d")
            if date_str not in daily:
                daily[date_str] = []
            daily[date_str].append(hr)

        # 按日期排序，取最近N天
        sorted_dates = sorted(daily.keys())
        recent_dates = sorted_dates[-days:] if len(sorted_dates) >= days else sorted_dates

        result = {}
        for date_str in recent_dates:
            if daily[date_str]:
                result[date_str] = sum(daily[date_str]) / len(daily[date_str])

        return result

    def set_records_getter(self, getter):
        self.records_getter = getter