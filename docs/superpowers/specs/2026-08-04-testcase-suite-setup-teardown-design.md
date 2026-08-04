# Testcase Suite 级 Setup 和 Teardown 设计

## 目标

基于测试用例类的继承关系，为中间父类提供 suite 级生命周期钩子。
Runner 按用例执行顺序，在首次进入 suite 时执行 setup，在离开 suite
时执行 teardown。

假设用例继承关系如下：

```text
TestCase
└── TC
    └── TC_HGDB
        └── TC_HGDB_ACCESS
            ├── TC_HGDB_ACCESS_LEVEL
            │   ├── TC_HGDB_ACCESS_LEVEL_003
            │   └── TC_HGDB_ACCESS_LEVEL_ALTERTABLE_001
            └── TC_HGDB_ACCESS_RL
                └── TC_HGDB_ACCESS_RL_ROWLEVEL_002
```

执行顺序为：

```text
TC.setup
TC_HGDB.setup
TC_HGDB_ACCESS.setup
TC_HGDB_ACCESS_LEVEL.setup
TC_HGDB_ACCESS_LEVEL_003
TC_HGDB_ACCESS_LEVEL_ALTERTABLE_001
TC_HGDB_ACCESS_LEVEL.teardown
TC_HGDB_ACCESS_RL.setup
TC_HGDB_ACCESS_RL_ROWLEVEL_002
TC_HGDB_ACCESS_RL.teardown
TC_HGDB_ACCESS.teardown
TC_HGDB.teardown
TC.teardown
```

## API

suite 钩子由中间父类声明为类方法：

```python
from typing import ClassVar

from xbot.framework.testbed import TestBed


class TC_HGDB_ACCESS(TestCase):

    conn: ClassVar[object | None] = None

    @classmethod
    def setup(cls, testbed: TestBed) -> None:
        """
        Initialize suite resources.

        :param testbed: TestBed instance.
        :return: None.
        """
        cls.conn = testbed.get_conn('admin')

    @classmethod
    def teardown(cls, testbed: TestBed) -> None:
        """
        Release suite resources.

        :param testbed: TestBed instance.
        :return: None.
        """
        if cls.conn is not None:
            cls.conn.close()
            cls.conn = None
```

Runner 仅把类自身通过 `@classmethod` 声明的 `setup` 和 `teardown`
作为该层 suite 的钩子。继承来的钩子不会在子层重复执行，普通实例方法
仍供叶子用例继承和调用。

suite 的共享常量和资源使用 `ClassVar`。可变资源在 setup 中初始化，
不直接使用可变类属性默认值。普通公共方法继续定义为实例方法，以便访问
`self.testbed` 和实例日志方法。

叶子用例保留现有实例方法 API：

```python
def setup(self) -> None:
    pass

def teardown(self) -> None:
    pass
```

## Suite 识别

Runner 从叶子用例类的 MRO 中提取叶子类与框架 `TestCase` 之间的
中间父类，按从外到内排列。没有自行声明 suite 钩子的中间父类不产生
执行阶段，但其普通方法和属性仍可被叶子用例继承。

框架 `TestCase` 和叶子用例类本身不属于 suite 链。导入失败时没有可用
的叶子类，继续使用现有 `ErrorTestCase`，不推断 suite。

同一 suite 在连续用例之间保持打开。若 testset 将同一 suite 的用例
分散到不连续的位置，则每次重新进入都重新执行一轮 setup 和 teardown。

## Runner 执行流程

Runner 保留 `TestSet.paths` 的现有顺序，分两个轻量阶段执行：

1. 按顺序导入并实例化叶子用例，计算每个用例的 suite 链。
2. 标记至少包含一个未被标签过滤用例的 suite。
3. 按原顺序遍历用例，对比当前 suite 链和目标 suite 链。
4. 从内向外 teardown 已离开的 suite。
5. 从外向内 setup 新进入的 suite。
6. 执行叶子用例现有的 `TestCase.run()`。
7. 全部用例结束后，从内向外 teardown 剩余 suite。

目标 suite 链仅保留已标记的 suite。因此，一个 suite 下的用例全部
被标签过滤时，不执行该 suite 的 setup 和 teardown；用例本身仍按现有
流程生成 `SKIP` HTML 日志。若只有部分用例被过滤，suite 生命周期仍
覆盖该组用例。

Runner 只维护当前 suite 链和失败状态，不构建独立 suite 树，也不修改
testset 格式或目录发现规则。

## 异常处理

suite setup 抛出异常时：

1. 记录完整异常。
2. 标记当前 suite 失败，不再进入其子 suite。
3. 其后代用例不执行 setup、steps 或 teardown，而是复用 testcase
   日志流程生成 `SKIP` HTML，原因注明失败的 suite。
4. 离开当前 suite 时仍尝试执行其 teardown，以清理部分初始化资源。
5. 已成功进入的父 suite 保持有效，后续兄弟 suite 继续执行。

suite teardown 抛出异常时，记录完整异常并继续关闭其他 suite，避免
阻断父级资源清理。suite 钩子错误不新增独立 HTML 报告，也不修改已经
完成的叶子用例结果。

为复用现有计时、线程和 HTML 生成逻辑，`TestCase.run()` 接受一个可选
的外部跳过原因。现有无参数调用保持兼容。

## 修改范围

- `xbot/framework/runner.py`
  - 解析 suite 链。
  - 切换 suite 生命周期。
  - 隔离 suite 钩子错误。
- `xbot/framework/testcase.py`
  - 支持带原因的外部跳过。
- `tests/test_runner.py`
  - 验证 suite 执行顺序和失败行为。
- `README.md`
  - 增加英文 API 和示例。
- `README.zh.md`
  - 增加中文 API 和示例。

不增加新依赖，不增加 suite 配置、suite 结果模型或独立 suite 日志。

## 验证

测试至少覆盖：

1. 多层 suite 按从外到内 setup、从内到外 teardown。
2. 同级 suite 切换时只关闭和打开变化的继承链。
3. suite 自身未声明钩子时不会重复调用父级钩子。
4. suite setup 失败后，其后代生成带原因的 `SKIP` 日志，兄弟 suite
   继续执行。
5. suite teardown 失败不阻断其他 teardown。
6. suite 下全部用例被标签过滤时，不执行 suite 钩子。
7. 现有 testcase setup、steps、teardown、导入错误和标签过滤行为不变。

最终运行框架现有完整测试集，并检查修改文件格式。
