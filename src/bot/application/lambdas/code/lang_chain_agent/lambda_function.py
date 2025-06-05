import os
import boto3
import logging


def get_logger(level):
    root = logging.getLogger()
    if root.handlers:
        for handler in root.handlers:
            root.removeHandler(handler)
    logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=level)
    return root


log = get_logger(logging.INFO)


def lambda_handler(events, context):
    log.info("Hello")
