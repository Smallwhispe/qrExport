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

    # Oracle 数据库配置
    ORACLE_USER = os.getenv('ORACLE_USER', '')
    ORACLE_PASSWORD = os.getenv('ORACLE_PASSWORD', '')
    ORACLE_DSN = os.getenv('ORACLE_DSN', '')
    ORACLE_CONFIG_DIR = os.getenv('ORACLE_CONFIG_DIR', '') or None
    ORACLE_WALLET_PASSWORD = os.getenv('ORACLE_WALLET_PASSWORD', '') or None
    ORACLE_DEFAULT_SQL = os.getenv(
        'ORACLE_DEFAULT_SQL',
        "SELECT * FROM (SELECT * FROM your_table ORDER BY sampled_date DESC) WHERE ROWNUM = 1"
    )
