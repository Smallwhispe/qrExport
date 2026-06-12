import logging
import time
import threading
from concurrent.futures import ThreadPoolExecutor
from services.DataViewService import DataViewService
from config.Config import Config

logger = logging.getLogger(__name__)

class Manager:
    def __init__(self):
        self.qr_interval_seconds = Config.QR_INTERVAL_SECONDS
        self.qr_scheduler_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="Manager-QrScheduler")
        self._running = False

    def start(self):
        """启动 QR 定时调度"""
        if self._running:
            logger.warning("服务已经在运行中")
            return
        self._running = True
        logger.info("[QR 调度] - 启动 QR 定时任务 (周期=%d 秒)", self.qr_interval_seconds)
        self.qr_scheduler_executor.submit(self.schedule_qr_export)

    def schedule_qr_export(self):
        """定时从 Oracle 取最新数据并导出二维码"""
        from vo.QrExport import QrExportReq
        while self._running:
            try:
                DataViewService.qr_export(QrExportReq())
            except Exception as e:
                logger.error("[QR 调度] - 二维码导出异常: %s", e)
            remaining = int(self.qr_interval_seconds)
            step = max(1, min(5, remaining)) if remaining > 0 else 1
            while remaining > 0 and self._running:
                time.sleep(min(step, remaining))
                remaining -= step

    def update_qr_interval(self, seconds: int) -> bool:
        """动态更新 QR 导出周期（同时更新 Config 和 Manager 实例）"""
        try:
            seconds = int(seconds)
            if seconds <= 0:
                logger.error("[QR 调度] - 无效的周期值: %s", seconds)
                return False
            Config.QR_INTERVAL_SECONDS = seconds
            self.qr_interval_seconds = seconds
            logger.info("[QR 调度] - 周期已更新为 %s 秒", seconds)
            return True
        except Exception as e:
            logger.error("[QR 调度] - 更新周期失败: %s", e)
            return False

    def shutdown(self):
        if not self._running:
            return
        logger.info("[QR 调度] - Manager 服务关闭中...")
        self._running = False
        self.qr_scheduler_executor.shutdown(wait=False, cancel_futures=True)
        logger.info("[QR 调度] - Manager 服务已关闭")

    @property
    def running(self):
        return self._running
