# TestSet Install Tests Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 完善 `testcases.install/test` 新结构测试，并验证安装用例忽略 tags、安装失败中断后续执行。

**Architecture:** 保留现有 `unittest` 测试组织，`TestSet` 使用临时目录做单元测试，`Runner` 复用 `INIT_DIR` 做真实执行测试。只从日志文件和控制台输出验证行为，不为测试引入 Mock 执行模型。

**Tech Stack:** Python 3.10、`unittest`、标准库临时目录、现有 xbot.framework 测试夹具。

## Global Constraints

- 不兼容旧 `paths` 格式。
- 不增加测试框架、依赖或公共测试抽象。
- `install` 用例忽略测试套 tags 过滤。
- 任一 `install` 用例未通过时，后续安装和测试用例均不执行。
- Python docstring 使用三引号多行格式，参数和返回值使用 `:param`、`:return:`。
- 字符串默认使用单引号。
- 保留用户当前已暂存的无关改动。

---

### Task 1: 迁移 TestSet 单元测试

**Files:**
- Modify: `tests/test_testset.py`
- Test: `tests/test_testset.py`

**Interfaces:**
- Consumes: `TestSet(filepath: str)`、`TestSet.include_tags`、`TestSet.exclude_tags`
- Produces: 对 `TestSet.testcases.install: tuple[str, ...]` 和 `TestSet.testcases.test: tuple[str, ...]` 的回归测试

- [ ] **Step 1: 将 tags 测试数据迁移到新结构**

把 `tests/test_testset.py` 中仅为满足结构校验而存在的：

```yaml
paths:
```

统一替换为：

```yaml
testcases:
  install:
  test:
```

tags 断言保持不变。

- [ ] **Step 2: 用新分组替换旧 paths 正常路径测试**

导入返回类型：

```python
from xbot.framework.testset import TestCases, TestSet, TestSetError
```

用下面的测试替换 `test_paths`：

```python
def test_testcases(self):
    """
    Test testcase groups and directory expansion.
    """
    content = """
    tags:
      include:
      exclude:
    testcases:
      install:
        - testcases/dir1/tc_01.py
      test:
        - testcases/dir2
    """
    testset = self.mock_testset(content)
    self.assertEqual(
        testset.testcases,
        TestCases(
            install=('testcases/dir1/tc_01.py',),
            test=(
                'testcases/dir2/tc_03.py',
                'testcases/dir2/tc_04.py',
                'testcases/dir2/subdir2_1/tc_05.py',
                'testcases/dir2/subdir2_1/tc_06.py',
            ),
        ),
    )
```

增加空分组测试：

```python
def test_testcases_empty(self):
    """
    Expect empty tuples when testcase groups are empty.
    """
    content = """
    tags:
      include:
      exclude:
    testcases:
      install:
      test:
    """
    self.assertEqual(
        self.mock_testset(content).testcases,
        TestCases(install=(), test=()),
    )
```

- [ ] **Step 3: 增加新结构校验测试**

增加缺少根字段测试：

```python
def test_testcases_not_found(self):
    """
    Expect TestSetError when testcases is not found.
    """
    content = """
    tags:
      include:
      exclude:
    """
    with self.assertRaisesRegex(TestSetError, 'No `testcases`'):
        self.mock_testset(content)
```

增加缺少分组测试：

```python
def test_testcase_group_not_found(self):
    """
    Expect TestSetError when a testcase group is not found.
    """
    contents = (
        """
        tags:
          include:
          exclude:
        testcases:
          test:
        """,
        """
        tags:
          include:
          exclude:
        testcases:
          install:
        """,
    )
    for content in contents:
        with self.subTest(content=content):
            with self.assertRaises(TestSetError):
                self.mock_testset(content)
```

增加分组类型错误测试：

```python
def test_testcase_group_not_list(self):
    """
    Expect TestSetError when a non-empty testcase group is not a list.
    """
    content = """
    tags:
      include:
      exclude:
    testcases:
      install: testcases/dir1/tc_01.py
      test:
    """
    with self.assertRaisesRegex(
        TestSetError,
        '`testcases.install` is not a list',
    ):
        self.mock_testset(content)
```

把旧 `test_path_not_exist` 改为新结构，并让异常在构造时触发：

```python
def test_testcase_path_not_exist(self):
    """
    Expect TestSetError when a testcase path does not exist.
    """
    content = """
    tags:
      include:
      exclude:
    testcases:
      install:
      test:
        - testcases/dir1/tc_00.py
    """
    with self.assertRaisesRegex(TestSetError, 'does not exist'):
        self.mock_testset(content)
```

- [ ] **Step 4: 运行 TestSet 测试，确认失败原因来自旧测试未覆盖的新结构**

Run:

```text
../venv/bin/python -m unittest tests.test_testset
```

