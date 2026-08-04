# Testcase Suite Setup and Teardown Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 testcase 中间父类增加按继承层级执行一次的 suite setup 和 teardown。

**Architecture:** Runner 预先导入用例并从 MRO 提取 suite 链，再按相邻用例的公共前缀增量关闭和打开 suite。TestCase 仅增加可选的外部跳过原因，以复用现有线程、计时和 HTML 日志流程记录 suite setup 失败后的后代用例。

**Tech Stack:** Python 3.10、标准库 `unittest`、现有 xbot framework 日志和 HTML 模板。

## Global Constraints

- 父类 suite 钩子使用 `@classmethod setup(cls, testbed)` 和 `@classmethod teardown(cls, testbed)`。
- 只调用 suite 类自身声明的钩子，不重复调用继承来的钩子。
- 叶子用例现有实例方法 `setup(self)` 和 `teardown(self)` 保持兼容。
- suite setup 失败时跳过其后代、尝试当前 suite teardown，并继续兄弟 suite。
- suite teardown 失败不能阻断其他 suite 的清理。
- suite 下全部用例被标签过滤时，不执行该 suite 的钩子。
- 不修改 TestSet 格式、目录发现规则或现有无参数 `TestCase.run()` 调用。
- 不新增依赖、suite 配置、suite 结果模型或独立 suite HTML 日志。
- Python 字符串默认使用单引号；docstring 使用三引号多行格式，并包含 `:param` 和 `:return:`。

## File Structure

- `xbot/framework/testcase.py`：接受外部跳过原因，并复用现有 SKIP 日志流程。
- `xbot/framework/runner.py`：解析 MRO、预加载用例、切换 suite 和隔离钩子异常。
- `tests/test_testcase.py`：验证外部跳过不执行叶子阶段且生成带原因的 SKIP HTML。
- `tests/test_runner.py`：验证 suite 顺序、继承、标签过滤和异常隔离。
- `README.md`：记录英文 suite API。
- `README.zh.md`：记录中文 suite API。

---

### Task 1: TestCase 外部跳过原因

**Files:**
- Modify: `xbot/framework/testcase.py:221-255`
- Test: `tests/test_testcase.py:156-195`

**Interfaces:**
- Consumes: 现有 `TestCase.run()`、`TestCase.__run()` 和 HTML 日志流程。
- Produces: `TestCase.run(skip_reason: str | None = None) -> None`，供 Runner 在 suite setup 失败时调用。

- [ ] **Step 1: 写失败测试**

在 `tests/test_testcase.py` 的标签过滤测试之后增加：

```python
    def test_external_skip_reason(self) -> None:
        """
        Test an external skip reason.

        :return: None.
        """
        caseid = 'tc_eg_pass_get_values_from_testbed'
        caseinst = self.instcase('pass', caseid)
        caseinst.setup = MagicMock()
        caseinst.step1 = MagicMock()
        caseinst.teardown = MagicMock()
        reason = 'Suite TC_HGDB setup failed.'

        caseinst.run(reason)

        self.assertEqual(caseinst.result, 'SKIP')
        caseinst.setup.assert_not_called()
        caseinst.step1.assert_not_called()
        caseinst.teardown.assert_not_called()
        with open(caseinst.logfile, encoding='utf8') as f:
            self.assertIn(reason, f.read())
```

- [ ] **Step 2: 运行测试并确认失败**

Run:

```bash
../venv/bin/python -m unittest \
  tests.test_testcase.TestTestCase.test_external_skip_reason -v
```

Expected: `TypeError: TestCase.run() takes 1 positional argument but 2 were given`。

- [ ] **Step 3: 实现最小外部跳过支持**

将 `TestCase.run()` 和私有执行方法改为：

