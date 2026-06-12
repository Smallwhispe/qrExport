from dataclasses import dataclass
from typing import Optional, Any
from enum import Enum, unique

@dataclass
class ResultEntity:
    def __init__(self, success: bool, code: str, message: str, data: Optional[Any] = None):
        self.success = success
        self.code = code
        self.message = message
        self.data = data

    """统一响应结果实体"""
    code: str
    message: str
    data: Optional[Any] = None
    success: bool = False

@unique
class ErrorCode(Enum):
    """错误码枚举"""
    SUCCESS = ("000000", "成功")
    FAILURE = ("999999", "失败")
    VALID_FAILURE = ("000005", "参数验证失败")
    NO_PARAM = ("000006", "无参数")
    SERVICE_FAILURE = ("000007", "服务调用失败")

    def __init__(self, code: str, msg: str):
        self._code = code
        self._msg = msg

    def get_code(self) -> str:
        return self._code

    def get_msg(self) -> str:
        return self._msg

class ResultEntityMethod:
    """结果构建工具类"""
    @staticmethod
    def buildSuccessResult(code: str = "000000", message: str = "成功", data: Any = None) -> ResultEntity:
        return ResultEntity(success=True, code=code, message=message, data=data)

    @staticmethod
    def buildFailedResult(code: str = "999999", message: str = "失败", data: Any = None) -> ResultEntity:
        return ResultEntity(success=False, code=code, message=message, data=data)