Expected: 新结构测试通过；如失败，只允许是 `TestSet` 新结构校验或展开结果与设计不符。

- [ ] **Step 5: 只做使 TestSet 测试通过的最小修正**

如果 Step 4 暴露 `TestSet` 自身缺陷，只修改 `xbot/framework/testset.py` 对应校验或展开逻辑；不增加兼容分支或新类型。

- [ ] **Step 6: 复验并提交**

Run:

```text
../venv/bin/python -m unittest tests.test_testset
git diff --check -- tests/test_testset.py xbot/framework/testset.py
```

Expected: 所有 `tests.test_testset` 测试通过，空白检查无输出。

Commit:

```text
git commit --only tests/test_testset.py xbot/framework/testset.py -m 'test: cover grouped testset cases'
```

---

### Task 2: 验证安装用例忽略 tags

**Files:**
- Modify: `tests/test_runner.py`
- Modify: `xbot/framework/testcase.py`
- Rename: `xbot/framework/statics/initdir/testcases/examples/inst/tc_eg_install_the_sofawre_to_be_tested_successful.py`
- To: `xbot/framework/statics/initdir/testcases/examples/inst/tc_eg_install_the_software_to_be_tested_successful.py`
- Test: `tests/test_runner.py`

**Interfaces:**
- Consumes: `TestCase.run(never_skip: bool = False) -> None`
- Produces: 安装用例从 `Runner` 到执行线程忽略 tags 的真实行为保证

- [ ] **Step 1: 在现有 Runner 成功路径中加入安装日志断言**

在 `test_run` 执行后加入：

```python
self.assertEqual(
    self.get_case_result_from_logfile(
        os.path.join(
            logroot,
            'testcases',
            'examples',
            'inst',
            'tc_eg_install_the_software_to_be_tested_successful.html',
        ),
    ),
    'PASS',
)
```

默认测试套包含 `tags.include: [tag1]`，而安装用例 `TAGS = []`，因此该断言能验证
安装用例确实忽略 tags。

- [ ] **Step 2: 运行测试并确认当前失败**

Run:

```text
../venv/bin/python -m unittest tests.test_runner.TestRunner.test_run
```

Expected: 先因示例文件名 `sofawre/software` 不一致而无法构造 `TestSet`；统一文件名后应因安装用例结果为 `SKIP` 而失败。

- [ ] **Step 3: 统一成功安装用例文件名**

把：

```text
xbot/framework/statics/initdir/testcases/examples/inst/tc_eg_install_the_sofawre_to_be_tested_successful.py
```

重命名为：

```text
xbot/framework/statics/initdir/testcases/examples/inst/tc_eg_install_the_software_to_be_tested_successful.py
```

类名已经使用正确的 `software` 拼写，不修改类内容。

- [ ] **Step 4: 把 never_skip 传入真实执行线程**

在 `xbot/framework/testcase.py` 中把线程创建改为：

```python
t = Thread(
    target=self.__run,
    args=(never_skip,),
    name=self.caseid,
)
```

把 tags 判断改为：

```python
if not never_skip and self.skipped:
```

不修改 `skipped` 属性，使普通测试用例继续使用原有 tags 行为。

- [ ] **Step 5: 运行成功路径与 TestCase 回归测试**

Run:

```text
../venv/bin/python -m unittest \
    tests.test_runner.TestRunner.test_run \
    tests.test_testcase
```

Expected: 安装日志为 `PASS`，既有跳过用例仍为 `SKIP`，全部通过。

- [ ] **Step 6: 检查并提交**

Run:

```text
git diff --check -- \
    tests/test_runner.py \
    xbot/framework/testcase.py \
    xbot/framework/statics/initdir/testcases/examples/inst
```

Expected: 无输出。

Commit:

```text
git commit --only \
    tests/test_runner.py \
    xbot/framework/testcase.py \
    xbot/framework/statics/initdir/testcases/examples/inst/tc_eg_install_the_sofawre_to_be_tested_successful.py \
    xbot/framework/statics/initdir/testcases/examples/inst/tc_eg_install_the_software_to_be_tested_successful.py \
    -m 'test: verify install cases ignore tags'
```

---

### Task 3: 验证安装失败中断

**Files:**
- Modify: `tests/test_runner.py`
- Modify: `xbot/framework/runner.py`
- Rename: `xbot/framework/statics/initdir/testcases/examples/inst/tc_eg_install_the_sofawre_to_be_tested_failed.py`
- To: `xbot/framework/statics/initdir/testcases/examples/inst/tc_eg_install_the_software_to_be_tested_failed.py`
- Modify: `xbot/framework/statics/initdir/testsets/testset_example.yml`
- Test: `tests/test_runner.py`

