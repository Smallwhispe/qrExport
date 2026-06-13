import logging
import os
from datetime import datetime
import qrcode
from vo.QrExport import QrExportReq, QrExportRes
from vo.ResultEntity import ResultEntity, ResultEntityMethod
from config.Config import Config

logger = logging.getLogger(__name__)
EXPORT_DIR = "export"

class DataViewService:
    @staticmethod
    def qr_export(request: QrExportReq) -> ResultEntity:
        try:
            # 1) 从数据库取最新一条记录
            # --- 切换数据源：取消注释即可换回 Oracle ---
            # from services.qr.OracleRepository import fetch_qr_records
            # records = fetch_qr_records(
            #     user=Config.ORACLE_USER,
            #     password=Config.ORACLE_PASSWORD,
            #     dsn=Config.ORACLE_DSN,
            #     table=Config.ORACLE_TABLE,
            #     config_dir=Config.ORACLE_CONFIG_DIR,
            #     wallet_password=Config.ORACLE_WALLET_PASSWORD,
            # )
            # if not records:
            #     return ResultEntityMethod.buildFailedResult(message="Oracle 未查询到可用数据")
            # --- 当前使用 MySQL ---
            from services.qr.MySQLRepository import fetch_qr_records
            records = fetch_qr_records(
                host=Config.MYSQL_HOST,
                port=Config.MYSQL_PORT,
                user=Config.MYSQL_USER,
                password=Config.MYSQL_PASSWORD,
                database=Config.MYSQL_DATABASE,
                table=Config.MYSQL_TABLE,
            )
            if not records:
                return ResultEntityMethod.buildFailedResult(message="MySQL 未查询到可用数据")

            # 2) 将唯一的组合结果格式化为紧凑字符串
            rec = records[0]
            lines = []
            for key in sorted(rec.keys()):
                val = rec[key]
                if val is None:
                    continue
                if hasattr(val, "isoformat"):
                    val = val.isoformat(timespec="seconds") if hasattr(val, "timespec") else val.isoformat()
                lines.append(f"{key}={val}")
            data = "\n".join(lines)

            # 追加导出时间戳
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            data += f"\nts={ts}"

            size = request.get("size")
            if size is None:
                size = Config.QR_SIZE
            border = request.get("border")
            if border is None:
                border = Config.QR_BORDER
            fill_color = request.get("fill_color")
            if fill_color is None:
                fill_color = Config.QR_FILL_COLOR
            back_color = request.get("back_color")
            if back_color is None:
                back_color = Config.QR_BACK_COLOR

            qr = qrcode.QRCode(
                version=None,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=size,
                border=border,
            )
            qr.add_data(data)
            qr.make(fit=True)

            export_dir = EXPORT_DIR
            os.makedirs(export_dir, exist_ok=True)

            filename = request.get("filename") or f"qr_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
            filepath = os.path.join(export_dir, filename)

            img = qr.make_image(fill_color=fill_color, back_color=back_color)

            # 缩放到适合屏幕的尺寸，避免 mspaint 等查看器无法完整显示
            from PIL import Image
            max_dim = Config.QR_DISPLAY_MAX_SIZE
            w, h = img.size
            if w > max_dim or h > max_dim:
                ratio = max_dim / max(w, h)
                new_size = (int(w * ratio), int(h * ratio))
                img = img.resize(new_size, Image.LANCZOS)
                logger.info("[qr 导出] - 图片缩放: %dx%d -> %dx%d", w, h, new_size[0], new_size[1])

            img.save(filepath)
            logger.info("[qr 导出] - 二维码保存成功: %s", filepath)

            # 3) 自动弹出（关闭上一次弹窗）
            try:
                from services.qr.QrImagePopup import popup_image
                popup_image(filepath, viewer_command=Config.QR_IMAGE_VIEWER)
            except Exception as e:
                logger.warning("[qr 导出] - 自动弹出图片失败: %s", e)

            qr_export_res = QrExportRes(
                exportSuccess=True,
                filePath=os.path.abspath(filepath),
            )
            return ResultEntityMethod.buildSuccessResult(data=qr_export_res)
        except Exception as e:
            logger.exception("[qr 导出] - opc qr导出失败: %s", e)
            return ResultEntityMethod.buildFailedResult(message=f"opc qr导出失败: {e}")
