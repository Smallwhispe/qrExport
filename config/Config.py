import os
from dotenv import load_dotenv

# 加载 .env（支持打包后 exe 同目录的 .env）
if getattr(__import__('sys'), 'frozen', False):
    _base_path = os.path.dirname(__import__('sys').executable)
else:
    _base_path = os.path.abspath('.')
_env_path = os.path.join(_base_path, '.env')
if os.path.exists(_env_path):
    load_dotenv(_env_path)

class Config:
    """QR 项目配置"""
    # QR 调度开关
    QR_START_TRUE = str(os.getenv('QR_START_TRUE', 'false')).strip().lower() == 'true'
    # QR 导出周期（秒）
    QR_INTERVAL_SECONDS = int(os.getenv('QR_INTERVAL_SECONDS', '864000'))
    # 自定义图片查看器命令（空则自动选择）
    QR_IMAGE_VIEWER = os.getenv('QR_IMAGE_VIEWER', '') or None
    # QR 图片生成参数
    QR_SIZE = int(os.getenv('QR_SIZE', '8'))
    QR_BORDER = int(os.getenv('QR_BORDER', '4'))
    QR_FILL_COLOR = os.getenv('QR_FILL_COLOR', 'black')
    QR_BACK_COLOR = os.getenv('QR_BACK_COLOR', 'white')
    # 二维码显示最大边长（像素），超过则等比缩放
    QR_DISPLAY_MAX_SIZE = int(os.getenv('QR_DISPLAY_MAX_SIZE', '800'))

    # Oracle 数据库配置
    ORACLE_USER = os.getenv('ORACLE_USER', '')
    ORACLE_PASSWORD = os.getenv('ORACLE_PASSWORD', '')
    ORACLE_DSN = os.getenv('ORACLE_DSN', '')
    ORACLE_CONFIG_DIR = os.getenv('ORACLE_CONFIG_DIR', '') or None
    ORACLE_WALLET_PASSWORD = os.getenv('ORACLE_WALLET_PASSWORD', '') or None
    ORACLE_TABLE = os.getenv('ORACLE_TABLE', 'data_view')

    # MySQL 数据库配置
    MYSQL_HOST = os.getenv('MYSQL_HOST', '127.0.0.1')
    MYSQL_PORT = int(os.getenv('MYSQL_PORT', '3306'))
    MYSQL_USER = os.getenv('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', '')
    MYSQL_DATABASE = os.getenv('MYSQL_DATABASE', '')
    MYSQL_TABLE = os.getenv('MYSQL_TABLE', 'data_view')
