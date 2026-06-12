"""MySQL 数据源仓库：从 MySQL 数据库按四种类型各取最新十条，合并为十条组合结果。依赖：pymysql。"""
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

# 四种查询类型：(短标签, PROCESS_UNIT, PRODUCT, NAME)
# 短标签用于生成紧凑的二维码 key
_QR_TYPES = [
    ("bx", "二套ARGG", "YPA2干气", "丙烯"),
    ("pr", "二套ARGG", "YPA2稳定汽油", "蒸气压"),
    ("tp", "二套ARGG", "YPA2稳定汽油", "终馏点"),
    ("c5", "二套ARGG", "YPA2稳定液态烃", "碳五及以上"),
]

# 字段名缩写映射
_KEY_ABBR = {
    "formatted_entry": "entry",
    "searchtime": "time",
}

_SELECT_COLUMNS = "FORMATTED_ENTRY, SEARCHTIME"


def fetch_qr_records(host: str, port: int, user: str, password: str,
                     database: str, table: str = "data_view") -> List[Dict[str, Any]]:
    """按四种类型各查询最新 10 条记录，按位置合并为 10 条组合结果。

    返回: [{"bingxi_name": ..., "bingxi_formatted_entry": ..., "bingxi_searchtime": ...,
            "pressure_name": ..., ...}, ...]  共 10 条
    """
    try:
        import pymysql
    except ImportError as e:
        raise RuntimeError("未安装 pymysql，请先 `pip install pymysql`") from e
    if not host or not user or not database:
        raise ValueError("MySQL 连接信息不完整")

    conn = pymysql.connect(
        host=host, port=port, user=user, password=password,
        database=database, charset='utf8mb4',
    )
    try:
        all_results = []  # [(tag, [row_dict, ...]), ...]

        for tag, process_unit, product, name in _QR_TYPES:
            sql = (
                f"SELECT {_SELECT_COLUMNS} FROM {table} "
                "WHERE PROCESS_UNIT=%s AND PRODUCT=%s AND NAME=%s "
                "ORDER BY SEARCHTIME DESC LIMIT 10"
            )
            with conn.cursor() as cursor:
                cursor.execute(sql, (process_unit, product, name))
                rows = cursor.fetchall()
                columns = [col[0].lower() for col in cursor.description] if cursor.description else []
                records = [dict(zip(columns, row)) for row in rows]
                all_results.append((tag, records))
                logger.info("[qr mysql] - %s 查询到 %d 条记录", tag, len(records))

        # 按位置合并：第 i 条结果 = 四种类型各自第 i 条记录的字段（带 tag 前缀）
        # 以四种类型中最多条数为上限，空记录跳过
        max_count = max((len(records) for _, records in all_results), default=0)
        combined = []
        for i in range(max_count):
            record = {}
            for tag, records in all_results:
                if i < len(records):
                    for key, val in records[i].items():
                        abbr = _KEY_ABBR.get(key, key)
                        record[f"{tag}_{abbr}"] = val
            if record:
                combined.append(record)

        logger.info("[qr mysql] - 合并完成，共 %d 条组合结果", len(combined))
        return combined
    finally:
        conn.close()
