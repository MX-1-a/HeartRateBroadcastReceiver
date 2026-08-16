# 蓝牙心率广播接收器 - 主题系统
"""三套主题：暗夜红心、极光蓝、暖阳橙"""

# 主题名称常量
THEME_DARK_HEART = "dark_heart"
THEME_AURORA_BLUE = "aurora_blue"
THEME_WARM_SUN = "warm_sun"

THEME_NAMES = {
    THEME_DARK_HEART: "暗夜红心",
    THEME_AURORA_BLUE: "极光蓝",
    THEME_WARM_SUN: "暖阳橙",
}

# === 暗夜红心主题 ===
# 深色背景 + 红色强调，适合心率监测场景
DARK_HEART_PALETTE = {
    'Window': '#1a1a2e',
    'WindowText': '#e0e0e0',
    'Base': '#16213e',
    'AlternateBase': '#1a1a2e',
    'ToolTipBase': '#e0e0e0',
    'ToolTipText': '#1a1a2e',
    'Text': '#e0e0e0',
    'Button': '#0f3460',
    'ButtonText': '#e0e0e0',
    'BrightText': '#e74c3c',
    'Link': '#e74c3c',
    'Highlight': '#e74c3c',
    'HighlightedText': '#ffffff',
}

DARK_HEART_QSS = """
QMainWindow {
    background-color: #1a1a2e;
}
QWidget {
    background-color: #1a1a2e;
    color: #e0e0e0;
    font-family: "Microsoft YaHei", "Arial", sans-serif;
}
QMenuBar {
    background-color: #16213e;
    color: #e0e0e0;
    border-bottom: 1px solid #0f3460;
    padding: 2px;
}
QMenuBar::item {
    padding: 6px 14px;
    background-color: transparent;
    border-radius: 4px;
}
QMenuBar::item:selected {
    background-color: #0f3460;
}
QMenu {
    background-color: #16213e;
    color: #e0e0e0;
    border: 1px solid #0f3460;
    border-radius: 6px;
    padding: 4px;
}
QMenu::item {
    padding: 6px 24px;
    border-radius: 4px;
}
QMenu::item:selected {
    background-color: #e74c3c;
}
QMenu::separator {
    height: 1px;
    background-color: #0f3460;
    margin: 4px 8px;
}
QPushButton {
    background-color: #0f3460;
    color: #e0e0e0;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    font-size: 13px;
    font-weight: bold;
}
QPushButton:hover {
    background-color: #1a4a8a;
}
QPushButton:pressed {
    background-color: #0a2540;
}
QPushButton:disabled {
    background-color: #2a2a3e;
    color: #666666;
}
QLabel {
    background-color: transparent;
    color: #e0e0e0;
}
QGroupBox {
    background-color: #16213e;
    border: 1px solid #0f3460;
    border-radius: 8px;
    margin-top: 12px;
    padding: 12px 8px 8px 8px;
    font-weight: bold;
    color: #e74c3c;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top center;
    padding: 0 8px;
    color: #e74c3c;
}
QStackedWidget {
    background-color: #1a1a2e;
}
QTableWidget {
    background-color: #16213e;
    color: #e0e0e0;
    gridline-color: #0f3460;
    border: 1px solid #0f3460;
    border-radius: 4px;
    selection-background-color: #e74c3c;
    selection-color: #ffffff;
}
QTableWidget::item {
    padding: 4px;
}
QHeaderView::section {
    background-color: #0f3460;
    color: #e0e0e0;
    border: none;
    padding: 6px;
    font-weight: bold;
}
QScrollBar:vertical {
    background-color: #1a1a2e;
    width: 10px;
    border-radius: 5px;
}
QScrollBar::handle:vertical {
    background-color: #0f3460;
    border-radius: 5px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover {
    background-color: #e74c3c;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}
QDialog {
    background-color: #1a1a2e;
    color: #e0e0e0;
}
QLineEdit {
    background-color: #16213e;
    color: #e0e0e0;
    border: 1px solid #0f3460;
    border-radius: 4px;
    padding: 6px;
}
QLineEdit:focus {
    border-color: #e74c3c;
}
QSpinBox, QComboBox {
    background-color: #16213e;
    color: #e0e0e0;
    border: 1px solid #0f3460;
    border-radius: 4px;
    padding: 4px;
}
QComboBox::drop-down {
    border: none;
    width: 20px;
}
QComboBox QAbstractItemView {
    background-color: #16213e;
    color: #e0e0e0;
    selection-background-color: #e74c3c;
    border: 1px solid #0f3460;
}
QCheckBox {
    color: #e0e0e0;
    spacing: 8px;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border-radius: 3px;
    border: 1px solid #0f3460;
    background-color: #16213e;
}
QCheckBox::indicator:checked {
    background-color: #e74c3c;
    border-color: #e74c3c;
}
QTextEdit {
    background-color: #16213e;
    color: #e0e0e0;
    border: 1px solid #0f3460;
    border-radius: 4px;
}
QMessageBox {
    background-color: #1a1a2e;
}
QProgressBar {
    background-color: #16213e;
    border: none;
    border-radius: 4px;
    text-align: center;
    color: #e0e0e0;
}
QProgressBar::chunk {
    background-color: #e74c3c;
    border-radius: 4px;
}
"""

