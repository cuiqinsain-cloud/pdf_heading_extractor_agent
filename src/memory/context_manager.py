"""
上下文管理模块
"""

from typing import Dict, Any, List
import logging


logger = logging.getLogger(__name__)


class ContextManager:
    """上下文管理器 - Agent的记忆系统"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化上下文管理器

        Args:
            config: 配置字典
        """
        self.config = config
        self.memory_config = config.get("memory", {})
        self.max_tokens = self.memory_config.get("max_tokens", 2000)

        # 短期记忆（当前任务）
        self.short_term_memory = {}

        # 工作记忆（中间结果）
        self.working_memory = []

        logger.info("上下文管理器初始化完成")

    def add_context(self, key: str, value: Any):
        """
        添加上下文信息

        Args:
            key: 上下文键
            value: 上下文值
        """
        self.short_term_memory[key] = value
        logger.debug(f"添加上下文: {key}")

    def get_context(self, key: str) -> Any:
        """
        获取上下文信息

        Args:
            key: 上下文键

        Returns:
            上下文值
        """
        return self.short_term_memory.get(key)

    def get_all_context(self) -> Dict[str, Any]:
        """获取所有上下文"""
        return self.short_term_memory.copy()

    def add_working_memory(self, item: Dict[str, Any]):
        """添加到工作记忆"""
        self.working_memory.append(item)

    def get_working_memory(self) -> List[Dict[str, Any]]:
        """获取工作记忆"""
        return self.working_memory.copy()

    def clear(self):
        """清空记忆"""
        self.short_term_memory.clear()
        self.working_memory.clear()
        logger.info("记忆已清空")
