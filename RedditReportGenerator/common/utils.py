import json
import logging
import os
from typing import Any, Callable, Dict, List, Literal, Optional, Tuple, Union, get_type_hints
from langchain_core.utils.function_calling import convert_to_openai_tool
from pydantic import BaseModel

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

# Dictionary to store file handlers for different user/community ids
user_handlers = {}


def get_logger(name: str, user_or_community_id: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    if not os.path.exists("logs"):
        os.makedirs("logs")

    log_file = os.path.join("logs", f"{user_or_community_id}.log")

    # Check if we already have a handler for this user/community
    if user_or_community_id not in user_handlers:
        # Create new handler
        handler = logging.FileHandler(log_file)
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        user_handlers[user_or_community_id] = handler

    # Check if this logger already has the user/community-specific handler
    has_user_handler = any(
        handler is user_handlers[user_or_community_id] for handler in logger.handlers
    )

    if not has_user_handler:
        logger.addHandler(user_handlers[user_or_community_id])

    return logger


def convert_tool(tool: Callable) -> Dict[str, Any]:
    if tool is None:
        raise ValueError("Tool cannot be None")

    schema = convert_to_openai_tool(
        tool,
    )
    return schema


def try_validate_json(base: BaseModel, data: str):
    try:
        return base.model_validate_json(data)
    except ValueError as e:
        try:
            return base(**json.loads(data))
        except Exception as json_error:
            raise ValueError("Invalid JSON data") from json_error


def load_jsonl_file(file_path: str) -> List[Dict]:
    """Load data from a JSONL file"""
    data = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    data.append(json.loads(line))
                except Exception as e:
                    logging.warning(f"Failed to parse line in {file_path}: {e}")
    return data
