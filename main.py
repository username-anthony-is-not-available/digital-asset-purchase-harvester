import argparse
import logging

from csv_writer import write_purchase_data_to_csv
from email_purchase_extractor import EmailPurchaseExtractor
from file_utils import ensure_directory_exists
from mbox_data_extractor import MboxDataExtractor

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def process_mbox_file(mbox_file: str, output_file: str):
    mbox_extractor = MboxDataExtractor(mbox_file)
    purchase_extractor = EmailPurchaseExtractor()

    all_emails = mbox_extractor.extract_all_emails()
    purchase_data = []

    for idx, email in enumerate(all_emails, 1):
        logger.info("Processing email %d/%d", idx, len(all_emails))
        email_content = f"Subject: {email['subject']}\n\nFrom: {email['sender']}\n\nDate: {email['date']}\n\nBody: {email['body']}"
        result = purchase_extractor.process_email(email_content)

        if result["has_purchase"]:
            purchase_info = result["purchase_info"]
            purchase_info['email_subject'] = email['subject']
            purchase_data.append(purchase_info)

    ensure_directory_exists(output_file)
    write_purchase_data_to_csv(output_file, purchase_data)
    logger.info("Purchase data written to %s", output_file)

def main():
    parser = argparse.ArgumentParser(description="Process an mbox file to extract cryptocurrency purchase information.")
    parser.add_argument("mbox_file", help="Path to the mbox file")
    parser.add_argument("--output", default="output/purchase_data.csv", help="Output CSV file path")

    args = parser.parse_args()

    try:
        process_mbox_file(args.mbox_file, args.output)
    except (FileNotFoundError, IOError) as e:
        logger.error("An error occurred: %s", e)

if __name__ == "__main__":
    main()
