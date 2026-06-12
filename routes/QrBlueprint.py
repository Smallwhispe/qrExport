import logging
from flask import Blueprint, request, jsonify
from pydantic import ValidationError
from vo.QrExport import QrExportReq
from vo.ResultEntity import ResultEntityMethod, ErrorCode

logger = logging.getLogger(__name__)
qrBp = Blueprint('qrBp', __name__)

@qrBp.route('/qrExport', methods=['GET'])
def qr_export():
    try:
        from services.DataViewService import DataViewService
        result = DataViewService.qr_export(QrExportReq())
        if result.success:
            return jsonify(ResultEntityMethod.buildSuccessResult(
                ErrorCode.SUCCESS.get_code(),
                ErrorCode.SUCCESS.get_msg(),
                result.data
            )), 200
        return jsonify(ResultEntityMethod.buildFailedResult(
            ErrorCode.SERVICE_FAILURE.get_code(),
            ErrorCode.SERVICE_FAILURE.get_msg(),
            None
        )), 500
    except Exception as e:
        logger.error("[qr 导出] - 失败: %s", e)
        return jsonify(ResultEntityMethod.buildFailedResult(
            ErrorCode.FAILURE.get_code(),
            ErrorCode.FAILURE.get_msg(),
            None
        )), 500

@qrBp.route('/qrInterval', methods=['POST'])
def qr_update_interval():
    """动态更新 QR 导出周期（同时更新 env 中的 QR_INTERVAL_SECONDS 和 manager 中的 qr_interval_seconds）"""
    try:
        data = request.get_json()
        if not data or 'interval_seconds' not in data:
            return jsonify(ResultEntityMethod.buildFailedResult(
                ErrorCode.NO_PARAM.get_code(),
                ErrorCode.NO_PARAM.get_msg(),
                None
            )), 400
        interval_seconds = data.get('interval_seconds')
        try:
            interval_seconds = int(interval_seconds)
        except (ValueError, TypeError):
            return jsonify(ResultEntityMethod.buildFailedResult(
                ErrorCode.VALID_FAILURE.get_code(),
                "interval_seconds 必须是正整数",
                None
            )), 400
        if interval_seconds <= 0:
            return jsonify(ResultEntityMethod.buildFailedResult(
                ErrorCode.VALID_FAILURE.get_code(),
                "interval_seconds 必须是正整数",
                None
            )), 400

        import app as Application
        manager = Application.get_manager()
        if manager is None:
            return jsonify(ResultEntityMethod.buildFailedResult(
                ErrorCode.SERVICE_FAILURE.get_code(),
                "Manager 尚未启动",
                None
            )), 503
        ok = manager.update_qr_interval(interval_seconds)
        if not ok:
            return jsonify(ResultEntityMethod.buildFailedResult(
                ErrorCode.SERVICE_FAILURE.get_code(),
                "更新周期失败",
                None
            )), 500
        response = {"interval_seconds": interval_seconds, "updated": True}
        return jsonify(ResultEntityMethod.buildSuccessResult(
            ErrorCode.SUCCESS.get_code(),
            ErrorCode.SUCCESS.get_msg(),
            response
        )), 200
    except Exception as e:
        logger.error("[qr 周期更新] - 失败: %s", e)
        return jsonify(ResultEntityMethod.buildFailedResult(
            ErrorCode.FAILURE.get_code(),
            ErrorCode.FAILURE.get_msg(),
            None
        )), 500