```python
    def run(self, skip_reason: str | None = None) -> None:
        """
        Run the current testcase.

        :param skip_reason: External reason for skipping this testcase.
        :return: None.
        """
        t = Thread(
            target=self.__run,
            args=(skip_reason,),
            name=self.caseid
        )
        t.start()
        t.join(self.TIMEOUT)
        if t.is_alive():
            utils.stop_thread(t, TestCaseTimeout)
            t.join(60)  # 等待 teardown 完成。

    def __run(self, skip_reason: str | None = None) -> None:
        """
        Run the current testcase.

        :param skip_reason: External reason for skipping this testcase.
        :return: None.
        """
        self.__starttime = datetime.now().replace(microsecond=0)
        if skip_reason or self.skipped:
            self.__loghdlr.set_stage('setup')
            self.__result = 'SKIP'
            if skip_reason:
                self.warn(f'Skipped: {skip_reason}')
            else:
                self.warn(
                    f'Skipped: self.TAGS={self.TAGS}, '
                    f'testset.tags.include={self.__testset.include_tags}, '
                    f'testset.tags.exclude={self.__testset.exclude_tags}'
                )
        else:
            self.__run_stage('setup')
            if not self.__result:
                for step in self.steps:
                    if not self.__result or (
                        self.__result == 'FAIL' and not self.FAILFAST
                    ):
                        self.__run_stage(step)
            self.__run_stage('teardown')
        self.__endtime = datetime.now().replace(microsecond=0)
        self.__duration = self.__endtime - self.__starttime
        self.__result = self.__result or 'PASS'
        self.__dump_log()
        logger.ROOT_LOGGER.removeHandler(self.__loghdlr)
```

- [ ] **Step 4: 运行 TestCase 测试**

Run:

```bash
../venv/bin/python -m unittest tests.test_testcase -v
```

Expected: 全部通过，包括原有无参数 `run()`、标签 SKIP 和超时测试。

- [ ] **Step 5: 提交**

```bash
git add xbot/framework/testcase.py tests/test_testcase.py
git commit -m 'feat: support external testcase skip reasons'
```

---

### Task 2: 从 MRO 提取 Suite 链

**Files:**
- Modify: `xbot/framework/runner.py:109-120`
- Test: `tests/test_runner.py:9-17,82`

**Interfaces:**
- Consumes: `type[TestCase].__mro__` 和类自身的 `setup`、`teardown` 描述符。
- Produces: `Runner._suite_chain(casecls: type[TestCase]) -> tuple[type[TestCase], ...]`，顺序为从外层到内层。

- [ ] **Step 1: 写失败测试**

把 `TestCase` 加入 `tests/test_runner.py` 文件顶部导入，并增加：

```python
    def test_suite_chain(self) -> None:
        """
        Test suite extraction from a testcase MRO.

        :return: None.
        """
        class BaseCase(TestCase):
            pass

        class TC(BaseCase):
            @classmethod
            def setup(cls, testbed: TestBed) -> None:
                """
                Set up the suite.

                :param testbed: TestBed instance.
                :return: None.
                """
                pass

        class TC_HGDB(TC):
            pass

        class TC_HGDB_ACCESS(TC_HGDB):
            @classmethod
            def teardown(cls, testbed: TestBed) -> None:
                """
                Tear down the suite.

                :param testbed: TestBed instance.
                :return: None.
                """
                pass

        class TC_HGDB_ACCESS_001(TC_HGDB_ACCESS):
            pass

        self.assertEqual(
            self.runner._suite_chain(TC_HGDB_ACCESS_001),
            (TC, TC_HGDB_ACCESS)
        )
```

这个测试同时证明：

- 没有自行声明 suite 钩子的 `BaseCase` 不进入链。
- `TC_HGDB` 不会因为继承 `TC.setup` 而重复进入链。
- 只声明 teardown 的 suite 也会进入链。

- [ ] **Step 2: 运行测试并确认失败**

Run:

```bash
../venv/bin/python -m unittest \
  tests.test_runner.TestRunner.test_suite_chain -v
```

Expected: `AttributeError: 'Runner' object has no attribute '_suite_chain'`。

- [ ] **Step 3: 实现 suite 链提取**

在 `Runner._import_case()` 之前增加：

```python
    def _suite_chain(
        self,
        casecls: type[TestCase]
    ) -> tuple[type[TestCase], ...]:
        """
        Get suite classes declared in a testcase MRO.

        :param casecls: Testcase class.
        :return: Suite classes ordered from outermost to innermost.
        """
        mro = casecls.__mro__
        parents = mro[1:mro.index(TestCase)]
        return tuple(
            cls
            for cls in reversed(parents)
            if any(
                isinstance(vars(cls).get(stage), classmethod)
                for stage in ('setup', 'teardown')
            )
        )
```

- [ ] **Step 4: 运行 Runner 单元测试**