# === 极光蓝主题 ===
# 深蓝背景 + 蓝色强调，医疗专业感
AURORA_BLUE_PALETTE = {
    'Window': '#0d1b2a',
    'WindowText': '#e0e8f0',
    'Base': '#1b2838',
    'AlternateBase': '#0d1b2a',
    'ToolTipBase': '#e0e8f0',
    'ToolTipText': '#0d1b2a',
    'Text': '#e0e8f0',
    'Button': '#1b3a5c',
    'ButtonText': '#e0e8f0',
    'BrightText': '#2196F3',
    'Link': '#2196F3',
    'Highlight': '#2196F3',
    'HighlightedText': '#ffffff',
}

AURORA_BLUE_QSS = """
QMainWindow {
    background-color: #0d1b2a;
}
QWidget {
    background-color: #0d1b2a;
    color: #e0e8f0;
    font-family: "Microsoft YaHei", "Arial", sans-serif;
}
QMenuBar {
    background-color: #1b2838;
    color: #e0e8f0;
    border-bottom: 1px solid #1b3a5c;
    padding: 2px;
}
QMenuBar::item {
    padding: 6px 14px;
    background-color: transparent;
    border-radius: 4px;
}
QMenuBar::item:selected {
    background-color: #1b3a5c;
}
QMenu {
    background-color: #1b2838;
    color: #e0e8f0;
    border: 1px solid #1b3a5c;
    border-radius: 6px;
    padding: 4px;
}
QMenu::item {
    padding: 6px 24px;
    border-radius: 4px;
}
QMenu::item:selected {
    background-color: #2196F3;
}
QMenu::separator {
    height: 1px;
    background-color: #1b3a5c;
    margin: 4px 8px;
}
QPushButton {
    background-color: #1b3a5c;
    color: #e0e8f0;
    border: none;
    border-radius: 6px;
    padding: 8px 16px;
    font-size: 13px;
    font-weight: bold;
}
QPushButton:hover {
    background-color: #2a5a8a;
}
QPushButton:pressed {
    background-color: #0d2a4a;
}
QPushButton:disabled {
    background-color: #1a2a3a;
    color: #556677;
}
QLabel {
    background-color: transparent;
    color: #e0e8f0;
}
QGroupBox {
    background-color: #1b2838;
    border: 1px solid #1b3a5c;
    border-radius: 8px;
    margin-top: 12px;
    padding: 12px 8px 8px 8px;
    font-weight: bold;
    color: #2196F3;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top center;
    padding: 0 8px;
    color: #2196F3;
}
QStackedWidget {
    background-color: #0d1b2a;
}
QTableWidget {
    background-color: #1b2838;
    color: #e0e8f0;
    gridline-color: #1b3a5c;
    border: 1px solid #1b3a5c;
    border-radius: 4px;
    selection-background-color: #2196F3;
    selection-color: #ffffff;
}
QTableWidget::item {
    padding: 4px;
}
QHeaderView::section {
    background-color: #1b3a5c;
    color: #e0e8f0;
    border: none;
    padding: 6px;
    font-weight: bold;
}
QScrollBar:vertical {
    background-color: #0d1b2a;
    width: 10px;
    border-radius: 5px;
}
QScrollBar::handle:vertical {
    background-color: #1b3a5c;
    border-radius: 5px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover {
    background-color: #2196F3;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}
QDialog {
    background-color: #0d1b2a;
    color: #e0e8f0;
}
QLineEdit {
    background-color: #1b2838;
    color: #e0e8f0;
    border: 1px solid #1b3a5c;
    border-radius: 4px;
    padding: 6px;
}
QLineEdit:focus {
    border-color: #2196F3;
}
QSpinBox, QComboBox {
    background-color: #1b2838;
    color: #e0e8f0;
    border: 1px solid #1b3a5c;
    border-radius: 4px;
    padding: 4px;
}
QComboBox::drop-down {
    border: none;
    width: 20px;
}
QComboBox QAbstractItemView {
    background-color: #1b2838;
    color: #e0e8f0;
    selection-background-color: #2196F3;
    border: 1px solid #1b3a5c;
}
QCheckBox {
    color: #e0e8f0;
    spacing: 8px;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border-radius: 3px;
    border: 1px solid #1b3a5c;
    background-color: #1b2838;
}
QCheckBox::indicator:checked {
    background-color: #2196F3;
    border-color: #2196F3;
}
QTextEdit {
    background-color: #1b2838;
    color: #e0e8f0;
    border: 1px solid #1b3a5c;
    border-radius: 4px;
}
QMessageBox {
    background-color: #0d1b2a;
}
QProgressBar {
    background-color: #1b2838;
    border: none;
    border-radius: 4px;
    text-align: center;
    color: #e0e8f0;
}
QProgressBar::chunk {
    background-color: #2196F3;
    border-radius: 4px;
}
"""