**Interfaces:**
- Consumes: `Runner.run(outfmt: str = 'brief') -> str`
- Produces: 首个非 `PASS` 安装结果终止后续安装和测试执行的行为保证

- [ ] **Step 1: 为 Runner 测试增加可复用的真实执行辅助方法**

把 `setUpClass` 中固定的 `cls.runner` 删除，保留临时工程创建。增加：

```python
def run_testset(self, filename: str) -> tuple[str, str]:
    """
    Run a testset from the copied example project.

    :param filename: Testset filename.
    :return: Log root and captured stdout.
    """
    runner = Runner(
        TestBed(
            os.path.join(
                self.workdir,
                'testbeds',
                'testbed_example.yml',
            ),
        ),
        TestSet(os.path.join(self.workdir, 'testsets', filename)),
    )
    with utils.cd(self.workdir):
        with patch('sys.stdout', new_callable=StringIO) as stdout:
            with patch('sys.stderr', new_callable=StringIO):
                logroot = runner.run()
    return logroot, stdout.getvalue()
```

现有 `test_run` 改为：

```python
logroot, _ = self.run_testset('testset_example.yml')
```

增加每个测试后的日志清理，避免秒级日志目录重名：

```python
def tearDown(self) -> None:
    """
    Remove logs created by one test.
    """
    logdir = os.path.join(self.workdir, 'logs')
    if os.path.exists(logdir):
        shutil.rmtree(logdir)
```

- [ ] **Step 2: 写入失败安装测试**

增加：

```python
def test_failed_install_interrupts_execution(self):
    """
    Stop remaining install and test cases after an install failure.
    """
    filename = 'testset_install_failed.yml'
    filepath = os.path.join(self.workdir, 'testsets', filename)
    with open(filepath, 'w', encoding='utf8') as testset_file:
        testset_file.write(
            """
tags:
  include:
    - tag1
  exclude:
testcases:
  install:
    - testcases/examples/inst/tc_eg_install_the_software_to_be_tested_failed.py
    - testcases/examples/inst/tc_eg_install_the_software_to_be_tested_successful.py
  test:
    - testcases/examples/pass/tc_eg_pass_get_values_from_testbed.py
""",
        )

    logroot, output = self.run_testset(filename)
    failed = os.path.join(
        logroot,
        'testcases',
        'examples',
        'inst',
        'tc_eg_install_the_software_to_be_tested_failed.html',
    )
    successful = os.path.join(
        logroot,
        'testcases',
        'examples',
        'inst',
        'tc_eg_install_the_software_to_be_tested_successful.html',
    )
    tested = os.path.join(
        logroot,
        'testcases',
        'examples',
        'pass',
        'tc_eg_pass_get_values_from_testbed.html',
    )

    self.assertEqual(self.get_case_result_from_logfile(failed), 'ERROR')
    self.assertFalse(os.path.exists(successful))
    self.assertFalse(os.path.exists(tested))
    self.assertIn('Execution was interrupted', output)
```

- [ ] **Step 3: 运行测试并确认失败**

Run:

```text
../venv/bin/python -m unittest \
    tests.test_runner.TestRunner.test_failed_install_interrupts_execution
```

Expected: 在失败用例文件重命名前因路径不存在而失败；重命名后，如果 `break` 正确，
测试通过，否则会因后续日志存在而失败。

- [ ] **Step 4: 统一失败安装用例文件名并保留最小 break 实现**

把：

```text
xbot/framework/statics/initdir/testcases/examples/inst/tc_eg_install_the_sofawre_to_be_tested_failed.py
```

重命名为：

```text
xbot/framework/statics/initdir/testcases/examples/inst/tc_eg_install_the_software_to_be_tested_failed.py
```

`Runner.run()` 保留以下中断条件：

```python
if insting and caseinst.result != 'PASS':
    xprint(f'Execution was interrupted because `{caseid}` failed.')
    break
```

- [ ] **Step 5: 清理示例 YAML 空白并运行完整相关测试**

删除 `xbot/framework/statics/initdir/testsets/testset_example.yml` 的行尾空格。

Run:

```text
../venv/bin/python -m unittest \
    tests.test_testset \
    tests.test_testcase \
    tests.test_runner \
    tests.test_main \
    tests.test_report
```

Expected: 全部通过。

- [ ] **Step 6: 最终检查并提交**

Run:

```text
git diff --check
```

Expected: 无输出。

Commit:

```text
git commit --only \
    tests/test_runner.py \
    xbot/framework/runner.py \
    xbot/framework/statics/initdir/testcases/examples/inst/tc_eg_install_the_sofawre_to_be_tested_failed.py \
    xbot/framework/statics/initdir/testcases/examples/inst/tc_eg_install_the_software_to_be_tested_failed.py \
    xbot/framework/statics/initdir/testsets/testset_example.yml \
    -m 'test: cover failed install interruption'
```