Run:

```bash
../venv/bin/python -m unittest tests.test_runner -v
```

Expected: 全部通过。

- [ ] **Step 5: 提交**

```bash
git add xbot/framework/runner.py tests/test_runner.py
git commit -m 'feat: derive testcase suites from class hierarchy'
```

---

### Task 3: Runner 正常 Suite 生命周期

**Files:**
- Modify: `xbot/framework/runner.py:38-71`
- Test: `tests/test_runner.py`

**Interfaces:**
- Consumes: `Runner._suite_chain()` 和现有 `TestSet.paths` 顺序。
- Produces:
  - `Runner._run_suite_hook(suitecls: type[TestCase], stage: str) -> None`
  - Runner 单遍增量 suite 切换。

- [ ] **Step 1: 写正常顺序测试**

在测试方法内定义最小假用例基类和层级，用事件列表记录调用：

```python
    def test_suite_lifecycle_order(self) -> None:
        """
        Test nested and sibling suite lifecycle order.

        :return: None.
        """
        events = []

        class BaseCase(TestCase):
            SKIPPED = False

            def __init__(
                self,
                testbed: TestBed,
                testset: TestSet,
                logroot: str
            ) -> None:
                """
                Initialize a fake testcase.

                :param testbed: TestBed instance.
                :param testset: TestSet instance.
                :param logroot: Testcase log root.
                :return: None.
                """
                self._caseid = self.__class__.__name__

            @property
            def caseid(self) -> str:
                """
                Return the fake testcase id.

                :return: Testcase id.
                """
                return self._caseid

            @property
            def skipped(self) -> bool:
                """
                Return whether the testcase is skipped.

                :return: Skip state.
                """
                return self.SKIPPED

            def run(self, skip_reason: str | None = None) -> None:
                """
                Record testcase execution.

                :param skip_reason: External skip reason.
                :return: None.
                """
                events.append(
                    f'{self.caseid}.skip'
                    if skip_reason
                    else self.caseid
                )

        class TC(BaseCase):
            @classmethod
            def setup(cls, testbed: TestBed) -> None:
                """
                Record setup.

                :param testbed: TestBed instance.
                :return: None.
                """
                events.append('TC.setup')

            @classmethod
            def teardown(cls, testbed: TestBed) -> None:
                """
                Record teardown.

                :param testbed: TestBed instance.
                :return: None.
                """
                events.append('TC.teardown')

        class TC_LEFT(TC):
            @classmethod
            def setup(cls, testbed: TestBed) -> None:
                """
                Record setup.

                :param testbed: TestBed instance.
                :return: None.
                """
                events.append('TC_LEFT.setup')

            @classmethod
            def teardown(cls, testbed: TestBed) -> None:
                """
                Record teardown.

                :param testbed: TestBed instance.
                :return: None.
                """
                events.append('TC_LEFT.teardown')

        class TC_LEFT_001(TC_LEFT):
            pass

        class TC_LEFT_002(TC_LEFT):
            pass

        class TC_RIGHT(TC):
            @classmethod
            def setup(cls, testbed: TestBed) -> None:
                """
                Record setup.

                :param testbed: TestBed instance.
                :return: None.
                """
                events.append('TC_RIGHT.setup')

            @classmethod
            def teardown(cls, testbed: TestBed) -> None:
                """
                Record teardown.

                :param testbed: TestBed instance.
                :return: None.
                """
                events.append('TC_RIGHT.teardown')

        class TC_RIGHT_001(TC_RIGHT):
            pass

        testset = MagicMock()
        testset.paths = ('left1.py', 'left2.py', 'right1.py')
        runner = Runner(self.runner.testbed, testset)
        with patch.object(
            runner,
            '_import_case',
            side_effect=(TC_LEFT_001, TC_LEFT_002, TC_RIGHT_001)
        ):
            with patch.object(
                runner,
                '_make_logroot',
                return_value=self.logroot
            ):
                with patch('xbot.framework.runner.enable_console_logging'):
                    with patch('xbot.framework.runner.xprint'):
                        runner.run('verbose')

        self.assertEqual(events, [
            'TC.setup',
            'TC_LEFT.setup',
            'TC_LEFT_001',
            'TC_LEFT_002',
            'TC_LEFT.teardown',
            'TC_RIGHT.setup',
            'TC_RIGHT_001',
            'TC_RIGHT.teardown',
            'TC.teardown'
        ])
```

