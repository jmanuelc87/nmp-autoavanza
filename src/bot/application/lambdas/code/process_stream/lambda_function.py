import os
import fitz
import time
import json
import boto3

import requests

from botocore.exceptions import ClientError


mat = fitz.Matrix(3, 3)


def process_pdf(input, output):
    doc = fitz.open(input)
    # fix multiple document output
    for page in doc:
        pix = page.get_pixmap(matrix=mat)
        pix.save(output)


def lambda_handler(events, context):
    # Iterate records
    for event in events["Records"]:
        record = event["Keys"]["NewImage"]

        # search the image using the meta API and store it in s3
        if record["type"] == "image":
            blob = record[record["type"]]

            # extract the document
            if blob["mime_type"] in ["image/png", "image/jpeg", "image/jpg"]:
                pass

            # convert to image and extract the document
            # evaluate if pdf is supported.
            elif blob["mime_type"] in ["application/pdf"]:
                pdf_path = ""
                output_path = ""
                process_pdf(pdf_path, output_path)

        # send the text to the agent
        elif record["type"] == "text":
            pass