# === 暖阳橙主题 ===
# 浅色温暖背景 + 橙色强调，清新健康感
WARM_SUN_PALETTE = {
    'Window': '#f5f0eb',
    'WindowText': '#333333',
    'Base': '#ffffff',
    'AlternateBase': '#f0ebe5',
    'ToolTipBase': '#333333',
    'ToolTipText': '#ffffff',
    'Text': '#333333',
    'Button': '#ffffff',
    'ButtonText': '#333333',
    'BrightText': '#FF9800',
    'Link': '#FF9800',
    'Highlight': '#FF9800',
    'HighlightedText': '#ffffff',
}

WARM_SUN_QSS = """
QMainWindow {
    background-color: #f5f0eb;
}
QWidget {
    background-color: #f5f0eb;
    color: #333333;
    font-family: "Microsoft YaHei", "Arial", sans-serif;
}
QMenuBar {
    background-color: #ffffff;
    color: #333333;
    border-bottom: 1px solid #e0d8d0;
    padding: 2px;
}
QMenuBar::item {
    padding: 6px 14px;
    background-color: transparent;
    border-radius: 4px;
}
QMenuBar::item:selected {
    background-color: #fff3e0;
    color: #FF9800;
}
QMenu {
    background-color: #ffffff;
    color: #333333;
    border: 1px solid #e0d8d0;
    border-radius: 6px;
    padding: 4px;
}
QMenu::item {
    padding: 6px 24px;
    border-radius: 4px;
}
QMenu::item:selected {
    background-color: #FF9800;
    color: #ffffff;
}
QMenu::separator {
    height: 1px;
    background-color: #e0d8d0;
    margin: 4px 8px;
}
QPushButton {
    background-color: #ffffff;
    color: #333333;
    border: 1px solid #e0d8d0;
    border-radius: 6px;
    padding: 8px 16px;
    font-size: 13px;
    font-weight: bold;
}
QPushButton:hover {
    background-color: #fff3e0;
    border-color: #FF9800;
    color: #FF9800;
}
QPushButton:pressed {
    background-color: #ffe0b2;
}
QPushButton:disabled {
    background-color: #f0ebe5;
    color: #aaaaaa;
    border-color: #e0d8d0;
}
QLabel {
    background-color: transparent;
    color: #333333;
}
QGroupBox {
    background-color: #ffffff;
    border: 1px solid #e0d8d0;
    border-radius: 8px;
    margin-top: 12px;
    padding: 12px 8px 8px 8px;
    font-weight: bold;
    color: #FF9800;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top center;
    padding: 0 8px;
    color: #FF9800;
}
QStackedWidget {
    background-color: #f5f0eb;
}
QTableWidget {
    background-color: #ffffff;
    color: #333333;
    gridline-color: #e0d8d0;
    border: 1px solid #e0d8d0;
    border-radius: 4px;
    selection-background-color: #FF9800;
    selection-color: #ffffff;
}
QTableWidget::item {
    padding: 4px;
}
QHeaderView::section {
    background-color: #fff3e0;
    color: #FF9800;
    border: none;
    padding: 6px;
    font-weight: bold;
}
QScrollBar:vertical {
    background-color: #f5f0eb;
    width: 10px;
    border-radius: 5px;
}
QScrollBar::handle:vertical {
    background-color: #e0d8d0;
    border-radius: 5px;
    min-height: 30px;
}
QScrollBar::handle:vertical:hover {
    background-color: #FF9800;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}
QDialog {
    background-color: #f5f0eb;
    color: #333333;
}
QLineEdit {
    background-color: #ffffff;
    color: #333333;
    border: 1px solid #e0d8d0;
    border-radius: 4px;
    padding: 6px;
}
QLineEdit:focus {
    border-color: #FF9800;
}
QSpinBox, QComboBox {
    background-color: #ffffff;
    color: #333333;
    border: 1px solid #e0d8d0;
    border-radius: 4px;
    padding: 4px;
}
QComboBox::drop-down {
    border: none;
    width: 20px;
}
QComboBox QAbstractItemView {
    background-color: #ffffff;
    color: #333333;
    selection-background-color: #FF9800;
    border: 1px solid #e0d8d0;
}
QCheckBox {
    color: #333333;
    spacing: 8px;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border-radius: 3px;
    border: 1px solid #e0d8d0;
    background-color: #ffffff;
}
QCheckBox::indicator:checked {
    background-color: #FF9800;
    border-color: #FF9800;
}
QTextEdit {
    background-color: #ffffff;
    color: #333333;
    border: 1px solid #e0d8d0;
    border-radius: 4px;
}
QMessageBox {
    background-color: #f5f0eb;
}
QProgressBar {
    background-color: #e0d8d0;
    border: none;
    border-radius: 4px;
    text-align: center;
    color: #333333;
}
QProgressBar::chunk {
    background-color: #FF9800;
    border-radius: 4px;
}
"""

