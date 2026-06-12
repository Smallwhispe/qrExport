import logging
import os
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
            # 1) 从 Oracle 取最新一条记录
            from services.qr.OracleRepository import fetch_latest_qr_record
            record = fetch_latest_qr_record(
                user=Config.ORACLE_USER,
                password=Config.ORACLE_PASSWORD,
                dsn=Config.ORACLE_DSN,
                sql=Config.ORACLE_DEFAULT_SQL,
                config_dir=Config.ORACLE_CONFIG_DIR,
                wallet_password=Config.ORACLE_WALLET_PASSWORD,
            )
            if not record:
                return ResultEntityMethod.buildFailedResult(message="Oracle 未查询到可用数据")

            # 2) 把记录格式化为字符串后编二维码，保存到 export/
            lines = []
            for key in sorted(record.keys()):
                val = record[key]
                if val is None:
                    continue
                if hasattr(val, "isoformat"):
                    val = val.isoformat(timespec="seconds") if hasattr(val, "timespec") else val.isoformat()
                lines.append(f"{key}={val}")
            data = "\n".join(lines)

            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_M,
                box_size=request.get("size"),
                border=request.get("border"),
            )
            qr.add_data(data)
            qr.make(fit=True)

            export_dir = EXPORT_DIR
            os.makedirs(export_dir, exist_ok=True)

            def get_unique_filename(export_dir, filename):
                name, ext = os.path.splitext(filename)
                ext = ext or ".png"
                counter = 1
                new_filename = filename
                filepath = os.path.join(export_dir, new_filename)
                while os.path.exists(filepath):
                    new_filename = f"{name}_{counter}{ext}"
                    filepath = os.path.join(export_dir, new_filename)
                    counter += 1
                return new_filename, filepath

            filename = request.get("filename") or "qr.png"
            unique_filename, filepath = get_unique_filename(export_dir, filename)

            img = qr.make_image(fill_color=request.get("fill_color"), back_color=request.get("back_color"))
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
