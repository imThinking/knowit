"""配置管理模块"""

import os
from pathlib import Path
from typing import Optional


class Config:
    """KnowIt 配置"""

    def __init__(self):
        # 目录路径
        self.home_dir = Path(os.getenv("KNOWIT_HOME", "~/KnowIt")).expanduser()
        self.data_dir = self.home_dir / "data"
        self.config_dir = self.home_dir / "config"
        self.logs_dir = self.home_dir / "logs"

        # 数据库路径
        self.db_path = self.data_dir / "vault.db"

        # Meilisearch 配置
        self.meilisearch_url = os.getenv(
            "KNOWIT_MEILISEARCH_URL", "http://localhost:7700"
        )

        # 相似度阈值
        self.similarity_threshold = 0.75

        # 初始化目录
        self._init_dirs()

    def _init_dirs(self):
        """初始化必要的目录"""
        self.home_dir.mkdir(parents=True, exist_ok=True)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)


# 全局配置实例
config = Config()
