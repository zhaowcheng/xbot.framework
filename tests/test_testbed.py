import os
import unittest

from unittest.mock import patch, mock_open

from xbot.framework.testbed import TestBed

class TestTestBed(unittest.TestCase):
    """
    测试床单元测试。
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
        测试 name 属性。
        """
        name = os.path.basename(self.filepath).rsplit('.', 1)[0]
        self.assertEqual(self.testbed.name, name)
        
    def test_content(self):
        """
        测试 content 属性。
        """
        self.assertEqual(self.testbed.content, self.content)

    def test_get_existing_key(self):
        """
        获取存在的 key。
        """
        value = self.testbed.get("a.b1")
        self.assertEqual(value, "c")

    def test_get_existing_index(self):
        """
        获取存在的索引。
        """
        value = self.testbed.get("a.b2[0]")
        self.assertEqual(value, 1)

    def test_get_nonexistent_key(self):
        """
        获取不存在的 key。
        """
        value = self.testbed.get("a.b4")
        self.assertIsNone(value)

    def test_get_nonexistent_index(self):
        """
        获取不存在的索引。
        """
        value = self.testbed.get("a.b2[3]")
        self.assertIsNone(value)

    def test_get_nested_key(self):
        """
        获取嵌套 key。
        """
        value = self.testbed.get("a.b3[0].x")
        self.assertEqual(value, 1)

    def test_get_nested_key_nonexistent(self):
        """
        获取嵌套 key 不存在。
        """
        value = self.testbed.get("a.b3[0].z")
        self.assertIsNone(value)

    def test_get_nested_key_nonexistent2(self):
        """
        获取嵌套 key 不存在。
        """
        value = self.testbed.get("a.b3[0].z.y")
        self.assertIsNone(value)

    def test_get_nested_key_filter(self):
        """
        获取嵌套 key 并过滤。
        """
        value = self.testbed.get("a.b3[?x==`1`]")
        self.assertEqual(value, [{'x': 1, 'y': 'h'}])

    def test_get_nested_key_filter_and_pipe(self):
        """
        获取嵌套 key 并过滤。
        """
        value = self.testbed.get("a.b3[?y=='i']|[0]")
        self.assertEqual(value, {'x': 2, 'y': 'i'})

    def test_get_nested_key_filter_nonexistent(self):
        """
        获取嵌套 key 并过滤。
        """
        value = self.testbed.get("a.b3[?x==`3`]")
        self.assertEqual(value, [])

    def test_get_nested_key_filter_nonexistent2(self):
        """
        获取嵌套 key 并过滤。
        """
        value = self.testbed.get("a.b3[?x==`3`].x")
        self.assertEqual(value, [])


if __name__ == '__main__':
    unittest.main(verbosity=2)
