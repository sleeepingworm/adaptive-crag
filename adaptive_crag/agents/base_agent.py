"""
基础 Agent 类。封装共享的 LLM 调用逻辑。
支持 OpenAI-compatible API 和 Ollama 两种适配。
"""

import json
from abc import ABC, abstractmethod
from adaptive_crag.config.llm_config import LLMConfig, LLMProvider


class BaseAgent(ABC):
    """
    所有 Agent 的基类。封装共享的 LLM 调用逻辑。

    调用模式:
    1. build_system_prompt()
    2. build_input(state)       ← 新增：dict → 类型化输入
    3. build_user_prompt(input) ← 改为接收类型化输入
    4. call_llm(prompt)
    5. parse_response(response) → 类型化输出
    6. update_state(result, state)
    """

    def __init__(self, llm_config: LLMConfig):
        self.llm_config = llm_config
        self.model_name = llm_config.model_name

    # ---- 子类必须实现 ----

    @abstractmethod
    def build_system_prompt(self) -> str:
        """构建 system prompt"""

    @abstractmethod
    def build_input(self, state: dict):
        """将裸 dict state 转换为类型化的输入对象"""

    @abstractmethod
    def build_user_prompt(self, agent_input) -> str:
        """从类型化输入构建 user prompt"""

    @abstractmethod
    def parse_response(self, response: str):
        """解析 LLM 响应为类型化输出"""

    @abstractmethod
    def update_state(self, result, state: dict) -> dict:
        """将类型化结果映射为 GraphState 的增量更新"""

    def call_llm(self, system: str, user: str) -> str:
        """
        调用 LLM。

        支持:
        - OpenAI-compatible API
        - Ollama
        """
        provider = self.llm_config.provider
        model = self.model_name
        print(f"[LOG] [Agent] {self.__class__.__name__}.call_llm 入口 — provider={provider}, model={model}")

        try:
            if provider in (LLMProvider.OPENAI, LLMProvider.OPENSOURCE, LLMProvider.AZURE):
                response = self._call_openai(system, user)
            elif provider == LLMProvider.OLLAMA:
                response = self._call_ollama(system, user)
            else:
                response = self._call_openai(system, user)
            print(f"[LOG] [Agent] {self.__class__.__name__}.call_llm 出口 — 响应长度={len(response)} 字符")
            return response
        except Exception as e:
            print(f"[LOG] [Agent] {self.__class__.__name__}.call_llm 首次失败: {str(e)}，重试中...")
            # 重试一次
            try:
                if provider in (LLMProvider.OPENAI, LLMProvider.OPENSOURCE, LLMProvider.AZURE):
                    response = self._call_openai(system, user)
                else:
                    response = self._call_ollama(system, user)
                print(f"[LOG] [Agent] {self.__class__.__name__}.call_llm 重试成功 — 响应长度={len(response)} 字符")
                return response
            except Exception as e2:
                print(f"[LOG] [Agent] {self.__class__.__name__}.call_llm 重试也失败: {str(e2)}")
                return ""

    def _call_openai(self, system: str, user: str) -> str:
        """调用 OpenAI-compatible API"""
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("需要安装 openai: pip install openai")

        client = OpenAI(
            api_key=self.llm_config.api_key or "sk-placeholder",
            base_url=self.llm_config.api_base,
        )

        response = client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=self.llm_config.temperature,
            max_tokens=self.llm_config.max_tokens,
            timeout=self.llm_config.timeout_seconds,
        )

        return response.choices[0].message.content or ""

    def _call_ollama(self, system: str, user: str) -> str:
        """调用 Ollama API"""
        import requests

        api_base = self.llm_config.api_base or "http://localhost:11434"
        response = requests.post(
            f"{api_base}/api/chat",
            json={
                "model": self.model_name,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "options": {
                    "temperature": self.llm_config.temperature,
                    "num_predict": self.llm_config.max_tokens,
                },
            },
            timeout=self.llm_config.timeout_seconds,
        )
        response.raise_for_status()
        return response.json().get("message", {}).get("content", "")

    @abstractmethod
    def parse_response(self, response: str) -> dict:
        """解析 LLM 响应为结构化 dict"""

    @abstractmethod
    def update_state(self, result: dict, state: dict) -> dict:
        """将解析结果映射为 GraphState 的增量更新"""

    def run(self, state: dict) -> dict:
        """
        完整执行流程:
        1. system = self.build_system_prompt()
        2. agent_input = self.build_input(state)      ← dict → 类型化
        3. user = self.build_user_prompt(agent_input) ← 类型化 → prompt
        4. response = self.call_llm(system, user)
        5. result = self.parse_response(response)      ← 类型化输出
        6. return self.update_state(result, state)
        """
        print(f"[LOG] [Agent] {self.__class__.__name__}.run() 入口")
        system = self.build_system_prompt()
        agent_input = self.build_input(state)
        user = self.build_user_prompt(agent_input)
        response = self.call_llm(system, user)

        if not response:
            print(f"[LOG] [Agent] {self.__class__.__name__}.run() — LLM 无响应，进入降级")
            return self._fallback(state)

        result = self.parse_response(response)
        updated = self.update_state(result, state)
        print(f"[LOG] [Agent] {self.__class__.__name__}.run() 出口")
        return updated

    def _fallback(self, state: dict) -> dict:
        """LLM 无响应时的降级策略，子类可重写"""
        return {"errors": [f"{self.__class__.__name__}: LLM 无响应"]}

    def _extract_json(self, text: str) -> dict | None:
        """从 LLM 响应中提取 JSON（可能被 markdown 包裹）"""
        import re

        # 尝试直接解析
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # 尝试从 ```json ... ``` 中提取
        json_match = re.search(r"```(?:json)?\n?([\s\S]*?)\n?```", text)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        # 尝试从 { 到 } 提取
        brace_match = re.search(r"\{[\s\S]*\}", text)
        if brace_match:
            try:
                return json.loads(brace_match.group(0))
            except json.JSONDecodeError:
                pass

        return None
