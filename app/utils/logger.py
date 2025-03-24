import logging
import sys
from app.config import LOG_LEVEL

# Create logger
logger = logging.getLogger("vanna-ai-qa")
logger.setLevel(getattr(logging, LOG_LEVEL))

# Create console handler and set level
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(getattr(logging, LOG_LEVEL))

# Create formatter
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Add formatter to console handler
console_handler.setFormatter(formatter)

# Add console handler to logger
logger.addHandler(console_handler)
