# 单元测试说明书：配置层 (config)

## 对应模块
`02_config.md`

## 目标测试文件
```
tests/
    test_config/
        __init__.py
        test_settings.py        # AppConfig, PathsConfig, RetrievalConfig, ...
        test_llm_config.py      # LLMConfig, EmbeddingConfig
        conftest.py             # 环境变量 fixture（清空和设置测试用环境变量）
```

## 运行方式
```bash
pytest tests/test_config/ -v
```

## 测试依赖
- 不依赖任何其他模块
- 不需要真实 API Key
- 不需要真实文件路径

## 测试用例清单

### conftest.py

```python
# 文件: tests/test_config/conftest.py

@pytest.fixture
def clean_env():
    """清空 CRAG_ 前缀的环境变量，测试后恢复"""

@pytest.fixture
def temp_dir(tmp_path):
    """返回临时目录模拟项目根"""
```

### test_settings.py

```python
# 文件: tests/test_config/test_settings.py

def test_app_config_defaults():
    """AppConfig 所有字段都有合理的默认值，不报错"""

def test_paths_config_default_paths():
    """
    验证默认路径:
    - upload_dir == "data/uploads"
    - index_dir == "data/indexes"
    - artifact_dir == "data/artifacts"
    """

def test_retrieval_config_defaults():
    """检索配置默认 top_k=10, min_score_threshold=0.3"""

def test_sandbox_config_allowed_packages():
    """allowed_packages 包含 pandas/numpy/matplotlib"""

def test_sandbox_config_restricted_modules():
    """restricted_modules 包含 os/subprocess/sys/socket/requests"""

def test_sandbox_config_default_timeout():
    """timeout_seconds 默认 60"""

def test_web_search_config_default_disabled():
    """web_search.enabled 默认 False"""

def test_self_correction_config_max_retries():
    """self_correction.max_retries 默认 3"""

def test_from_env_overrides_defaults(clean_env, monkeypatch):
    """
    设置 CRAG_API_KEY=test_key 后，
    load_config() 返回的 AppConfig 能正确读取。
    （需要实现 load_config 后补充具体断言）
    """

def test_config_serialization():
    """AppConfig 可被 json.dumps 序列化"""
```

### test_llm_config.py

```python
# 文件: tests/test_config/test_llm_config.py

def test_llm_config_default_temperature():
    """temperature 默认 0.1"""

def test_llm_config_max_tokens_default():
    """max_tokens 默认 4096"""

def test_llm_config_provider_enum():
    """LLMProvider 包含 OPENAI/OLLAMA/AZURE/OPENSOURCE"""

def test_embedding_config_default_model():
    """embedding 模型默认 BAAI/bge-small-zh-v1.5"""

def test_embedding_config_device_default():
    """device 默认 cpu"""

def test_load_llm_config_no_env():
    """没有环境变量时也能返回默认配置"""
```