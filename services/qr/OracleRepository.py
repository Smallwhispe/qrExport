"""Oracle 数据源仓库：从 Oracle 数据库按四种类型各取最新一条，合并为一条组合结果。依赖：python-oracledb。"""
import logging
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

# 四种查询类型：(短标签, PROCESS_UNIT, PRODUCT, NAME)
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


def _build_connect_kwargs(user: str, password: str, dsn: str,
                          config_dir: Optional[str] = None,
                          wallet_password: Optional[str] = None) -> Dict[str, Any]:
    kwargs = {"user": user, "password": password, "dsn": dsn}
    if config_dir:
        kwargs["config_dir"] = config_dir
    if wallet_password:
        kwargs["wallet_password"] = wallet_password
    return kwargs


def fetch_qr_records(user: str, password: str, dsn: str,
                     table: str = "data_view",
                     config_dir: Optional[str] = None,
                     wallet_password: Optional[str] = None) -> List[Dict[str, Any]]:
    """按四种类型各查询最新 1 条记录，合并为 1 条组合结果。

    返回: [{"bx_entry": ..., "bx_time": ..., "pr_entry": ..., ...}, ...]  共 1 条
    """
    try:
        import oracledb
    except ImportError as e:
        raise RuntimeError("未安装 python-oracledb，请先 `pip install oracledb`") from e
    if not user or not password or not dsn:
        raise ValueError("Oracle 连接信息不完整")

    connect_kwargs = _build_connect_kwargs(user, password, dsn, config_dir, wallet_password)
    with oracledb.connect(**connect_kwargs) as conn:
        all_results = []  # [(tag, [row_dict, ...]), ...]

        for tag, process_unit, product, name in _QR_TYPES:
            # Oracle 用 ROWNUM 取前 10 条
            sql = (
                f"SELECT * FROM ("
                f"SELECT {_SELECT_COLUMNS} FROM {table} "
                f"WHERE PROCESS_UNIT=:pu AND PRODUCT=:pd AND NAME=:nm "
                f"ORDER BY SEARCHTIME DESC"
                f") WHERE ROWNUM <= 1"
            )
            with conn.cursor() as cursor:
                cursor.execute(sql, pu=process_unit, pd=product, nm=name)
                rows = cursor.fetchall()
                columns = [col[0].lower() for col in cursor.description] if cursor.description else []
                records = [dict(zip(columns, row)) for row in rows]
                all_results.append((tag, records))
                logger.info("[qr oracle] - %s 查询到 %d 条记录", tag, len(records))

        # 按位置合并：第 i 条结果 = 四种类型各自第 i 条记录的字段（带 tag 前缀）
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

        logger.info("[qr oracle] - 合并完成，共 %d 条组合结果", len(combined))
        return combined
