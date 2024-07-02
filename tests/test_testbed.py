import os
import unittest

from unittest.mock import patch, mock_open

from xbot.framework.testbed import TestBed

class TestTestBed(unittest.TestCase):
    """
    Unit tests for testbed module.
    """
    @classmethod
    def setUpClass(cls):
        cls.content = """
        a:
          b1: c
          b2:
            - 1
            - 2
            - 3
          b3:
            - x: 1
              y: 'h'
            - x: 2
              y: 'i'
        """
        cls.filepath = './testbed.yml'
        with patch("builtins.open", mock_open(read_data=cls.content)):
            cls.testbed = TestBed(cls.filepath)

    def test_name(self):
        """
        Test `name` property.
        """
        name = os.path.basename(self.filepath).rsplit('.', 1)[0]
        self.assertEqual(self.testbed.name, name)
        
    def test_content(self):
        """
        Test `content` property.
        """
        self.assertEqual(self.testbed.content, self.content)

    def test_get_existing_key(self):
        """
        Get an existing key.
        """
        value = self.testbed.get("a.b1")
        self.assertEqual(value, "c")

    def test_get_existing_index(self):
        """
        Get an existing index.
        """
        value = self.testbed.get("a.b2[0]")
        self.assertEqual(value, 1)

    def test_get_nonexistent_key(self):
        """
        Get a nonexistent key.
        """
        value = self.testbed.get("a.b4")
        self.assertIsNone(value)

    def test_get_nonexistent_index(self):
        """
        Get a nonexistent index.
        """
        value = self.testbed.get("a.b2[3]")
        self.assertIsNone(value)

    def test_get_nested_key(self):
        """
        Get a nested key.
        """
        value = self.testbed.get("a.b3[0].x")
        self.assertEqual(value, 1)

    def test_get_nested_key_nonexistent(self):
        """
        Get a nonexistent nested key.
        """
        value = self.testbed.get("a.b3[0].z")
        self.assertIsNone(value)

    def test_get_nested_key_nonexistent2(self):
        """
        Get a nonexistent nested key.
        """
        value = self.testbed.get("a.b3[0].z.y")
        self.assertIsNone(value)

    def test_get_nested_key_filter(self):
        """
        Get a nested key and filter.
        """
        value = self.testbed.get("a.b3[?x==`1`]")
        self.assertEqual(value, [{'x': 1, 'y': 'h'}])

    def test_get_nested_key_filter_and_pipe(self):
        """
        Get a nested key and filter and pipe.
        """
        value = self.testbed.get("a.b3[?y=='i']|[0]")
        self.assertEqual(value, {'x': 2, 'y': 'i'})

    def test_get_nested_key_filter_nonexistent(self):
        """
        Get a nested key and filter(nonexistent).
        """
        value = self.testbed.get("a.b3[?x==`3`]")
        self.assertEqual(value, [])

    def test_get_nested_key_filter_nonexistent2(self):
        """
        Get a nested key and filter(nonexistent).
        """
        value = self.testbed.get("a.b3[?x==`3`].x")
        self.assertEqual(value, [])


if __name__ == '__main__':
    unittest.main(verbosity=2)
