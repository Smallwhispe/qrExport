from typing import Optional
from pydantic import BaseModel

class QrExportRes(BaseModel):
    exportSuccess: bool = False
    filePath: Optional[str] = None

class QrExportReq(BaseModel):
    # 生成控制参数（None 表示使用 .env / Config 默认值）
    filename: Optional[str] = None
    size: Optional[int] = None
    border: Optional[int] = None
    fill_color: Optional[str] = None
    back_color: Optional[str] = None

    def get(self, key: str, default=None):
        return getattr(self, key, default)
