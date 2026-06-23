"""
Adaptive CRAG - 系统入口点
==========================
提供命令行和 Streamlit 两种启动方式。
"""

import sys
import os


def main():
    """主入口"""
    if len(sys.argv) > 1 and sys.argv[1] == "--cli":
        _run_cli()
    else:
        _run_streamlit()


def _run_streamlit():
    """启动 Streamlit Web UI"""
    import streamlit.web.bootstrap as bootstrap

    # 找到 app/main.py 的路径
    app_path = os.path.join(os.path.dirname(__file__), "app", "main.py")

    if not os.path.exists(app_path):
        print(f"错误: 找不到 {app_path}")
        sys.exit(1)

    # 启动 Streamlit
    sys.argv = ["streamlit", "run", app_path, "--server.port", "8501"]
    bootstrap.run(app_path, "", [], [])


def _run_cli():
    """命令行模式（开发/调试用）"""
    print("Adaptive CRAG CLI Mode")
    print("=" * 40)

    from adaptive_crag.config import load_config
    config = load_config()
    print(f"配置已加载:")
    print(f"  项目根目录: {config.paths.project_root}")
    print(f"  上传目录: {config.paths.upload_dir}")
    print(f"  索引目录: {config.paths.index_dir}")
    print(f"  产物目录: {config.paths.artifact_dir}")
    print(f"  检索 Top-K: {config.retrieval.top_k}")
    print(f"  沙箱超时: {config.sandbox.timeout_seconds}s")
    print()
    print("系统就绪。使用以下命令启动 Web UI:")
    print("  python main.py")
    print("  或")
    print("  streamlit run app/main.py")


if __name__ == "__main__":
    main()
