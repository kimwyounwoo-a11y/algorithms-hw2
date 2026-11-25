import unittest

from src.hash_table import HashTable
from src.linear_probing_table import LinearProbingTable


class HashTableTests(unittest.TestCase):
    def setUp(self):
        self.table = HashTable()

    def test_empty_table_rejects_missing_get_and_delete(self):
        self.assertFalse(self.table.contains("missing"))
        with self.assertRaises(KeyError):
            self.table.get("missing")
        with self.assertRaises(KeyError):
            self.table.delete("missing")

    def test_shared_interface_supports_find_length_membership_and_load_factor(self):
        self.assertEqual(len(self.table), 0)
        self.assertEqual(self.table.load_factor, 0)
        self.table.put("key", "value")

        self.assertEqual(self.table.find("key"), "value")
        self.assertEqual(self.table.get("key"), "value")
        self.assertEqual(len(self.table), 1)
        self.assertIn("key", self.table)
        self.assertNotIn("missing", self.table)
        self.assertEqual(self.table.load_factor, 1 / self.table.capacity)

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


class LinearProbingTableTests(HashTableTests):
    def setUp(self):
        self.table = LinearProbingTable()

    def test_none_max_load_disables_resizing_and_counts_probes(self):
        table = LinearProbingTable(capacity=8, max_load=None)
        for key in ("a", "i", "q"):
            table.put(key, key)

        self.assertEqual(table.capacity, 8)
        self.assertEqual(len(table), 3)
        self.assertEqual(table.probe_count("q"), 3)
        self.assertEqual(table.probe_count("i"), 2)
        self.assertEqual(table.probe_count("a"), 1)
        self.assertEqual(table.probe_count("y"), 4)

    def test_probe_wraps_from_last_slot_to_first_slot(self):
        table = LinearProbingTable(capacity=4, max_load=None)
        table.put("c", "last")
        table.put("g", "wrapped")
        table.put("k", "next")

        self.assertEqual(table.find("c"), "last")
        self.assertEqual(table.find("g"), "wrapped")
        self.assertEqual(table.find("k"), "next")
        self.assertEqual(table.probe_count("c"), 1)
        self.assertEqual(table.probe_count("g"), 2)
        self.assertEqual(table.probe_count("k"), 3)

    def test_full_table_raises_on_new_key_and_reuses_deleted_slot(self):
        table = LinearProbingTable(capacity=3, max_load=None)
        table.put("a", 1)
        table.put("b", 2)
        table.put("c", 3)

        self.assertEqual(table.load_factor, 1.0)
        self.assertEqual(len(table), 3)
        self.assertIn("b", table)
        self.assertEqual(table.find("c"), 3)
        with self.assertRaises(OverflowError):
            table.put("d", 4)

        table.delete("b")
        self.assertNotIn("b", table)
        table.put("d", 4)
        self.assertEqual(table.get("a"), 1)
        self.assertEqual(table.get("c"), 3)
        self.assertEqual(table.get("d"), 4)
        self.assertEqual(table.load_factor, 1.0)

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
