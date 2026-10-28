import unittest
import tempfile
import os
from donkeybridge.core import DonkeyBridge

class TestDonkeyBridge(unittest.TestCase):
    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.db = DonkeyBridge(self.temp_db.name)

    def tearDown(self):
        self.db.conn.close()
        os.unlink(self.temp_db.name)

    def test_add_and_recall(self):
        db_id = self.db.add("NASAKOM", "N=Nasionalisme; A=Agama; KOM=Komunisme", "Detailed document explaining NASAKOM.", "history politics")
        self.assertEqual(db_id, 1)

        recalled = self.db.recall("NASAKOM")
        self.assertIsNotNone(recalled)
        self.assertEqual(recalled["id"], 1)
        self.assertEqual(recalled["peta"], "N=Nasionalisme; A=Agama; KOM=Komunisme")

    def test_open(self):
        db_id = self.db.add("TEST", "T=Test", "This is the full payload", "test")
        payload = self.db.open(db_id)
        self.assertEqual(payload, "This is the full payload")

    def test_index(self):
        self.db.add("A", "Map A", "Content A", "tagA")
        self.db.add("B", "Map B", "Content B", "tagB")

        index_str = self.db.index()
        self.assertIn("A — tagA | DB-1", index_str)
        self.assertIn("B — tagB | DB-2", index_str)

    def test_search(self):
        self.db.add("NASAKOM", "N=Nasionalisme; A=Agama; KOM=Komunisme", "Detailed document explaining NASAKOM.", "history politics")
        self.db.add("NASA", "National Aeronautics...", "Space stuff", "science")

        results = self.db.search("Nasionalisme")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["acronym"], "NASAKOM")

        results_tags = self.db.search("science")
        self.assertEqual(len(results_tags), 1)
        self.assertEqual(results_tags[0]["acronym"], "NASA")

    def test_forget(self):
        db_id = self.db.add("TEST", "T=Test", "Payload", "test")
        self.assertTrue(self.db.forget(db_id))
        self.assertIsNone(self.db.recall("TEST"))

        # Verify FTS5 is updated
        results = self.db.search("Payload")
        self.assertEqual(len(results), 0)

    def test_stats(self):
        self.db.add("A", "Map", "Long payload that should take more tokens than the acronym itself.", "")
        stats = self.db.stats()
        self.assertEqual(stats["total_bridges"], 1)
        self.assertGreater(stats["tokens_saved"], 0)
        self.assertGreater(stats["savings_percent"], 0)

    def test_unique_constraint(self):
        self.db.add("DUP", "Map 1", "Content 1", "")
        with self.assertRaises(ValueError):
            self.db.add("DUP", "Map 2", "Content 2", "")

if __name__ == '__main__':
    unittest.main()
