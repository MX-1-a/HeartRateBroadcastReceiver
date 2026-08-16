# 蓝牙心率广播接收器 - 配置文件

APP_VERSION = "v1.0.2"
GITHUB_REPO = "bluebighead/HeartRateBroadcastDesktopReceiver"
GITHUB_RELEASES_API = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"

# 蓝牙心率服务 UUID
HEART_RATE_SERVICE_UUID = "0000180D-0000-1000-8000-00805F9B34FB"
HEART_RATE_MEASUREMENT_UUID = "00002A37-0000-1000-8000-00805F9B34FB"

# BLE 重连设置
MAX_RECONNECT_ATTEMPTS = 10
HEART_RATE_TIMEOUT = 10  # 秒

# HRV 设置
HRV_WINDOW_SIZE = 30

# 默认卡路里设置
DEFAULT_CALORIE_SETTINGS = {
    'enabled': False,
    'weight': 70,
    'age': 30,
    'gender': 'male'
}

# 默认主题
DEFAULT_THEME = 'dark_heart'

# 关闭行为：最小化到系统托盘
DEFAULT_CLOSE_TO_TRAY = True

# 弹窗心率显示选项
DEFAULT_MINI_HEART_OPTIONS = {
    'title': True,       # 标题"心率监测"
    'heart': True,       # 跳动的小心脏
    'hr_number': True,   # 心率数字
    'bpm': True,         # BPM标签
}

# 首页显示选项
DEFAULT_HOME_DISPLAY_OPTIONS = {
    'heart_rate': True,  # 心率区域（心跳动画+心率数字+BPM）
    'calorie': True,     # 卡路里分组
    'duration': True,    # 运动时长分组
    'hrv': True,         # HRV分组
}