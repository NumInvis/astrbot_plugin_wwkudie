"""
自定义异常
"""


class WwkudieError(Exception):
    """尽孝插件基础异常"""
    pass


class ValidationError(WwkudieError):
    """输入验证错误"""
    pass


class CooldownError(WwkudieError):
    """冷却限制错误"""
    
    def __init__(self, message: str, remaining_seconds: int = 0):
        super().__init__(message)
        self.remaining_seconds = remaining_seconds


class RateLimitError(WwkudieError):
    """限流错误"""
    
    def __init__(self, message: str, wait_time: int = 0):
        super().__init__(message)
        self.wait_time = wait_time


class LLMError(WwkudieError):
    """LLM 调用错误"""
    pass


class ConfigError(WwkudieError):
    """配置错误"""
    pass
