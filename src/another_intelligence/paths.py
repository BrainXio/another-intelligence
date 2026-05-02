"""Centralized ~/.brainxio path constants for the Another-Intelligence package."""

from __future__ import annotations

from pathlib import Path

BRAINXIO_HOME = Path.home() / ".brainxio"

# State directory
STATE_DIR = BRAINXIO_HOME / "state"

# MCP configuration
GLOBAL_MCP_CONFIG = BRAINXIO_HOME / "mcp.json"
PROJECT_MCP_CONFIG = Path(".brainxio") / "mcp.json"

# Knowledge pipeline
DAILY_LOGS_DIR = BRAINXIO_HOME / "daily"
KNOWLEDGE_DIR = BRAINXIO_HOME / "knowledge"

# Training
TRAINING_DATASETS_DIR = BRAINXIO_HOME / "training_datasets"

# Plugin directory
PLUGINS_DIR = BRAINXIO_HOME / "plugins"
