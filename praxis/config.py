"""Configuration management for PRAXIS using Pydantic Settings."""

from __future__ import annotations

import os
from enum import Enum
from pathlib import Path
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMProvider(str, Enum):
    """Supported LLM providers."""

    ANTHROPIC = "anthropic"
    MOCK = "mock"


class ExecutionMode(str, Enum):
    """Execution modes for the generator."""

    REALTIME = "realtime"  # Direct API calls
    BATCH = "batch"  # Batch API for 50% discount


class PraxisConfig(BaseSettings):
    """Main configuration for PRAXIS task generation."""

    model_config = SettingsConfigDict(
        env_prefix="PRAXIS_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # LLM Configuration
    llm_provider: LLMProvider = Field(
        default=LLMProvider.MOCK,
        description="LLM provider to use",
    )
    llm_model: str = Field(
        default="claude-sonnet-4-20250514",
        description="Model identifier",
    )
    anthropic_api_key: str | None = Field(
        default=None,
        description="Anthropic API key",
    )
    execution_mode: ExecutionMode = Field(
        default=ExecutionMode.REALTIME,
        description="Execution mode (realtime or batch for 50% discount)",
    )

    # Generation Parameters
    max_tokens: int = Field(default=4096, ge=100, le=16384)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    top_p: float = Field(default=0.95, ge=0.0, le=1.0)

    # Batch Configuration
    batch_size: int = Field(
        default=100,
        ge=1,
        le=10000,
        description="Number of requests per batch file",
    )
    batch_poll_interval: int = Field(
        default=60,
        ge=10,
        description="Seconds between batch status checks",
    )

    # Parallelization
    ray_num_cpus: int | None = Field(
        default=None,
        description="Number of CPUs for Ray (None = auto-detect)",
    )
    ray_object_store_memory: int | None = Field(
        default=None,
        description="Ray object store memory in bytes",
    )
    workers_per_cpu: int = Field(
        default=2,
        ge=1,
        le=10,
        description="Number of worker tasks per CPU",
    )

    # Storage and Caching
    cache_dir: Path = Field(
        default=Path(".praxis_cache"),
        description="Directory for LLM response cache",
    )
    checkpoint_dir: Path = Field(
        default=Path(".praxis_checkpoints"),
        description="Directory for crash recovery checkpoints",
    )
    output_dir: Path = Field(
        default=Path("output"),
        description="Directory for generated tasks",
    )
    cache_ttl_days: int = Field(
        default=365,
        ge=1,
        description="Cache time-to-live in days",
    )

    # Generation Limits
    max_tasks_per_session: int = Field(
        default=100000,
        ge=1,
        description="Maximum tasks to generate in one session",
    )
    self_consistency_samples: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Number of samples for self-consistency check",
    )
    confidence_threshold: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Minimum confidence score to accept a task",
    )

    # Retry Configuration (tenacity)
    retry_max_attempts: int = Field(default=5, ge=1, le=20)
    retry_min_wait: float = Field(default=1.0, ge=0.1)
    retry_max_wait: float = Field(default=60.0, ge=1.0)
    retry_exponential_base: float = Field(default=2.0, ge=1.1, le=5.0)

    # Diversity and Clustering
    embedding_model: str = Field(
        default="all-MiniLM-L6-v2",
        description="Sentence transformer model for embeddings",
    )
    min_cluster_distance: float = Field(
        default=0.3,
        ge=0.0,
        le=1.0,
        description="Minimum cosine distance between task clusters",
    )
    diversity_check_interval: int = Field(
        default=1000,
        ge=100,
        description="Run diversity analysis every N tasks",
    )

    # Logging
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(
        default="INFO",
    )
    structured_logging: bool = Field(
        default=True,
        description="Use structured JSON logging",
    )

    @field_validator("cache_dir", "checkpoint_dir", "output_dir", mode="before")
    @classmethod
    def ensure_path(cls, v: str | Path) -> Path:
        """Ensure value is a Path object."""
        return Path(v) if isinstance(v, str) else v

    @field_validator("anthropic_api_key", mode="before")
    @classmethod
    def get_api_key(cls, v: str | None) -> str | None:
        """Get API key from environment if not provided."""
        if v is None:
            return os.environ.get("ANTHROPIC_API_KEY")
        return v

    def ensure_dirs(self) -> None:
        """Create necessary directories."""
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.output_dir.mkdir(parents=True, exist_ok=True)


class DataSourceConfig(BaseSettings):
    """Configuration for external data sources."""

    model_config = SettingsConfigDict(
        env_prefix="PRAXIS_DATA_",
        extra="ignore",
    )

    # HuggingFace datasets for diversity
    use_onet_occupations: bool = Field(
        default=True,
        description="Use O*NET occupations dataset for personas",
    )
    use_verbnet: bool = Field(
        default=True,
        description="Use VerbNet for comprehensive verb coverage",
    )
    use_framenet: bool = Field(
        default=True,
        description="Use FrameNet for semantic frames",
    )
    use_wordnet: bool = Field(
        default=True,
        description="Use WordNet for noun hierarchies",
    )

    # Domain coverage weights
    industrial_weight: float = Field(default=0.2, ge=0.0, le=1.0)
    municipality_weight: float = Field(default=0.15, ge=0.0, le=1.0)
    maintenance_weight: float = Field(default=0.15, ge=0.0, le=1.0)
    healthcare_weight: float = Field(default=0.15, ge=0.0, le=1.0)
    domestic_weight: float = Field(default=0.2, ge=0.0, le=1.0)
    office_weight: float = Field(default=0.15, ge=0.0, le=1.0)

    # Caching for datasets
    datasets_cache_dir: Path = Field(
        default=Path(".datasets_cache"),
        description="Cache directory for HuggingFace datasets",
    )


# Global config instance (can be overridden)
_config: PraxisConfig | None = None
_data_config: DataSourceConfig | None = None


def get_config() -> PraxisConfig:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = PraxisConfig()
    return _config


def get_data_config() -> DataSourceConfig:
    """Get the data source configuration instance."""
    global _data_config
    if _data_config is None:
        _data_config = DataSourceConfig()
    return _data_config


def set_config(config: PraxisConfig) -> None:
    """Set the global configuration instance."""
    global _config
    _config = config


def set_data_config(config: DataSourceConfig) -> None:
    """Set the data source configuration instance."""
    global _data_config
    _data_config = config
