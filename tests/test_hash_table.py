import unittest

from src.hash_table import HashTable


class HashTableTests(unittest.TestCase):
    def setUp(self):
        self.table = HashTable()

    def test_empty_table_rejects_missing_get_and_delete(self):
        self.assertFalse(self.table.contains("missing"))
        with self.assertRaises(KeyError):
            self.table.get("missing")
        with self.assertRaises(KeyError):
            self.table.delete("missing")

    def test_colliding_keys_can_be_retrieved_and_deleted_independently(self):
        # "a", "i", and "q" share a bucket at the initial capacity of 8.
        for key in ("a", "i", "q"):
            self.table.put(key, key.upper())

        self.assertEqual(self.table.get("a"), "A")
        self.assertEqual(self.table.get("i"), "I")
        self.assertEqual(self.table.get("q"), "Q")

        self.table.delete("i")
        self.assertFalse(self.table.contains("i"))
        with self.assertRaises(KeyError):
            self.table.get("i")
        self.assertEqual(self.table.get("a"), "A")
        self.assertEqual(self.table.get("q"), "Q")

        self.table.delete("a")
        self.table.delete("q")
        self.assertFalse(self.table.contains("a"))
        self.assertFalse(self.table.contains("q"))

    def test_put_updates_an_existing_key_without_creating_a_duplicate(self):
        self.table.put("key", "first")
        self.table.put("key", "updated")

        self.assertTrue(self.table.contains("key"))
        self.assertEqual(self.table.get("key"), "updated")

    def test_delete_removes_a_key_and_other_keys_remain_available(self):
        self.table.put("keep", 1)
        self.table.put("remove", 2)

        self.table.delete("remove")

        self.assertFalse(self.table.contains("remove"))
        with self.assertRaises(KeyError):
            self.table.get("remove")
        self.assertEqual(self.table.get("keep"), 1)

    def test_entries_remain_available_after_resizing(self):
        entries = [(f"key-{index}", index) for index in range(32)]
        for key, value in entries:
            self.table.put(key, value)

        for key, value in entries:
            with self.subTest(key=key):
                self.assertEqual(self.table.get(key), value)

    def test_none_max_load_disables_resizing_and_counts_probes(self):
        table = HashTable(capacity=8, max_load=None)
        for key in ("a", "i", "q"):
            table.put(key, key)

        self.assertEqual(table.capacity, 8)
        self.assertEqual(len(table), 3)
        self.assertEqual(table.probe_count("q"), 1)
        self.assertEqual(table.probe_count("i"), 2)
        self.assertEqual(table.probe_count("a"), 3)
        self.assertEqual(table.probe_count("y"), 3)


if __name__ == "__main__":
    unittest.main()
