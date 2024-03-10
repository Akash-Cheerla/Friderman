import os
import uvicorn
from loguru import logger

from utils import read_json


if __name__ == "__main__":
    config = read_json("config.json")

    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = config["google_creds_path"]

    log_dir_path = os.path.dirname(config["logs"]["filepath"])
    if len(log_dir_path) != 0:
        os.makedirs(log_dir_path, exist_ok=True)

    # add logger
    logger.add(
        config["logs"]["filepath"],
        level=config["logs"]["level"],
        rotation=config["logs"]["rotation"]
    )

    # starting the service
    logger.info(f"Starting the service at = {config['host']}:{config['port']}")

    uvicorn.run("main:app", host=config['host'], port=config['port'])
