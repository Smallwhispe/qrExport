import logging
import logging.handlers
import threading
import sys
import os
from datetime import datetime
from flask import Flask, jsonify
from flask_cors import CORS
from routes.QrBlueprint import qrBp
from services.Manager import Manager
from config.Config import Config


# --------- 可配置的 CORS / 日志项 ---------
_ALLOWED_ORIGINS_RAW = os.getenv('CORS_ALLOW_ORIGINS', '*')
_ALLOWED_ORIGINS = [
    o.strip() for o in _ALLOWED_ORIGINS_RAW.split(',') if o.strip()
] or ['*']
_CORS_SUPPORT_CREDENTIALS = (
    str(os.getenv('CORS_SUPPORT_CREDENTIALS', 'true')).strip().lower() == 'true'
)
_CORS_MAX_AGE = int(os.getenv('CORS_MAX_AGE', str(24 * 3600)))
_CORS_EXPOSE_HEADERS = [
    h.strip() for h in os.getenv('CORS_EXPOSE_HEADERS', 'Content-Type,Authorization').split(',')
    if h.strip()
]

logger = logging.getLogger(__name__)
manager_stop_event = threading.Event()
_manager_instance = None


def get_manager():
    """返回全局 Manager 实例"""
    return _manager_instance


def _setup_logging():
    """控制台 + 按日轮转的日志文件（log/app-YYYY-MM-DD.log）"""
    project_root = os.path.abspath(os.path.dirname(__file__))
    log_dir = os.path.join(project_root, 'log')
    os.makedirs(log_dir, exist_ok=True)

    today = datetime.now().strftime('%Y-%m-%d')
    filename = os.path.join(log_dir, f'app-{today}.log')

    fmt = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s')

    root = logging.getLogger()
    if root.handlers:
        return

    root.setLevel(logging.INFO)

    console = logging.StreamHandler(sys.stdout)
    console.setFormatter(fmt)
    root.addHandler(console)

    file_handler = logging.handlers.TimedRotatingFileHandler(
        filename=filename,
        when='midnight',
        interval=1,
        backupCount=30,
        encoding='utf-8',
        utc=False,
    )
    file_handler.setFormatter(fmt)
    file_handler.suffix = '%Y-%m-%d'
    root.addHandler(file_handler)

    logging.getLogger('werkzeug').setLevel(logging.WARNING)


def _resolve_origins():
    """当 origins 含 '*' 且开启 credentials 时，返回 '*' 让 flask-cors
    自动回显请求 Origin，避免浏览器拒绝带凭证的跨域请求。"""
    if '*' in _ALLOWED_ORIGINS and _CORS_SUPPORT_CREDENTIALS:
        return '*'
    return _ALLOWED_ORIGINS


def create_app():
    app = Flask(__name__)
    CORS(
        app,
        resources={r"/*": {
            "origins": _resolve_origins(),
            "supports_credentials": _CORS_SUPPORT_CREDENTIALS,
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
            "allow_headers": ["Content-Type", "Authorization"],
            "expose_headers": _CORS_EXPOSE_HEADERS,
            "max_age": _CORS_MAX_AGE,
        }}
    )
    app.register_blueprint(qrBp)

    @app.route('/')
    def index():
        return jsonify({
            "service": "QR Export Service",
            "QR_INTERVAL_SECONDS": Config.QR_INTERVAL_SECONDS,
            "endpoints": [
                "GET  /qrExport   - 手动触发一次二维码导出",
                "POST /qrInterval - 更新导出周期（body: {interval_seconds: N}）",
                "GET  /health     - 健康检查",
            ]
        })

    @app.route('/health')
    def health():
        mgr = get_manager()
        return jsonify({
            "status": "ok",
            "manager_running": bool(mgr and mgr.running),
            "qr_interval_seconds": Config.QR_INTERVAL_SECONDS,
        })

    return app


def run_manager():
    """在单独线程中运行 Manager"""
    global _manager_instance
    manager = Manager()
    _manager_instance = manager
    try:
        manager.start()
        logger.info("Manager 服务启动成功")
        manager_stop_event.wait()
    except Exception as e:
        logger.error("Manager 运行异常: %s", e)
    finally:
        if manager.running:
            manager.shutdown()
        logger.info("Manager 服务已关闭")


if __name__ == '__main__':
    _setup_logging()
    logger = logging.getLogger(__name__)

    # 启动后台业务线程
    manager_thread = threading.Thread(target=run_manager, daemon=True)
    manager_thread.start()
    logger.info("Manager 服务线程已启动")

    # 启动 Flask 应用
    logger.info("正在初始化 Flask 应用...")
    app = create_app()
    try:
        logger.info("启动 Flask 应用...")
        app.run(host='0.0.0.0', port=5001, debug=False)
    except KeyboardInterrupt:
        logger.info("接收到中断信号")
        manager_stop_event.set()
    except Exception as e:
        logger.error("应用运行异常: %s", e)
        manager_stop_event.set()
    finally:
        logger.info("正在停止后台服务...")
        manager_stop_event.set()
        manager_thread.join(timeout=2.0)
        logger.info("应用完全退出")
