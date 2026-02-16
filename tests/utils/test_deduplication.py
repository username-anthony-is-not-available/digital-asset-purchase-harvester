import json
import os
import tempfile
import unittest

from digital_asset_harvester.utils.deduplication import DuplicateDetector, generate_email_hash, generate_record_hash


class TestDeduplication(unittest.TestCase):
    def setUp(self):
        self.temp_file = tempfile.NamedTemporaryFile(delete=False)
        self.temp_path = self.temp_file.name
        self.temp_file.close()

    def tearDown(self):
        if os.path.exists(self.temp_path):
            os.remove(self.temp_path)

    def test_generate_record_hash(self):
        record1 = {
            "vendor": "Coinbase",
            "item_name": "BTC",
            "amount": 0.1,
            "purchase_date": "2023-01-01",
            "total_spent": 2000,
        }
        record2 = {
            "vendor": " Coinbase ",
            "item_name": "btc",
            "amount": "0.1",
            "purchase_date": "2023-01-01",
            "total_spent": 2000,
        }
        hash1 = generate_record_hash(record1)
        hash2 = generate_record_hash(record2)
        self.assertEqual(hash1, hash2)

        record3 = record1.copy()
        record3["transaction_id"] = "TX123"
        hash3 = generate_record_hash(record3)
        self.assertNotEqual(hash1, hash3)

    def test_generate_email_hash(self):
        email1 = {
            "subject": "Your Purchase",
            "sender": "no-reply@coinbase.com",
            "date": "Mon, 1 Jan 2023",
            "body": "You bought 0.1 BTC",
        }
        email2 = {
            "subject": " Your Purchase ",
            "sender": "no-reply@coinbase.com",
            "date": "Mon, 1 Jan 2023",
            "body": "You bought 0.1 BTC",
        }
        hash1 = generate_email_hash(email1)
        hash2 = generate_email_hash(email2)
        self.assertEqual(hash1, hash2)

    def test_duplicate_detector_records(self):
        detector = DuplicateDetector(persistence_path=self.temp_path)
        record = {"vendor": "A", "item_name": "B", "amount": 1, "purchase_date": "D"}

        self.assertFalse(detector.is_duplicate(record))
        self.assertTrue(detector.is_duplicate(record))

        # Test persistence
        detector2 = DuplicateDetector(persistence_path=self.temp_path)
        self.assertTrue(detector2.is_duplicate(record))

    def test_duplicate_detector_emails(self):
        detector = DuplicateDetector(persistence_path=self.temp_path)
        email_with_id = {"message_id": "<id123@mail>", "subject": "S"}
        email_no_id = {"subject": "S", "sender": "A", "date": "D", "body": "B"}

        # Test with Message-ID
        self.assertFalse(detector.is_email_duplicate(email_with_id))
        self.assertTrue(detector.is_email_duplicate(email_with_id))

        # Test without Message-ID (content hash)
        self.assertFalse(detector.is_email_duplicate(email_no_id))
        self.assertTrue(detector.is_email_duplicate(email_no_id))

        # Test persistence
        detector2 = DuplicateDetector(persistence_path=self.temp_path)
        self.assertTrue(detector2.is_email_duplicate(email_with_id))
        self.assertTrue(detector2.is_email_duplicate(email_no_id))

    def test_duplicate_detector_legacy_string(self):
        detector = DuplicateDetector(persistence_path=self.temp_path)
        self.assertFalse(detector.is_email_duplicate("legacy-id"))
        self.assertTrue(detector.is_email_duplicate("legacy-id"))

    def test_duplicate_detector_reset(self):
        detector = DuplicateDetector(persistence_path=self.temp_path)
        email = {"message_id": "id"}
        detector.is_email_duplicate(email)
        self.assertTrue(os.path.exists(self.temp_path))

        detector.reset()
        self.assertFalse(os.path.exists(self.temp_path))
        self.assertFalse(detector.is_email_duplicate(email, auto_save=False))


if __name__ == "__main__":
    unittest.main()
