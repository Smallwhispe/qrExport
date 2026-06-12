"""Oracle 数据源仓库：从 Oracle 数据库读取最新一条二维码所需数据。依赖：python-oracledb。"""
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

def _build_connect_kwargs(user: str, password: str, dsn: str,
                         config_dir: Optional[str] = None,
                         wallet_password: Optional[str] = None) -> Dict[str, Any]:
    kwargs = {"user": user, "password": password, "dsn": dsn}
    if config_dir:
        kwargs["config_dir"] = config_dir
    if wallet_password:
        kwargs["wallet_password"] = wallet_password
    return kwargs

def fetch_latest_qr_record(user: str, password: str, dsn: str, sql: str,
                           config_dir: Optional[str] = None,
                           wallet_password: Optional[str] = None) -> Dict[str, Any]:
    try:
        import oracledb
    except ImportError as e:
        raise RuntimeError("未安装 python-oracledb，请先 `pip install oracledb`") from e
    if not user or not password or not dsn or not sql:
        raise ValueError("Oracle 连接信息或 SQL 不完整")
    connect_kwargs = _build_connect_kwargs(user, password, dsn, config_dir, wallet_password)
    with oracledb.connect(**connect_kwargs) as conn:
        with conn.cursor() as cursor:
            cursor.execute(sql)
            row = cursor.fetchone()
            if row is None:
                logger.warning("[qr oracle] - Oracle 查询返回空结果: sql=%s", sql)
                return {}
            columns = [col[0].lower() for col in cursor.description] if cursor.description else []
            record = dict(zip(columns, row))
            logger.info("[qr oracle] - Oracle 查询成功: %s", record)
            return record
