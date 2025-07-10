import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional


class JSONFormatter(logging.Formatter):

    def format(self, record):
        log_entry = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "levelname": record.levelname,
            "module": record.module,
            "funcName": record.funcName,
            "lineno": record.lineno,
        }

        message = record.getMessage()
        try:
            parsed_message = json.loads(message)
            log_entry["message"] = json.dumps(
                parsed_message, indent=4, ensure_ascii=False
            )
        except json.JSONDecodeError:
            log_entry["message"] = message

        if record.args:
            log_entry["extra"] = record.args

        return json.dumps(log_entry, ensure_ascii=False, indent=4)


def setup_logger(
    name: str, log_file: str, log_dir: str = "struct_logs", level=logging.INFO
) -> logging.Logger:
    """
    Sets up a logger with a specified name and log file.

    Args:
        name (str): The name of the logger.
        log_file (str): The name of the log file.
        log_dir (str): Directory where logs will be stored.
        level (int): Logging level (ault: logging.INFO).

    Returns:
        logging.Logger: Configured logger instance.
    """
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, log_file)

    logger = logging.getLogger(name)
    logger.setLevel(level)

    handler = logging.FileHandler(log_path)
    handler.setFormatter(JSONFormatter())

    logger.addHandler(handler)
    return logger


def log_llm_call(
    call_type: str,
    system_prompt: str,
    messages: List[Dict[str, Any]],
    thread_id: str,
    additional_info: Optional[Dict[str, Any]] = None,
):
    """
    Log LLM call details for tracking and debugging

    Args:
        call_type: Type of LLM call (classification, post_app_modification, etc.)
        system_prompt: The system prompt used
        messages: List of messages sent to the LLM
        thread_id: Thread ID for tracking
        additional_info: Any additional information to log
    """
    try:
        log_data = {
            "event_type": "llm_call",
            "call_type": call_type,
            "thread_id": thread_id,
            "timestamp": datetime.utcnow().isoformat(),
            "system_prompt_length": len(system_prompt) if system_prompt else 0,
            "message_count": len(messages) if messages else 0,
            "additional_info": additional_info or {},
        }

        # Use the main logger
        logger = loggers.get("main")
        if logger:
            logger.info(json.dumps(log_data))
        else:
            print(
                f"📝 [LLM_CALL] {call_type} - Thread: {thread_id} | Messages: {len(messages) if messages else 0}"
            )

    except Exception as e:
        print(f"❌ [LOG] Error logging LLM call: {str(e)}")


loggers = {
    "main": setup_logger("main", "main.log"),
    "pinecone": setup_logger("pinecone_service", "pinecone_service.log"),
    "requests": setup_logger("requests", "requests.log"),
    "voyageai": setup_logger("voyageai", "voyageai.log"),
    "data_insert": setup_logger("data_insert", "data_insert.log"),
}
