from typing import Optional
from pydantic import BaseModel

class QrExportRes(BaseModel):
    exportSuccess: bool = False
    filePath: Optional[str] = None

class QrExportReq(BaseModel):
    # 生成控制参数
    filename: Optional[str] = "qr.png"
    size: Optional[int] = 4
    border: Optional[int] = 4
    fill_color: Optional[str] = "black"
    back_color: Optional[str] = "white"

    def get(self, key: str, default=None):
        return getattr(self, key, default)