# 主题映射表
THEMES = {
    THEME_DARK_HEART: {
        'name': '暗夜红心',
        'palette': DARK_HEART_PALETTE,
        'qss': DARK_HEART_QSS,
        'accent': '#e74c3c',
        'nav_active_home': '#e74c3c',
        'nav_active_record': '#e74c3c',
        'nav_inactive': '#0f3460',
        'heart_color': '#FF4444',
        'bpm_color': '#FF8888',
        'start_btn': '#e74c3c',
        'start_btn_hover': '#c0392b',
        'stop_btn': '#e74c3c',
        'stop_btn_hover': '#c0392b',
    },
    THEME_AURORA_BLUE: {
        'name': '极光蓝',
        'palette': AURORA_BLUE_PALETTE,
        'qss': AURORA_BLUE_QSS,
        'accent': '#2196F3',
        'nav_active_home': '#2196F3',
        'nav_active_record': '#2196F3',
        'nav_inactive': '#1b3a5c',
        'heart_color': '#2196F3',
        'bpm_color': '#64B5F6',
        'start_btn': '#2196F3',
        'start_btn_hover': '#1976D2',
        'stop_btn': '#f44336',
        'stop_btn_hover': '#da190b',
    },
    THEME_WARM_SUN: {
        'name': '暖阳橙',
        'palette': WARM_SUN_PALETTE,
        'qss': WARM_SUN_QSS,
        'accent': '#FF9800',
        'nav_active_home': '#FF9800',
        'nav_active_record': '#FF9800',
        'nav_inactive': '#e0d8d0',
        'heart_color': '#FF5722',
        'bpm_color': '#FF8A65',
        'start_btn': '#FF9800',
        'start_btn_hover': '#F57C00',
        'stop_btn': '#f44336',
        'stop_btn_hover': '#da190b',
    },
}


def apply_theme(app, theme_name):
    """应用主题到QApplication"""
    from PyQt5.QtGui import QPalette, QColor

    if theme_name not in THEMES:
        theme_name = THEME_DARK_HEART

    theme = THEMES[theme_name]
    palette_data = theme['palette']

    app.setStyle("Fusion")
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(palette_data['Window']))
    palette.setColor(QPalette.WindowText, QColor(palette_data['WindowText']))
    palette.setColor(QPalette.Base, QColor(palette_data['Base']))
    palette.setColor(QPalette.AlternateBase, QColor(palette_data['AlternateBase']))
    palette.setColor(QPalette.ToolTipBase, QColor(palette_data['ToolTipBase']))
    palette.setColor(QPalette.ToolTipText, QColor(palette_data['ToolTipText']))
    palette.setColor(QPalette.Text, QColor(palette_data['Text']))
    palette.setColor(QPalette.Button, QColor(palette_data['Button']))
    palette.setColor(QPalette.ButtonText, QColor(palette_data['ButtonText']))
    palette.setColor(QPalette.BrightText, QColor(palette_data['BrightText']))
    palette.setColor(QPalette.Link, QColor(palette_data['Link']))
    palette.setColor(QPalette.Highlight, QColor(palette_data['Highlight']))
    palette.setColor(QPalette.HighlightedText, QColor(palette_data['HighlightedText']))
    app.setPalette(palette)
    app.setStyleSheet(theme['qss'])

    return theme


def get_theme(theme_name):
    """获取主题配置"""
    if theme_name not in THEMES:
        theme_name = THEME_DARK_HEART
    return THEMES[theme_name]