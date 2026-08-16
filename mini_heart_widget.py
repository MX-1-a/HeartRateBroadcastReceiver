# 蓝牙心率广播接收器 - 弹窗小心率检测（支持拖拽缩放+等比例缩放+显示选项）
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QSizePolicy, QMenu, QAction
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, pyqtProperty, QPoint, QRect
from PyQt5.QtGui import QFont, QColor, QPainter, QPen, QCursor

# 初始尺寸常量
INIT_WIDTH = 200
INIT_HEIGHT = 100
MIN_WIDTH = 120
MIN_HEIGHT = 60
MAX_WIDTH = 600
MAX_HEIGHT = 300
# 缩放手柄检测区域宽度（像素）
HANDLE_MARGIN = 6

# 默认显示选项
DEFAULT_DISPLAY_OPTIONS = {
    'title': True,       # 标题"心率监测"
    'heart': True,       # 跳动的小心脏
    'hr_number': True,   # 心率数字
    'bpm': True,         # BPM标签
}


class MiniHeartAnimation(QLabel):
    """迷你心跳动画 - 跟随心率节拍缩放"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._scale = 1.0
        self._base_font_size = 28
        self.heart_text = "❤"
        self.setFont(QFont("Arial", self._base_font_size))
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("color: #FF4444;")
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setMinimumSize(1, 1)

        self.beat_animation = QPropertyAnimation(self, b"scale")
        self.beat_animation.setDuration(150)
        self.beat_animation.setKeyValueAt(0, 1.0)
        self.beat_animation.setKeyValueAt(0.3, 1.25)
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
        # 使用基础字号 * 动画缩放 * 窗口缩放比例
        widget_scale = self.width() / 50.0 if self.width() > 0 else 1.0
        font_size = max(1, int(self._base_font_size * self._scale * widget_scale))
        font = self.font()
        font.setPointSize(font_size)
        painter.setFont(font)
        painter.drawText(self.rect(), Qt.AlignCenter, self.heart_text)

    def set_color(self, color):
        self.setStyleSheet(f"color: {color};")

    def set_base_font_size(self, size):
        """设置基础字号（由外部缩放逻辑调用）"""
        self._base_font_size = size
        self.update()


class MiniHeartRateWidget(QWidget):
    """弹窗小心率检测窗口 - 置顶+拖拽移动+拖拽缩放+实时心率+心跳动画+等比例缩放+显示选项"""

    # 缩放方向枚举
    EDGE_NONE = 0
    EDGE_LEFT = 1
    EDGE_TOP = 2
    EDGE_RIGHT = 4
    EDGE_BOTTOM = 8
    EDGE_TOP_LEFT = EDGE_TOP | EDGE_LEFT
    EDGE_TOP_RIGHT = EDGE_TOP | EDGE_RIGHT
    EDGE_BOTTOM_LEFT = EDGE_BOTTOM | EDGE_LEFT
    EDGE_BOTTOM_RIGHT = EDGE_BOTTOM | EDGE_RIGHT

    def __init__(self, parent=None, display_options=None):
        super().__init__(parent)
        self.current_heart_rate = 0
        self._drag_pos = QPoint()

        # 显示选项
        self.display_options = dict(DEFAULT_DISPLAY_OPTIONS)
        if display_options:
            self.display_options.update(display_options)

        # 缩放状态
        self._resizing = False
        self._resize_edge = self.EDGE_NONE
        self._resize_start_geo = QRect()
        self._resize_start_pos = QPoint()

        # 缩放比例
        self._scale_factor = 1.0

        self.setWindowFlags(
            Qt.Window |  # 独立窗口
            Qt.WindowStaysOnTopHint |  # 置顶
            Qt.FramelessWindowHint |  # 无边框
            Qt.Tool  # 任务栏不显示
        )
        self.setAttribute(Qt.WA_TranslucentBackground, False)
        # 允许缩放：设置初始大小和最小/最大限制
        self.resize(INIT_WIDTH, INIT_HEIGHT)
        self.setMinimumSize(MIN_WIDTH, MIN_HEIGHT)
        self.setMaximumSize(MAX_WIDTH, MAX_HEIGHT)
        # 开启鼠标追踪以检测缩放手柄悬停
        self.setMouseTracking(True)
        # 启用右键菜单
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)

        self._init_ui()
        self._init_timers()
        self._apply_display_options()

    def _detect_edge(self, pos):
        """检测鼠标位置是否在缩放手柄区域，返回方向枚举"""
        x, y = pos.x(), pos.y()
        w, h = self.width(), self.height()
        m = HANDLE_MARGIN

        left = x <= m
        right = x >= w - m
        top = y <= m
        bottom = y >= h - m

        edge = self.EDGE_NONE
        if left:
            edge |= self.EDGE_LEFT
        if right:
            edge |= self.EDGE_RIGHT
        if top:
            edge |= self.EDGE_TOP
        if bottom:
            edge |= self.EDGE_BOTTOM
        return edge

    def _edge_cursor(self, edge):
        """根据缩放方向返回对应的光标样式"""
        cursor_map = {
            self.EDGE_LEFT: Qt.SizeHorCursor,
            self.EDGE_RIGHT: Qt.SizeHorCursor,
            self.EDGE_TOP: Qt.SizeVerCursor,
            self.EDGE_BOTTOM: Qt.SizeVerCursor,
            self.EDGE_TOP_LEFT: Qt.SizeFDiagCursor,
            self.EDGE_BOTTOM_RIGHT: Qt.SizeFDiagCursor,
            self.EDGE_TOP_RIGHT: Qt.SizeBDiagCursor,
            self.EDGE_BOTTOM_LEFT: Qt.SizeBDiagCursor,
        }
        return cursor_map.get(edge, Qt.ArrowCursor)

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(2)

        # 标题栏（可拖拽区域）+ 关闭按钮
        self.title_layout = QHBoxLayout()
        self.title_layout.setContentsMargins(0, 0, 0, 0)

        self.title_label = QLabel("心率监测")
        self.title_label.setFont(QFont("Microsoft YaHei", 9))
        self.title_label.setStyleSheet("color: #AAAAAA;")
        self.title_label.setCursor(QCursor(Qt.SizeAllCursor))
        self.title_layout.addWidget(self.title_label)

        self.title_layout.addStretch()

        self.close_btn = QPushButton("✕")
        self.close_btn.setFixedSize(18, 18)
        self.close_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #888888;
                border: none;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                color: #FF4444;
                background-color: rgba(255, 68, 68, 30);
                border-radius: 9px;
            }
        """)
        self.close_btn.clicked.connect(self.hide)
        self.title_layout.addWidget(self.close_btn)

        layout.addLayout(self.title_layout)

        # 心跳动画 + 心率数值
        self.content_layout = QHBoxLayout()
        self.content_layout.setSpacing(6)

        self.heart_animation = MiniHeartAnimation()
        self.heart_animation.setMinimumSize(30, 30)
        self.content_layout.addWidget(self.heart_animation, 1)

        # 心率数值区域
        self.hr_layout = QVBoxLayout()
        self.hr_layout.setSpacing(0)

        self.hr_label = QLabel("--")
        self.hr_label.setFont(QFont("Arial", 32, QFont.Bold))
        self.hr_label.setStyleSheet("color: #FF4444;")
        self.hr_label.setAlignment(Qt.AlignCenter)
        self.hr_layout.addWidget(self.hr_label)

        self.bpm_label = QLabel("BPM")
        self.bpm_label.setFont(QFont("Arial", 10))
        self.bpm_label.setStyleSheet("color: #FF8888;")
        self.bpm_label.setAlignment(Qt.AlignCenter)
        self.hr_layout.addWidget(self.bpm_label)

        self.content_layout.addLayout(self.hr_layout, 2)

        layout.addLayout(self.content_layout, 1)

        # 设置整体样式
        self._update_style()

    def _update_style(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #1a1a2e;
                border: 1px solid #333355;
                border-radius: 12px;
            }
        """)

    def _init_timers(self):
        # 状态检查定时器
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self._check_status)
        self.status_timer.start(2000)

    def _check_status(self):
        """检查心率数据是否还在更新"""
        pass  # 由外部更新心率

    # === 显示选项 ===
    def _show_context_menu(self, pos):
        """右键菜单 - 显示选项"""
        menu = QMenu(self)

        title_action = menu.addAction("显示标题")
        title_action.setCheckable(True)
        title_action.setChecked(self.display_options['title'])

        heart_action = menu.addAction("显示心跳动画")
        heart_action.setCheckable(True)
        heart_action.setChecked(self.display_options['heart'])

        hr_action = menu.addAction("显示心率数字")
        hr_action.setCheckable(True)
        hr_action.setChecked(self.display_options['hr_number'])

        bpm_action = menu.addAction("显示BPM标签")
        bpm_action.setCheckable(True)
        bpm_action.setChecked(self.display_options['bpm'])

        action = menu.exec_(self.mapToGlobal(pos))

        if action == title_action:
            self.set_display_option('title', action.isChecked())
        elif action == heart_action:
            self.set_display_option('heart', action.isChecked())
        elif action == hr_action:
            self.set_display_option('hr_number', action.isChecked())
        elif action == bpm_action:
            self.set_display_option('bpm', action.isChecked())

    def set_display_option(self, key, visible):
        """设置显示选项并更新UI"""
        self.display_options[key] = visible
        self._apply_display_options()

    def _apply_display_options(self):
        """根据显示选项更新控件可见性"""
        # 标题
        self.title_label.setVisible(self.display_options['title'])

        # 心跳动画
        self.heart_animation.setVisible(self.display_options['heart'])

        # 心率数字
        self.hr_label.setVisible(self.display_options['hr_number'])

        # BPM标签
        self.bpm_label.setVisible(self.display_options['bpm'])

        # 如果心跳动画隐藏，心率区域占满
        if not self.display_options['heart']:
            self.content_layout.setStretch(0, 0)
            self.content_layout.setStretch(1, 1)
        else:
            self.content_layout.setStretch(0, 1)
            self.content_layout.setStretch(1, 2)

        self.update()

    def _apply_scale(self):
        """根据当前窗口尺寸计算缩放比例，并更新所有子控件尺寸和字体"""
        # 基于宽度计算缩放比例
        self._scale_factor = self.width() / INIT_WIDTH

        # 标题字体
        title_size = max(6, int(9 * self._scale_factor))
        self.title_label.setFont(QFont("Microsoft YaHei", title_size))

        # 关闭按钮
        btn_size = max(12, int(18 * self._scale_factor))
        self.close_btn.setFixedSize(btn_size, btn_size)
        btn_font_size = max(8, int(12 * self._scale_factor))
        self.close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: #888888;
                border: none;
                font-size: {btn_font_size}px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                color: #FF4444;
                background-color: rgba(255, 68, 68, 30);
                border-radius: {btn_size // 2}px;
            }}
        """)

        # 心率数值字体
        hr_size = max(12, int(32 * self._scale_factor))
        self.hr_label.setFont(QFont("Arial", hr_size, QFont.Bold))

        # BPM标签字体
        bpm_size = max(6, int(10 * self._scale_factor))
        self.bpm_label.setFont(QFont("Arial", bpm_size))

        # 心跳动画基础字号
        heart_font = max(10, int(28 * self._scale_factor))
        self.heart_animation.set_base_font_size(heart_font)

        # 边距和间距等比例缩放
        margin = max(4, int(8 * self._scale_factor))
        self.layout().setContentsMargins(margin, margin, margin, margin)
        spacing = max(1, int(2 * self._scale_factor))
        self.layout().setSpacing(spacing)

        # 内容区域间距
        content_item = self.layout().itemAt(1)
        if content_item and content_item.layout():
            content_item.layout().setSpacing(max(2, int(6 * self._scale_factor)))

        self.update()

    def resizeEvent(self, event):
        """窗口大小改变时，等比例缩放所有内容"""
        super().resizeEvent(event)
        self._apply_scale()

    def update_heart_rate(self, hr):
        """更新心率数据 - 由主窗口调用"""
        self.current_heart_rate = hr
        self.hr_label.setText(str(hr))
        self.heart_animation.set_heart_rate(hr)

    def stop(self):
        """停止监测"""
        self.current_heart_rate = 0
        self.hr_label.setText("--")
        self.heart_animation.stop_beat()

    def apply_theme(self, theme):
        """应用主题配色"""
        bg_color = theme['palette']['Window']
        accent = theme['accent']
        heart_color = theme['heart_color']
        bpm_color = theme['bpm_color']
        border_color = theme['palette']['Button']

        self.setStyleSheet(f"""
            QWidget {{
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-radius: 12px;
            }}
        """)
        self.title_label.setStyleSheet(f"color: {theme['palette']['WindowText']};")
        self.hr_label.setStyleSheet(f"color: {heart_color};")
        self.bpm_label.setStyleSheet(f"color: {bpm_color};")
        self.heart_animation.set_color(heart_color)

    # === 鼠标事件：拖拽移动 + 拖拽缩放 ===
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            edge = self._detect_edge(event.pos())
            if edge != self.EDGE_NONE:
                # 缩放模式
                self._resizing = True
                self._resize_edge = edge
                self._resize_start_geo = self.geometry()
                self._resize_start_pos = event.globalPos()
                event.accept()
            else:
                # 拖拽移动模式
                self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()
                event.accept()

    def mouseMoveEvent(self, event):
        if self._resizing and event.buttons() & Qt.LeftButton:
            # 缩放逻辑
            delta = event.globalPos() - self._resize_start_pos
            geo = QRect(self._resize_start_geo)

            # 根据缩放方向调整几何
            if self._resize_edge & self.EDGE_LEFT:
                new_left = geo.left() + delta.x()
                new_width = geo.right() - new_left + 1
                if new_width >= self.minimumWidth():
                    geo.setLeft(new_left)
                else:
                    geo.setLeft(geo.right() - self.minimumWidth() + 1)

            if self._resize_edge & self.EDGE_RIGHT:
                new_width = geo.width() + delta.x()
                if new_width >= self.minimumWidth():
                    geo.setWidth(new_width)
                else:
                    geo.setWidth(self.minimumWidth())

            if self._resize_edge & self.EDGE_TOP:
                new_top = geo.top() + delta.y()
                new_height = geo.bottom() - new_top + 1
                if new_height >= self.minimumHeight():
                    geo.setTop(new_top)
                else:
                    geo.setTop(geo.bottom() - self.minimumHeight() + 1)

            if self._resize_edge & self.EDGE_BOTTOM:
                new_height = geo.height() + delta.y()
                if new_height >= self.minimumHeight():
                    geo.setHeight(new_height)
                else:
                    geo.setHeight(self.minimumHeight())

            # 限制最大尺寸
            if geo.width() > self.maximumWidth():
                if self._resize_edge & self.EDGE_LEFT:
                    geo.setLeft(geo.right() - self.maximumWidth() + 1)
                else:
                    geo.setWidth(self.maximumWidth())
            if geo.height() > self.maximumHeight():
                if self._resize_edge & self.EDGE_TOP:
                    geo.setTop(geo.bottom() - self.maximumHeight() + 1)
                else:
                    geo.setHeight(self.maximumHeight())

            self.setGeometry(geo)
            event.accept()
        elif event.buttons() & Qt.LeftButton and not self._resizing:
            # 拖拽移动
            self.move(event.globalPos() - self._drag_pos)
            event.accept()
        else:
            # 悬停检测 - 更新光标样式
            edge = self._detect_edge(event.pos())
            if edge != self.EDGE_NONE:
                self.setCursor(QCursor(self._edge_cursor(edge)))
            else:
                self.unsetCursor()

    def mouseReleaseEvent(self, event):
        if self._resizing:
            self._resizing = False
            self._resize_edge = self.EDGE_NONE
        event.accept()

    def closeEvent(self, event):
        """关闭时只隐藏，不销毁"""
        event.ignore()
        self.hide()