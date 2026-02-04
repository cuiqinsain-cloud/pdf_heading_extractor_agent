"""
LLM客户端模块
封装对不同LLM提供商的API调用（使用 Anthropic SDK）
"""

import os
from typing import Dict, Any, Optional, List
import logging
from anthropic import Anthropic


logger = logging.getLogger(__name__)


class LLMClient:
    """LLM客户端封装类（基于 Anthropic SDK）"""

    def __init__(self, config: Dict[str, Any]):
        """
        初始化LLM客户端

        Args:
            config: 配置字典
        """
        self.config = config
        self.llm_config = config.get("llm", {})
        self.provider = self.llm_config.get("provider", "openai")
        self.model = self.llm_config.get("model", "gpt-4")
        self.base_url = self.llm_config.get("base_url")
        self.temperature = self.llm_config.get("temperature", 0.1)
        self.max_tokens = self.llm_config.get("max_tokens", 4000)
        self.timeout = self.llm_config.get("timeout", 60)
        self.max_retries = self.llm_config.get("max_retries", 3)

        # 初始化主LLM客户端
        self.client = self._init_client()

        # 初始化备用LLM客户端
        fallback_model = self.llm_config.get("fallback_model")
        self.fallback_client = None
        self.fallback_model = fallback_model

        logger.info(f"LLM客户端初始化完成: {self.provider}/{self.model}")
        if self.base_url:
            logger.info(f"使用自定义API端点: {self.base_url}")

    def _init_client(self) -> Anthropic:
        """初始化 Anthropic 客户端"""
        api_key = self._get_api_key()

        # 使用 Anthropic SDK，支持自定义 base_url
        client_kwargs = {
            "api_key": api_key,
            "timeout": self.timeout,
            "max_retries": self.max_retries,
        }

        # 如果有自定义 base_url，添加到参数中
        if self.base_url:
            client_kwargs["base_url"] = self.base_url
            logger.info(f"使用自定义API端点: {self.base_url}")

        return Anthropic(**client_kwargs)

    def _get_api_key(self) -> str:
        """获取API密钥"""
        api_key = self.llm_config.get("api_key", "")

        # 支持环境变量
        if api_key.startswith("${") and api_key.endswith("}"):
            env_var = api_key[2:-1]
            api_key = os.getenv(env_var, "")
            logger.debug(f"从环境变量 {env_var} 读取API密钥")

        if not api_key:
            raise ValueError(
                f"未设置API密钥，请设置环境变量或在配置文件中指定\n"
                f"提示: 在 .env 文件中设置 LLM_API_KEY=your_key"
            )

        return api_key

    def invoke(
        self,
        system_prompt: str,
        user_message: str,
        context: Optional[List[Dict]] = None,
    ) -> str:
        """
        调用LLM

        Args:
            system_prompt: 系统提示词
            user_message: 用户消息
            context: 对话历史上下文

        Returns:
            LLM响应文本
        """
        try:
            # 构建消息列表（Anthropic SDK 格式）
            messages = []

            # 添加历史对话
            if context:
                for msg in context:
                    if msg["role"] in ["user", "assistant"]:
                        messages.append({
                            "role": msg["role"],
                            "content": msg["content"]
                        })

            # 添加当前用户消息
            messages.append({
                "role": "user",
                "content": user_message
            })

            # 调用 Anthropic API
            logger.debug(f"调用LLM: {self.model}")
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                system=system_prompt,
                messages=messages
            )

            # 提取响应文本
            return response.content[0].text

        except Exception as e:
            logger.error(f"LLM调用失败: {e}")

            # 尝试使用备用模型
            if self.fallback_model:
                logger.info("尝试使用备用模型...")
                try:
                    response = self.client.messages.create(
                        model=self.fallback_model,
                        max_tokens=self.max_tokens,
                        temperature=self.temperature,
                        system=system_prompt,
                        messages=messages
                    )
                    return response.content[0].text
                except Exception as fallback_e:
                    logger.error(f"备用模型也失败: {fallback_e}")

            raise Exception(f"LLM调用失败: {str(e)}")

    def invoke_structured(
        self,
        system_prompt: str,
        user_message: str,
        output_schema: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        调用LLM并要求结构化输出

        Args:
            system_prompt: 系统提示词
            user_message: 用户消息
            output_schema: 输出JSON schema

        Returns:
            结构化数据（字典）
        """
        import json

        # 在系统提示词中添加输出格式要求
        structured_prompt = f"""{system_prompt}

请严格按照以下JSON格式输出结果:
{json.dumps(output_schema, indent=2, ensure_ascii=False)}

重要: 只返回JSON对象，不要包含任何其他文字说明。
"""

        response_text = self.invoke(structured_prompt, user_message)

        # 解析JSON
        try:
            # 提取JSON（可能包含markdown代码块）
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                json_text = response_text[json_start:json_end].strip()
            elif "```" in response_text:
                json_start = response_text.find("```") + 3
                json_end = response_text.find("```", json_start)
                json_text = response_text[json_start:json_end].strip()
            else:
                json_text = response_text.strip()

            return json.loads(json_text)

        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}")
            logger.error(f"原始响应: {response_text}")
            raise ValueError(f"LLM返回的不是有效的JSON格式")

    def count_tokens(self, text: str) -> int:
        """
        计算文本的token数

        Args:
            text: 文本内容

        Returns:
            token数量
        """
        try:
            # 使用 Anthropic 的 token 计数方法
            count_response = self.client.count_tokens(text)
            return count_response

        except Exception as e:
            logger.warning(f"Token计数失败: {e}，使用估算方法")
            # 简单估算: 1个token约等于4个字符
            return len(text) // 4