在 `setUpClass()` 中保存 `cls.logroot = tempfile.mkdtemp()`，并在
`tearDownClass()` 中删除它。把 `MagicMock` 加入文件顶部
`unittest.mock` 导入。

- [ ] **Step 2: 运行测试并确认失败**

Run:

```bash
../venv/bin/python -m unittest \
  tests.test_runner.TestRunner.test_suite_lifecycle_order -v
```

Expected: 事件列表缺少全部 suite setup 和 teardown。

- [ ] **Step 3: 增加 suite 钩子调用**

在 Runner 中增加：

```python
    def _run_suite_hook(
        self,
        suitecls: type[TestCase],
        stage: str
    ) -> None:
        """
        Run a hook declared by a suite class.

        :param suitecls: Suite class.
        :param stage: Hook name, setup or teardown.
        :return: None.
        """
        hook = vars(suitecls).get(stage)
        if isinstance(hook, classmethod):
            getattr(suitecls, stage)(self.testbed)
```

重写 `Runner.run()` 的用例准备和循环部分：

```python
        cases = []
        enabled_suites = set()
        for casepath in self.testset.paths:
            caseid = casepath.split('/')[-1].replace('.py', '')
            abspath = os.path.abspath(casepath)
            suites: tuple[type[TestCase], ...] = ()
            try:
                casecls = self._import_case(casepath)
                caseinst = casecls(self.testbed, self.testset, logroot)
                suites = self._suite_chain(casecls)
            except (ImportError, AttributeError, SyntaxError) as exc:
                caseinst = ErrorTestCase(
                    caseid,
                    abspath,
                    self.testbed,
                    self.testset,
                    logroot,
                    exc
                )
            cases.append((caseid, caseinst, suites))
            if not caseinst.skipped:
                enabled_suites.update(suites)

        active_suites: list[type[TestCase]] = []
        try:
            for i, (caseid, caseinst, suites) in enumerate(cases):
                target_suites = [
                    suite for suite in suites if suite in enabled_suites
                ]
                common = 0
                for active, target in zip(active_suites, target_suites):
                    if active is not target:
                        break
                    common += 1

                for suite in reversed(active_suites[common:]):
                    self._run_suite_hook(suite, 'teardown')
                del active_suites[common:]

                for suite in target_suites[common:]:
                    active_suites.append(suite)
                    self._run_suite_hook(suite, 'setup')

                order = f'({i + 1}/{casecnt})'
                if outfmt == 'verbose':
                    xprint(f'Start: {caseid} {order}'.center(100, '='))
                if outfmt == 'brief':
                    timer = self._timer(caseinst, i + 1, casecnt)
                caseinst.run()
                if outfmt == 'brief':
                    timer.join()
                if outfmt == 'verbose':
                    xprint(f'End: {caseid} {order}'.center(100, '='), '\n')
        finally:
            for suite in reversed(active_suites):
                self._run_suite_hook(suite, 'teardown')
```

保留 `run()` 前部的输出格式校验、控制台日志开关、`logroot` 和
`casecnt`，以及末尾的 `return logroot`。

- [ ] **Step 4: 运行 Runner 测试**

Run:

```bash
../venv/bin/python -m unittest tests.test_runner -v
```

Expected: 正常顺序测试和现有导入错误测试全部通过。

- [ ] **Step 5: 提交**

```bash
git add xbot/framework/runner.py tests/test_runner.py
git commit -m 'feat: run testcase suite lifecycle hooks'
```

---

### Task 4: Suite 失败隔离和标签过滤

**Files:**
- Modify: `xbot/framework/runner.py`
- Test: `tests/test_runner.py`

**Interfaces:**
- Consumes: Task 1 的 `TestCase.run(skip_reason)` 和 Task 3 的 suite 切换。
- Produces:
  - `Runner._setup_suite(suitecls: type[TestCase]) -> bool`
  - `Runner._teardown_suite(suitecls: type[TestCase]) -> None`
  - setup 失败后代 SKIP、teardown 失败继续清理。

- [ ] **Step 1: 写 setup 失败和兄弟继续测试**

