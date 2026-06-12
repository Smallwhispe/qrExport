"""MySQL 数据源仓库：从 MySQL 数据库读取最新一条二维码所需数据。依赖：pymysql。"""
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


def fetch_latest_qr_record(host: str, port: int, user: str, password: str,
                           database: str, sql: str) -> Dict[str, Any]:
    try:
        import pymysql
    except ImportError as e:
        raise RuntimeError("未安装 pymysql，请先 `pip install pymysql`") from e
    if not host or not user or not database or not sql:
        raise ValueError("MySQL 连接信息或 SQL 不完整")
    conn = pymysql.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database=database,
        charset='utf8mb4',
    )
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql)
            row = cursor.fetchone()
            if row is None:
                logger.warning("[qr mysql] - MySQL 查询返回空结果: sql=%s", sql)
                return {}
            columns = [col[0].lower() for col in cursor.description] if cursor.description else []
            record = dict(zip(columns, row))
            logger.info("[qr mysql] - MySQL 查询成功: %s", record)
            return record
    finally:
        conn.close()
