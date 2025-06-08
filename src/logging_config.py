import logging
import sys
import os

# Add src directory to Python path so modules can import from src
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(current_dir) if os.path.basename(current_dir) != 'src' else current_dir
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)

# Create and configure the logger
logger = logging.getLogger("mcp_app")
logger.setLevel(logging.INFO)

# Create console handler
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)

# Create simple formatter
formatter = logging.Formatter(
    '[%(asctime)s] %(levelname)-8s %(message)s',
    datefmt='%m/%d/%y %H:%M:%S'
)

handler.setFormatter(formatter)
logger.addHandler(handler)

# Prevent duplicate logs
logger.propagate = False 