把 `ClassVar` 加入文件顶部 `typing` 导入，并在 `TestRunner` 之前增加
可复用的假用例：

```python
class SuiteTestCase(TestCase):
    """
    Minimal testcase used by suite runner tests.
    """

    EVENTS: ClassVar[list[str]] = []
    SKIPPED: ClassVar[bool] = False

    def __init__(
        self,
        testbed: TestBed,
        testset: TestSet,
        logroot: str
    ) -> None:
        """
        Initialize a fake testcase.

        :param testbed: TestBed instance.
        :param testset: TestSet instance.
        :param logroot: Testcase log root.
        :return: None.
        """
        self._caseid = self.__class__.__name__

    @property
    def caseid(self) -> str:
        """
        Return the fake testcase id.

        :return: Testcase id.
        """
        return self._caseid

    @property
    def skipped(self) -> bool:
        """
        Return whether the testcase is skipped.

        :return: Skip state.
        """
        return self.SKIPPED

    def run(self, skip_reason: str | None = None) -> None:
        """
        Record testcase execution.

        :param skip_reason: External skip reason.
        :return: None.
        """
        self.EVENTS.append(
            f'{self.caseid}.skip:{skip_reason}'
            if skip_reason
            else self.caseid
        )
```

在 `TestRunner` 中增加执行辅助方法：

```python
    def run_suite_cases(
        self,
        *caseclasses: type[SuiteTestCase]
    ) -> list[str]:
        """
        Run fake testcase classes through Runner.

        :param caseclasses: Fake testcase classes in execution order.
        :return: Recorded lifecycle events.
        """
        SuiteTestCase.EVENTS.clear()
        testset = MagicMock()
        testset.paths = tuple(
            f'case{index}.py'
            for index in range(len(caseclasses))
        )
        runner = Runner(self.runner.testbed, testset)
        with patch.object(
            runner,
            '_import_case',
            side_effect=caseclasses
        ):
            with patch.object(
                runner,
                '_make_logroot',
                return_value=self.logroot
            ):
                with patch('xbot.framework.runner.enable_console_logging'):
                    with patch('xbot.framework.runner.xprint'):
                        runner.run('verbose')
        return SuiteTestCase.EVENTS.copy()
```

增加 setup 失败测试：

```python
    def test_suite_setup_failure(self) -> None:
        """
        Test setup failure isolation and sibling execution.

        :return: None.
        """
        class TC(SuiteTestCase):
            @classmethod
            def setup(cls, testbed: TestBed) -> None:
                """
                Record setup.

                :param testbed: TestBed instance.
                :return: None.
                """
                cls.EVENTS.append('TC.setup')

            @classmethod
            def teardown(cls, testbed: TestBed) -> None:
                """
                Record teardown.

                :param testbed: TestBed instance.
                :return: None.
                """
                cls.EVENTS.append('TC.teardown')

        class TC_LEFT(TC):
            @classmethod
            def setup(cls, testbed: TestBed) -> None:
                """
                Fail suite setup.

                :param testbed: TestBed instance.
                :return: None.
                """
                cls.EVENTS.append('TC_LEFT.setup')
                raise RuntimeError('setup failed')

            @classmethod
            def teardown(cls, testbed: TestBed) -> None:
                """
                Record teardown.

                :param testbed: TestBed instance.
                :return: None.
                """
                cls.EVENTS.append('TC_LEFT.teardown')

        class TC_LEFT_001(TC_LEFT):
            pass

        class TC_RIGHT(TC):
            @classmethod
            def setup(cls, testbed: TestBed) -> None:
                """
                Record setup.

                :param testbed: TestBed instance.
                :return: None.
                """
                cls.EVENTS.append('TC_RIGHT.setup')

            @classmethod
            def teardown(cls, testbed: TestBed) -> None:
                """
                Record teardown.

                :param testbed: TestBed instance.
                :return: None.
                """
                cls.EVENTS.append('TC_RIGHT.teardown')

        class TC_RIGHT_001(TC_RIGHT):
            pass

        events = self.run_suite_cases(TC_LEFT_001, TC_RIGHT_001)
        self.assertEqual(events, [
            'TC.setup',
            'TC_LEFT.setup',
            'TC_LEFT_001.skip:Suite TC_LEFT setup failed.',
            'TC_LEFT.teardown',
            'TC_RIGHT.setup',
            'TC_RIGHT_001',
            'TC_RIGHT.teardown',
            'TC.teardown'
        ])
```

