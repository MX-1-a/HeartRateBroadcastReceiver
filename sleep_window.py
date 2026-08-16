# 蓝牙心率广播接收器 - 睡眠分析窗口
import os
import time
from datetime import datetime
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QProgressBar, QTextEdit, QFileDialog, QMessageBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
import pyqtgraph as pg


class SleepAnalysisWindow(QWidget):
    """睡眠分析窗口 - 自动检测睡眠时段、质量评分、改善建议"""
    def __init__(self, records_getter=None, parent=None):
        super().__init__(parent)
        self.records_getter = records_getter
        self.setWindowTitle("睡眠分析")
        self.setMinimumSize(700, 600)
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)

        # 标题
        title = QLabel("睡眠分析")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # 睡眠质量评分
        score_layout = QHBoxLayout()
        score_label = QLabel("睡眠质量评分:")
        score_label.setFont(QFont("Arial", 12))
        score_layout.addWidget(score_label)

        self.score_value_label = QLabel("--")
        self.score_value_label.setFont(QFont("Arial", 24, QFont.Bold))
        self.score_value_label.setStyleSheet("color: #2196F3;")
        self.score_value_label.setAlignment(Qt.AlignCenter)
        score_layout.addWidget(self.score_value_label)

        self.score_desc_label = QLabel("")
        self.score_desc_label.setStyleSheet("color: #AAAAAA; font-size: 12px;")
        score_layout.addWidget(self.score_desc_label)
        score_layout.addStretch()
        layout.addLayout(score_layout)

        # 睡眠时长
        self.duration_label = QLabel("睡眠时长: --")
        self.duration_label.setFont(QFont("Arial", 12))
        layout.addWidget(self.duration_label)

        # 睡眠时段
        self.period_label = QLabel("睡眠时段: --")
        self.period_label.setFont(QFont("Arial", 12))
        layout.addWidget(self.period_label)

        # 三状态分布进度条
        state_layout = QHBoxLayout()

        awake_label = QLabel("清醒")
        awake_label.setStyleSheet("color: #FF9800; font-size: 11px;")
        state_layout.addWidget(awake_label)
        self.awake_bar = QProgressBar()
        self.awake_bar.setStyleSheet("""
            QProgressBar { background-color: #1E1E1E; border: none; text-align: center; }
            QProgressBar::chunk { background-color: #FF9800; }
        """)
        state_layout.addWidget(self.awake_bar)

        light_label = QLabel("浅睡")
        light_label.setStyleSheet("color: #2196F3; font-size: 11px;")
        state_layout.addWidget(light_label)
        self.light_bar = QProgressBar()
        self.light_bar.setStyleSheet("""
            QProgressBar { background-color: #1E1E1E; border: none; text-align: center; }
            QProgressBar::chunk { background-color: #2196F3; }
        """)
        state_layout.addWidget(self.light_bar)

        deep_label = QLabel("深睡")
        deep_label.setStyleSheet("color: #4CAF50; font-size: 11px;")
        state_layout.addWidget(deep_label)
        self.deep_bar = QProgressBar()
        self.deep_bar.setStyleSheet("""
            QProgressBar { background-color: #1E1E1E; border: none; text-align: center; }
            QProgressBar::chunk { background-color: #4CAF50; }
        """)
        state_layout.addWidget(self.deep_bar)

        layout.addLayout(state_layout)

        # 睡眠状态折线图
        self.sleep_plot = pg.PlotWidget()
        self.sleep_plot.setBackground('#1E1E1E')
        self.sleep_plot.setTitle("睡眠状态", color='#FFFFFF', size='12pt')
        self.sleep_plot.setLabel('left', '心率 (BPM)', color='#AAAAAA')
        self.sleep_plot.setLabel('bottom', '时间', color='#AAAAAA')
        self.sleep_plot.showGrid(x=True, y=True, alpha=0.3)
        layout.addWidget(self.sleep_plot)

        # 改善建议
        self.advice_text = QTextEdit()
        self.advice_text.setReadOnly(True)
        self.advice_text.setMaximumHeight(120)
        self.advice_text.setStyleSheet("""
            QTextEdit {
                background-color: #1E1E1E;
                color: #DDDDDD;
                border: 1px solid #3D3D3D;
                border-radius: 4px;
            }
        """)
        layout.addWidget(self.advice_text)

        # 按钮
        btn_layout = QHBoxLayout()

        self.analyze_btn = QPushButton("分析睡眠")
        self.analyze_btn.setMinimumHeight(35)
        self.analyze_btn.setStyleSheet("""
            QPushButton {
                background-color: #9C27B0;
                color: white;
                border-radius: 4px;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #7B1FA2; }
        """)
        self.analyze_btn.clicked.connect(self.analyze_sleep)
        btn_layout.addWidget(self.analyze_btn)

        self.export_btn = QPushButton("导出报告")
        self.export_btn.setMinimumHeight(35)
        self.export_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border-radius: 4px;
                font-size: 13px;
            }
            QPushButton:hover { background-color: #1976D2; }
        """)
        self.export_btn.clicked.connect(self.export_report)
        btn_layout.addWidget(self.export_btn)

        layout.addLayout(btn_layout)

        # 存储分析结果
        self.sleep_data = None

    def analyze_sleep(self):
        """分析睡眠数据"""
        if not self.records_getter:
            QMessageBox.warning(self, "提示", "没有可用的心率数据")
            return

        records = self.records_getter()
        if len(records) < 10:
            QMessageBox.warning(self, "提示", "数据量不足，至少需要10条记录才能分析")
            return

        heart_rates = [r.heart_rate for r in records]
        timestamps = [r.timestamp for r in records]

        # 移动平均平滑（窗口5）
        smoothed = []
        window = 5
        for i in range(len(heart_rates)):
            start = max(0, i - window // 2)
            end = min(len(heart_rates), i + window // 2 + 1)
            avg = sum(heart_rates[start:end]) / (end - start)
            smoothed.append(avg)

        # 自动检测睡眠时段：阈值65，最少10条记录
        sleep_threshold = 65
        sleep_indices = [i for i, hr in enumerate(smoothed) if hr < sleep_threshold]

        if len(sleep_indices) < 10:
            QMessageBox.warning(self, "提示", "未检测到明显的睡眠时段（心率普遍高于65 BPM）")
            return

        # 找到连续睡眠时段
        sleep_start_idx = sleep_indices[0]
        sleep_end_idx = sleep_indices[-1]

        sleep_heart_rates = heart_rates[sleep_start_idx:sleep_end_idx + 1]
        sleep_timestamps = timestamps[sleep_start_idx:sleep_end_idx + 1]

        # 三状态分类
        awake_count = 0
        light_count = 0
        deep_count = 0

        for hr in sleep_heart_rates:
            if hr > 70:
                awake_count += 1
            elif hr >= 60:
                light_count += 1
            else:
                deep_count += 1

        total_sleep = len(sleep_heart_rates)
        awake_pct = awake_count / total_sleep * 100
        light_pct = light_count / total_sleep * 100
        deep_pct = deep_count / total_sleep * 100

        # 更新进度条
        self.awake_bar.setValue(int(awake_pct))
        self.awake_bar.setFormat(f"{awake_pct:.1f}%")
        self.light_bar.setValue(int(light_pct))
        self.light_bar.setFormat(f"{light_pct:.1f}%")
        self.deep_bar.setValue(int(deep_pct))
        self.deep_bar.setFormat(f"{deep_pct:.1f}%")

        # 睡眠时长
        sleep_duration = sleep_timestamps[-1] - sleep_timestamps[0]
        hours = int(sleep_duration) // 3600
        minutes = (int(sleep_duration) % 3600) // 60
        self.duration_label.setText(f"睡眠时长: {hours}小时{minutes}分钟")

        # 睡眠时段
        start_time = datetime.fromtimestamp(sleep_timestamps[0]).strftime("%H:%M")
        end_time = datetime.fromtimestamp(sleep_timestamps[-1]).strftime("%H:%M")
        self.period_label.setText(f"睡眠时段: {start_time} - {end_time}")

        # 质量评分：时长分(60%) + 深睡分(40%)
        # 时长分：8小时满分
        duration_hours = sleep_duration / 3600.0
        duration_score = min(100, (duration_hours / 8.0) * 100) * 0.6

        # 深睡分：50%深睡比例满分
        deep_score = min(100, (deep_pct / 50.0) * 100) * 0.4

        total_score = int(duration_score + deep_score)
        self.score_value_label.setText(str(total_score))

        if total_score >= 80:
            desc = "优秀"
            color = "#4CAF50"
        elif total_score >= 60:
            desc = "良好"
            color = "#8BC34A"
        elif total_score >= 40:
            desc = "一般"
            color = "#FF9800"
        else:
            desc = "较差"
            color = "#f44336"

        self.score_desc_label.setText(desc)
        self.score_desc_label.setStyleSheet(f"color: {color}; font-size: 12px;")

        # 绘制睡眠状态折线图
        self.sleep_plot.clear()
        start_ts = sleep_timestamps[0]
        x = [(t - start_ts) / 60.0 for t in sleep_timestamps]  # 分钟
        y = sleep_heart_rates

        # 阈值线
        self.sleep_plot.addLine(y=65, pen=pg.mkPen(color='#FF9800', style='Qt.DashLine', width=1))
        self.sleep_plot.addLine(y=60, pen=pg.mkPen(color='#4CAF50', style='Qt.DashLine', width=1))

        self.sleep_plot.plot(x, y, pen=pg.mkPen(color='#2196F3', width=2))

        # 改善建议
        advice = self._generate_advice(total_score, duration_hours, deep_pct, awake_pct)
        self.advice_text.setPlainText(advice)

        # 存储分析结果
        self.sleep_data = {
            'score': total_score,
            'duration': sleep_duration,
            'start_time': start_time,
            'end_time': end_time,
            'awake_pct': awake_pct,
            'light_pct': light_pct,
            'deep_pct': deep_pct,
            'avg_hr': sum(sleep_heart_rates) / len(sleep_heart_rates),
            'min_hr': min(sleep_heart_rates),
            'max_hr': max(sleep_heart_rates),
            'advice': advice
        }

    def _generate_advice(self, score, duration_hours, deep_pct, awake_pct):
        """生成改善建议"""
        advices = []

        if score >= 80:
            advices.append("✅ 睡眠质量优秀，请继续保持良好的睡眠习惯。")
        elif score >= 60:
            advices.append("👍 睡眠质量良好，仍有提升空间。")
        elif score >= 40:
            advices.append("⚠️ 睡眠质量一般，建议关注以下改善措施。")
        else:
            advices.append("❌ 睡眠质量较差，强烈建议改善睡眠习惯。")

        if duration_hours < 6:
            advices.append("• 睡眠时长不足6小时，建议每晚保证7-9小时睡眠。")
        elif duration_hours < 7:
            advices.append("• 睡眠时长略偏短，建议适当延长至7-8小时。")
        elif duration_hours > 9:
            advices.append("• 睡眠时长偏长，可能暗示身体疲劳或健康问题。")

        if deep_pct < 15:
            advices.append("• 深睡比例偏低，建议减少睡前蓝光暴露，保持卧室安静黑暗。")
        elif deep_pct < 25:
            advices.append("• 深睡比例可进一步提升，建议规律作息。")

        if awake_pct > 20:
            advices.append("• 清醒时间占比过高，可能存在睡眠中断，建议排查睡眠障碍。")

        advices.append("\n通用建议：")
        advices.append("• 保持规律作息，每天同一时间入睡和起床")
        advices.append("• 睡前1小时避免使用电子设备")
        advices.append("• 保持卧室温度在18-22°C")
        advices.append("• 睡前避免咖啡因和酒精摄入")

        return "\n".join(advices)

    def export_report(self):
        """导出睡眠分析报告"""
        if not self.sleep_data:
            QMessageBox.warning(self, "提示", "请先进行睡眠分析")
            return

        file_path, _ = QFileDialog.getSaveFileName(
            self, "导出睡眠报告", f"sleep_report_{time.strftime('%Y%m%d')}.txt",
            "文本文件 (*.txt)"
        )
        if not file_path:
            return

        try:
            d = self.sleep_data
            hours = int(d['duration']) // 3600
            minutes = (int(d['duration']) % 3600) // 60

            report = f"""=== 睡眠分析报告 ===
日期: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

睡眠质量评分: {d['score']}/100
睡眠时长: {hours}小时{minutes}分钟
睡眠时段: {d['start_time']} - {d['end_time']}

睡眠状态分布:
  清醒: {d['awake_pct']:.1f}%
  浅睡: {d['light_pct']:.1f}%
  深睡: {d['deep_pct']:.1f}%

心率统计:
  平均心率: {d['avg_hr']:.1f} BPM
  最低心率: {d['min_hr']} BPM
  最高心率: {d['max_hr']} BPM

改善建议:
{d['advice']}
"""
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(report)

            QMessageBox.information(self, "成功", f"报告已导出到:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"导出失败: {str(e)}")

    def set_records_getter(self, getter):
        self.records_getter = getter