import json
import logging
import urllib.parse

logger = logging.getLogger()
logger.setLevel(logging.INFO)

ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".pdf", ".txt", ".log", ".docx"}

def handler(event, context):
    processed = []
    for record in event.get("Records", []):
        bucket = record["s3"]["bucket"]["name"]
        key = urllib.parse.unquote_plus(record["s3"]["object"]["key"])
        size = record["s3"]["object"].get("size", 0)
        ext = "." + key.rsplit(".", 1)[-1].lower() if "." in key else ""
        is_valid = ext in ALLOWED_EXTENSIONS and size <= 10 * 1024 * 1024

        result = {
            "bucket": bucket,
            "key": key,
            "size_bytes": size,
            "valid_attachment": is_valid
        }
        logger.info(f"Processed TicketDesk attachment: {json.dumps(result)}")
        processed.append(result)

    return {"statusCode": 200, "body": json.dumps({"processed": processed})}