- [ ] **Step 2: 写 teardown 失败仍清理父级测试**

```python
    def test_suite_teardown_failure(self) -> None:
        """
        Test that teardown failure does not block parent cleanup.

        :return: None.
        """
        class TC(SuiteTestCase):
            @classmethod
            def setup(cls, testbed: TestBed) -> None:
                """
                Record setup.

                :param testbed: TestBed instance.
                :return: None.
                """
                cls.EVENTS.append('TC.setup')

            @classmethod
            def teardown(cls, testbed: TestBed) -> None:
                """
                Record teardown.

                :param testbed: TestBed instance.
                :return: None.
                """
                cls.EVENTS.append('TC.teardown')

        class TC_CHILD(TC):
            @classmethod
            def teardown(cls, testbed: TestBed) -> None:
                """
                Fail suite teardown.

                :param testbed: TestBed instance.
                :return: None.
                """
                cls.EVENTS.append('TC_CHILD.teardown')
                raise RuntimeError('teardown failed')

        class TC_CHILD_001(TC_CHILD):
            pass

        events = self.run_suite_cases(TC_CHILD_001)
        self.assertEqual(events[-2:], [
            'TC_CHILD.teardown',
            'TC.teardown'
        ])
```

- [ ] **Step 3: 写全部标签过滤测试**

```python
    def test_all_suite_cases_filtered(self) -> None:
        """
        Test that a fully filtered suite runs no hooks.

        :return: None.
        """
        class TC_FILTERED(SuiteTestCase):
            @classmethod
            def setup(cls, testbed: TestBed) -> None:
                """
                Record setup.

                :param testbed: TestBed instance.
                :return: None.
                """
                cls.EVENTS.append('TC_FILTERED.setup')

            @classmethod
            def teardown(cls, testbed: TestBed) -> None:
                """
                Record teardown.

                :param testbed: TestBed instance.
                :return: None.
                """
                cls.EVENTS.append('TC_FILTERED.teardown')

        class TC_FILTERED_001(TC_FILTERED):
            SKIPPED = True

        events = self.run_suite_cases(TC_FILTERED_001)
        self.assertEqual(events, ['TC_FILTERED_001'])
```

- [ ] **Step 4: 运行三个测试并确认失败**

Run:

```bash
../venv/bin/python -m unittest \
  tests.test_runner.TestRunner.test_suite_setup_failure \
  tests.test_runner.TestRunner.test_suite_teardown_failure \
  tests.test_runner.TestRunner.test_all_suite_cases_filtered -v
```

Expected:

- setup 异常直接中止 Runner；
- teardown 异常阻断父级清理；
- 标签过滤测试在 Task 3 的 enabled-suite 逻辑下应已通过。

- [ ] **Step 5: 实现异常隔离**

在 `runner.py` 文件顶部增加标准库导入：

```python
import traceback
```

增加两个最小包装方法：

```python
    def _setup_suite(self, suitecls: type[TestCase]) -> bool:
        """
        Set up a suite and report failure.

        :param suitecls: Suite class.
        :return: True when setup succeeds.
        """
        try:
            self._run_suite_hook(suitecls, 'setup')
            return True
        except Exception:
            logger.error(
                'Suite %s setup failed:\n%s',
                suitecls.__name__,
                traceback.format_exc().strip()
            )
            return False

    def _teardown_suite(self, suitecls: type[TestCase]) -> None:
        """
        Tear down a suite and report failure.

        :param suitecls: Suite class.
        :return: None.
        """
        try:
            self._run_suite_hook(suitecls, 'teardown')
        except Exception:
            logger.error(
                'Suite %s teardown failed:\n%s',
                suitecls.__name__,
                traceback.format_exc().strip()
            )
```

在 `run()` 中用 `_teardown_suite()` 替换直接 teardown 调用，并维护
一个失败 suite：

```python
        active_suites: list[type[TestCase]] = []
        failed_suite: type[TestCase] | None = None
```

suite 切换部分改为：

```python
                for suite in reversed(active_suites[common:]):
                    self._teardown_suite(suite)
                del active_suites[common:]
                if failed_suite not in active_suites:
                    failed_suite = None

                if failed_suite is None:
                    for suite in target_suites[common:]:
                        active_suites.append(suite)
                        if not self._setup_suite(suite):
                            failed_suite = suite
                            break
```

叶子执行改为：

```python
                skip_reason = None
                if failed_suite is not None:
                    skip_reason = (
                        f'Suite {failed_suite.__name__} setup failed.'
                    )
                caseinst.run(skip_reason)
```

最终清理改为：

```python
        finally:
            for suite in reversed(active_suites):
                self._teardown_suite(suite)
```

- [ ] **Step 6: 运行 Runner 和 TestCase 测试**

Run:

```bash
../venv/bin/python -m unittest \
  tests.test_runner tests.test_testcase -v
```

Expected: 全部通过；测试日志中允许出现预期的 suite 异常记录。

- [ ] **Step 7: 提交**

```bash
git add xbot/framework/runner.py tests/test_runner.py
git commit -m 'feat: isolate testcase suite hook failures'
```

---

### Task 5: 用户文档和完整回归

**Files:**
- Modify: `README.md:216-226`
- Modify: `README.zh.md:214-224`
- Verify: `xbot/framework/testcase.py`
- Verify: `xbot/framework/runner.py`
- Verify: `tests/test_testcase.py`
- Verify: `tests/test_runner.py`

**Interfaces:**
- Consumes: 最终 suite API 和已通过的单元测试。
- Produces: 中英文使用说明和完整验证证据。

- [ ] **Step 1: 更新中文文档**

在 `README.zh.md` 的 testcase 规则之后增加：

````markdown
### Suite 级 setup 和 teardown

用例继承链中的中间父类可以声明类方法，在进入和离开该组用例时各执行
一次：

```python
from typing import ClassVar

from lib.testcase import TestCase
from lib.testbed import TestBed


class TC_ACCESS(TestCase):

    database: ClassVar[str | None] = None

    @classmethod
    def setup(cls, testbed: TestBed) -> None:
        """
        Initialize suite resources.

        :param testbed: TestBed instance.
        :return: None.
        """
        cls.database = testbed.get('database')

    @classmethod
    def teardown(cls, testbed: TestBed) -> None:
        """
        Release suite resources.

        :param testbed: TestBed instance.
        :return: None.
        """
        cls.database = None
```

Runner 按继承关系从外到内执行 suite setup，从内到外执行 suite
teardown。父类中的普通实例方法和类属性仍由所有子用例继承。
````

- [ ] **Step 2: 更新英文文档**

在 `README.md` 对应位置增加：

````markdown
### Suite setup and teardown

An intermediate parent class in a testcase inheritance chain can declare
class methods that run once when Runner enters and leaves that group:

```python
from typing import ClassVar

from lib.testcase import TestCase
from lib.testbed import TestBed


class TC_ACCESS(TestCase):

    database: ClassVar[str | None] = None

    @classmethod
    def setup(cls, testbed: TestBed) -> None:
        """
        Initialize suite resources.

        :param testbed: TestBed instance.
        :return: None.
        """
        cls.database = testbed.get('database')

    @classmethod
    def teardown(cls, testbed: TestBed) -> None:
        """
        Release suite resources.

        :param testbed: TestBed instance.
        :return: None.
        """
        cls.database = None
```

Runner calls suite setup from outermost to innermost and suite teardown
from innermost to outermost. Regular instance methods and class attributes
defined by a parent remain available to every child testcase.
````

- [ ] **Step 3: 运行完整测试集**

Run:

```bash
../venv/bin/python tests/run.py
```

Expected: 所有测试通过，进程退出码为 `0`。

- [ ] **Step 4: 检查格式和修改范围**

Run:

```bash
git diff --check
git status --short
```

Expected:

- `git diff --check` 无输出；
- 只包含计划列出的实现、测试和 README 修改；
- 不包含日志、缓存或构建产物。

- [ ] **Step 5: 提交**

```bash
git add README.md README.zh.md
git commit -m 'docs: explain testcase suite lifecycle hooks'
```

- [ ] **Step 6: 最终验证**

Run:

```bash
../venv/bin/python tests/run.py
git diff --check HEAD~5
git status --short
```

Expected:

- 完整测试集再次通过；
- 五个计划提交后的累计 diff 无格式错误；
- 工作区干净。
