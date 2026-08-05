# 测试套依赖与父类生命周期用例实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为测试套增加有序 path 依赖，并把父类普通实例 `setup` 和
`teardown` 作为带完整日志的独立用例插入执行序列。

**Architecture:** `TestSet` 把 YAML 转换为有序 `PathItem`；Runner 在执行前
导入原始用例并根据 MRO 编译扁平执行计划。`TestCase` 统一承载普通用例、
BLOCK 和生命周期用例的执行与日志，报告读取执行顺序元数据并统计 BLOCK。

**Tech Stack:** Python 3.10、标准库 `dataclasses`/`inspect`、ruamel.yaml、
unittest、Jinja HTML 模板。

## Global Constraints

- 保持现有字符串 `paths`、`TestSet.paths`、标签和普通用例 API 兼容。
- `depends` 只能引用前面唯一的 path 原值。
- 只有 path 展开的全部原始用例均为 `PASS` 时，该 path 才成功。
- 父类钩子必须是自身声明的普通实例 `setup`/`teardown`。
- setup 与 teardown 共用父类实例，且清理不因叶子或子清理失败而中断。
- 不增加第三方依赖、通用 DAG、并行调度器或额外框架模块。
- Python docstring、引号、导入和 80 字符换行遵守仓库 `AGENTS.md`。

---

### Task 1: 解析并校验带依赖的 path 项

**Files:**
- Modify: `xbot/framework/testset.py:7-92`
- Test: `tests/test_testset.py:1-206`

**Interfaces:**
- Consumes: YAML 中字符串项或
  `{'path': str, 'depends': list[str] | None}`。
- Produces: `PathItem(path: str, depends: tuple[str, ...],
  cases: tuple[str, ...])` 和
  `TestSet.path_items -> tuple[PathItem, ...]`。
- Preserves: `TestSet.paths -> tuple[str, ...]`，仅包含原始用例。

- [ ] **Step 1: 为新旧格式和校验规则编写失败测试**

在 `tests/test_testset.py` 文件顶部导入 `PathItem`，增加以下核心断言；使用
现有临时测试目录，不在测试函数内延迟导入：

```python
def test_path_items(self):
    """
    Test path items and dependencies.
    """
    content = """
    tags:
      include:
      exclude:
    paths:
      - testcases/dir1/tc_01.py
      - path: testcases/dir2
        depends:
          - testcases/dir1/tc_01.py
    """
    testset = self.mock_testset(content)
    self.assertEqual(
        testset.path_items,
        (
            PathItem(
                'testcases/dir1/tc_01.py',
                tuple(),
                ('testcases/dir1/tc_01.py',)
            ),
            PathItem(
                'testcases/dir2',
                ('testcases/dir1/tc_01.py',),
                (
                    'testcases/dir2/tc_03.py',
                    'testcases/dir2/tc_04.py',
                    'testcases/dir2/subdir2_1/tc_05.py',
                    'testcases/dir2/subdir2_1/tc_06.py'
                )
            )
        )
    )
```

再分别覆盖：非字符串/字典项、缺少或非字符串 `path`、非列表或含非字符串
的 `depends`、未知键、重复 path、引用自身/未知/后项、不存在 path、空目录。
每个输入都断言构造 `TestSet` 时抛出 `TestSetError`。

- [ ] **Step 2: 运行 TestSet 测试并确认失败**

Run:

```bash
venv/bin/python -m unittest tests.test_testset -v
```

Expected: FAIL，原因是 `PathItem` 或 `path_items` 尚不存在，或者新格式尚不能
解析。

- [ ] **Step 3: 实现最小 PathItem 解析**

在 `xbot/framework/testset.py` 使用标准库 dataclass：

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class PathItem:
    """
    Parsed testset path item.
    """
    path: str
    depends: tuple[str, ...]
    cases: tuple[str, ...]
```

在 `TestSet.__init__` 中完成一次解析，新增：

```python
@property
def path_items(self) -> tuple[PathItem, ...]:
    """
    Parsed path items.

    :return: Ordered path items.
    """
    return tuple(self._path_items)
```

用一个 `_expand_path(path: str) -> tuple[str, ...]` 复用现有文件/目录展开
逻辑。解析每项时只接受 `path`、`depends` 两个键；验证 path 唯一且每个
依赖已出现在 `seen_paths` 中。不存在或没有展开出 `tc_*.py` 的 path 直接
抛出 `TestSetError`。`paths` 改为：

```python
return tuple(
    case
    for item in self._path_items
    for case in item.cases
)
```

- [ ] **Step 4: 运行 TestSet 测试并确认通过**

Run:

```bash
venv/bin/python -m unittest tests.test_testset -v
```

Expected: PASS。

- [ ] **Step 5: 提交 TestSet 变更**

```bash
git add xbot/framework/testset.py tests/test_testset.py
git commit -m 'feat: add testset path dependencies'
```

---

### Task 2: 为 TestCase 增加 BLOCK 与生命周期用例

**Files:**
- Modify: `xbot/framework/testcase.py:17-358`
- Test: `tests/test_testcase.py:1-199`

**Interfaces:**
- Consumes:
  `TestCase.run(block_reason: str | None = None,
  sequence: int | None = None) -> None`。
- Produces:
  `LifecycleTestCase(suitecls, suiteinst, stage, relpath, testbed, testset,
  logroot)`。
- Produces:
  `TestCase._remove_log_handler() -> None`，供 Runner 清理由父类实例产生但
  不使用的处理器。

- [ ] **Step 1: 编写 BLOCK 和共享父类实例的失败测试**

在 `tests/test_testcase.py` 顶部定义测试父类，不在测试方法内声明导入：

```python
class SuiteStateCase(TestCase):
    """
    Parent class used by lifecycle tests.
    """
    def setup(self) -> None:
        """
        Save state.

        :return: None.
        """
        self.saved_state = 'ready'

    def teardown(self) -> None:
        """
        Verify state.

        :return: None.
        """
        if self.saved_state != 'ready':
            raise RuntimeError('setup state was not preserved')
```

增加两组测试：

1. `case.run(block_reason='dependency failed', sequence=7)` 后结果为
   `BLOCK`，setup/step/teardown 均未调用，HTML 包含原因和
   `id="sequence">7`。
2. 为同一个 `SuiteStateCase` 实例创建 setup、teardown 两个
   `LifecycleTestCase`，依次运行后均为 `PASS`，caseid 分别为
   `SuiteStateCase.setup`、`SuiteStateCase.teardown`，两个日志文件存在且
   不相同。

- [ ] **Step 2: 运行 TestCase 测试并确认失败**

Run:

```bash
venv/bin/python -m unittest tests.test_testcase -v
```

Expected: FAIL，原因是 `run()` 不接受 BLOCK/sequence，且
`LifecycleTestCase` 尚不存在。

- [ ] **Step 3: 实现 BLOCK 执行入口**

把 `run` 和私有执行方法改为传递两个可选值：

```python
def run(
    self,
    block_reason: str | None = None,
    sequence: int | None = None
) -> None:
    """
    Run the current testcase.

    :param block_reason: Reason for blocking this testcase.
    :param sequence: Execution sequence used by reports.
    :return: None.
    """
```

在普通标签判断之前处理 `block_reason`：

```python
if block_reason:
    self.__loghdlr.set_stage('setup')
    self.__result = 'BLOCK'
    self.warn(f'Blocked: {block_reason}')
elif self.skipped:
    ...
```

把 `sequence` 传给 `__dump_log`，再传入模板变量。新增幂等的：

```python
def _remove_log_handler(self) -> None:
    """
    Remove the testcase log handler.

    :return: None.
    """
    logger.ROOT_LOGGER.removeHandler(self.__loghdlr)
```

普通执行结束和异常退出均调用该方法，避免生命周期目标实例残留处理器。

- [ ] **Step 4: 实现 LifecycleTestCase**

在同一文件增加一个最小子类。它持有真实 `suiteinst`，因此 setup 和
teardown 可共享实例属性；用 `vars(suitecls)[stage]` 保证只调用父类自身
声明的方法：

```python
class LifecycleTestCase(TestCase):
    """
    Standalone parent setup or teardown testcase.
    """
    def __init__(
        self,
        suitecls: type[TestCase],
        suiteinst: TestCase,
        stage: str,
        relpath: str,
        testbed: TestBed,
        testset: TestSet,
        logroot: str
    ) -> None:
        """
        :param suitecls: Parent testcase class.
        :param suiteinst: Shared parent testcase instance.
        :param stage: Lifecycle stage.
        :param relpath: Synthetic testcase path.
        :param testbed: TestBed instance.
        :param testset: TestSet instance.
        :param logroot: Testcase log directory.
        """
        self.__suitecls = suitecls
        self.__suiteinst = suiteinst
        self.__stage = stage
        self.__relpath = relpath
        super().__init__(testbed, testset, logroot)
```

覆盖 `caseid`、`abspath`、`relpath`、`sourcecode`、`skipped` 和 `steps`。
setup 用例仅在 `setup()` 中调用目标方法；teardown 用例仅在
`teardown()` 中调用目标方法。另一个阶段为空操作。源码使用
`inspect.getsource(suitecls)`。

- [ ] **Step 5: 运行 TestCase 测试并确认通过**

Run:

```bash
venv/bin/python -m unittest tests.test_testcase -v
```

Expected: PASS。

- [ ] **Step 6: 提交 TestCase 变更**

```bash
git add xbot/framework/testcase.py tests/test_testcase.py
git commit -m 'feat: add blocked and lifecycle testcases'
```

---

### Task 3: 编译并执行扁平生命周期计划

**Files:**
- Modify: `xbot/framework/runner.py:7-120`
- Test: `tests/test_runner.py:1-83`

**Interfaces:**
- Consumes: `TestSet.path_items`、`LifecycleTestCase` 和
  `TestCase.run(block_reason, sequence)`。
- Produces:
  `Runner._build_plan(logroot: str) -> list[_PlanNode]`。
- Produces:
  `_PlanNode.case`、`.path`、`.setup_dependencies`、`.paired_setup`、
  `.original`、`.started`。

- [ ] **Step 1: 建立可复用的临时继承树测试工程**

扩展 `tests/test_runner.py` 的临时工程，使生成文件包含：

```text
testcases/
├── __init__.py                 # TC，记录 setup/teardown
└── hgdb/
    ├── __init__.py             # TC_HGDB
    └── access/
        ├── __init__.py         # TC_HGDB_ACCESS
        ├── level/
        │   ├── __init__.py     # TC_HGDB_ACCESS_LEVEL
        │   ├── tc_level_01.py
        │   └── tc_level_02.py
        └── rl/
            ├── __init__.py     # TC_HGDB_ACCESS_RL
            └── tc_rl_01.py
```

父类普通 setup/teardown 和叶子步骤向
`testcases.events.EVENTS: list[str]` 追加名称。测试套将 `rl/` 依赖
`level/`。

- [ ] **Step 2: 编写执行顺序与 path 依赖失败测试**

成功场景断言事件顺序为：

```python
[
    'TC.setup',
    'TC_HGDB.setup',
    'TC_HGDB_ACCESS.setup',
    'TC_HGDB_ACCESS_LEVEL.setup',
    'tc_level_01',
    'tc_level_02',
    'TC_HGDB_ACCESS_LEVEL.teardown',
    'TC_HGDB_ACCESS_RL.setup',
    'tc_rl_01',
    'TC_HGDB_ACCESS_RL.teardown',
    'TC_HGDB_ACCESS.teardown',
    'TC_HGDB.teardown',
    'TC.teardown'
]
```

再让 `tc_level_02` 返回 `FAIL`，断言 `tc_rl_01` 为 `BLOCK`，日志包含
`testcases/hgdb/access/level` 及 `tc_level_02=FAIL`，且 RL 新进入的 setup
和 teardown 均为 `BLOCK`。

- [ ] **Step 3: 编写 setup/teardown 失败与标签测试**

增加测试覆盖：

- 中层 setup 失败后，后代 setup 和叶子均 BLOCK；
- 失败层 teardown 仍运行，未进入子层 teardown 为 BLOCK；
- 子 teardown 失败后外层 teardown 仍运行；
- setup 写入实例属性，teardown 能读取；
- 某父类全部叶子 SKIP 时不产生该父类生命周期日志；
- 部分 SKIP 时父类生命周期仍执行；
- 导入失败继续产生 ErrorTestCase，不推断父类链；
- 同一父类离开后再次进入时生成新一轮生命周期且日志不覆盖。

- [ ] **Step 4: 运行 Runner 测试并确认失败**

Run:

```bash
venv/bin/python -m unittest tests.test_runner -v
```

Expected: FAIL，现有 Runner 只按 `TestSet.paths` 执行叶子。

- [ ] **Step 5: 增加最小计划节点**

在 `runner.py` 使用内部 dataclass，不新增模块：

```python
@dataclass
class _PlanNode:
    """
    One executable testcase in a compiled plan.
    """
    case: TestCase
    path: str | None = None
    setup_dependencies: tuple['_PlanNode', ...] = tuple()
    paired_setup: '_PlanNode | None' = None
    original: bool = False
    started: bool = False
```

增加 `_suite_chain(casecls)`：读取
`casecls.__mro__[1:casecls.__mro__.index(TestCase)]`，反转为外到内，并仅
保留 `vars(cls)` 中含 setup 或 teardown 的父类。

- [ ] **Step 6: 编译生命周期计划**

`_build_plan` 先导入并实例化全部原始用例，再标出至少拥有一个非 SKIP
叶子的父类。随后按相邻继承链最长公共前缀：

```python
common = 0
while (
    common < len(current)
    and common < len(target)
    and current[common].suitecls is target[common]
):
    common += 1
```

关闭 `current[common:]` 时从内向外插入 teardown；打开新层时实例化一次
真实父类对象、立即调用其 `_remove_log_handler()`，并创建共享该对象的
setup/teardown `LifecycleTestCase`。叶子节点依赖当前所有非空 setup
节点。

生命周期日志路径优先使用父类源码中从 `testcases` 开始的目录；父类不在
`testcases` 下时使用
`testcases/__suite__/<module path>/<Class>.<stage>.py`。同一父类重复进入
时从第二次开始在文件名加入 `.2`、`.3`，避免覆盖，caseid 保持不变。

- [ ] **Step 7: 执行计划并计算 BLOCK 原因**

Runner 按计划顺序执行。对原始用例和新进入 setup，先检查所属 path 的
前置项；再检查父 setup：

```python
reason = self._path_block_reason(node.path, path_results)
if reason is None:
    reason = self._setup_block_reason(node.setup_dependencies)
node.started = reason is None
node.case.run(block_reason=reason, sequence=index)
```

原始节点执行后把 `(caseid, result)` 追加到所属 path。teardown 仅在其
`paired_setup` 存在且 `started` 为 `False` 时 BLOCK；paired setup 即使
结果失败，只要实际开始过，teardown 就执行。没有 setup 的父类 teardown
正常执行。

BLOCK 原因格式保持稳定：

```text
Path `B` blocked by unsuccessful dependencies: A
(tc_01=PASS, tc_02=FAIL).
Parent setup did not pass: TC_HGDB.setup=FAIL.
Setup did not run: TC_HGDB_ACCESS.setup.
```

- [ ] **Step 8: 运行 Runner 和相邻模块测试**

Run:

```bash
venv/bin/python -m unittest \
  tests.test_runner \
  tests.test_testset \
  tests.test_testcase -v
```

Expected: PASS。

- [ ] **Step 9: 提交 Runner 变更**

```bash
git add xbot/framework/runner.py tests/test_runner.py
git commit -m 'feat: run parent lifecycle testcases'
```

---

### Task 4: 报告 BLOCK 与稳定执行顺序

**Files:**
- Modify: `xbot/framework/report.py:16-88`
- Modify: `xbot/framework/statics/log_template.html:83-118`
- Modify: `xbot/framework/statics/report_template.html:15-180`
- Test: `tests/test_report.py:1-28`

**Interfaces:**
- Consumes: 用例日志中的可选 `id="sequence"`。
- Produces: 报告 `blockcnt`、BLOCK 过滤按钮和按 sequence 排列的 cases。
- Preserves: 没有 sequence 的旧日志仍按 `(starttime, path)` 排列。

- [ ] **Step 1: 编写 BLOCK 统计和顺序失败测试**

在临时日志目录写入三个最小 HTML：

```html
<td id="result">BLOCK</td>
<td id="starttime">2026-08-05 12:00:00</td>
<td id="endtime">2026-08-05 12:00:00</td>
<td id="duration">0:00:00</td>
<span id="sequence" hidden>2</span>
```

另外两个分别使用 sequence 1 和 3。断言生成报告中 case 路径顺序按
1、2、3，含 `BLOCK[1]`，且 `allpassed` 为 `False`。保留现有静态旧日志
快照测试，证明缺少 sequence 时兼容。

- [ ] **Step 2: 运行报告测试并确认失败**

Run:

```bash
venv/bin/python -m unittest tests.test_report -v
```

Expected: FAIL，当前 counter 不认识 BLOCK 且不读取 sequence。

- [ ] **Step 3: 写入 sequence 并更新报告解析**

在日志模板 Summary 后加入：

```html
<span id="sequence" hidden>{{sequence or ''}}</span>
```

报告读取可选 sequence：

```python
match = re.search(r'id="sequence".*>(.*)<.*', content)
sequence = int(match.group(1)) if match and match.group(1) else None
```

`counter` 增加 `BLOCK`。只要一个 case 有 sequence，就使用：

```python
cases.sort(
    key=lambda case: (
        case['sequence'] is None,
        case['sequence'] or 0,
        case['starttime'],
        case['path']
    )
)
```

否则保留现有 `(starttime, path)` 排序。传递
`blockcnt=counter['BLOCK']`。

- [ ] **Step 4: 更新报告模板**

增加 `.filter_button.block`、`.BLOCK` 样式、`filterCase(6)` 分支和：

```html
<a class="block filter_button"
   href='javascript:filterCase(6)'>BLOCK[{{blockcnt}}]</a>
```

BLOCK 使用与 SKIP 区分的中性深灰背景，不改变其他结果颜色。

- [ ] **Step 5: 运行报告测试并更新必要快照**

Run:

```bash
venv/bin/python -m unittest tests.test_report -v
```

如果仅因报告模板新增 `BLOCK[0]` 导致 `report.ok.html` 快照失败，用实际
生成结果替换 `tests/resources/logs/report.ok.html`，再次运行并确认 PASS。

- [ ] **Step 6: 提交报告变更**

```bash
git add \
  xbot/framework/report.py \
  xbot/framework/statics/log_template.html \
  xbot/framework/statics/report_template.html \
  tests/test_report.py \
  tests/resources/logs/report.ok.html
git commit -m 'feat: report blocked testcases in execution order'
```

---

### Task 5: 文档、示例与完整回归

**Files:**
- Modify: `README.md:106-135,215-221`
- Modify: `README.zh.md:105-134,213-220`
- Modify:
  `xbot/framework/statics/initdir/testsets/testset_example.yml:1-12`
- Test: `tests/run.py`

**Interfaces:**
- Documents: 字符串/字典 paths、depends 成功语义、BLOCK、普通实例父类
  setup/teardown 和执行顺序。

- [ ] **Step 1: 更新测试套示例**

保持第一个 path 为字符串，把后续 path 改为依赖字典，示例同时展示兼容
格式和新格式：

```yaml
paths:
  - testcases/examples/pass/tc_eg_pass_get_values_from_testbed.py
  - path: testcases/examples/pass/tc_eg_pass_create_dirs_and_files.py
    depends:
      - testcases/examples/pass/tc_eg_pass_get_values_from_testbed.py
```

不要让示例中的 nonpass path 依赖前面的 pass path，以免改变其失败演示
目的。

- [ ] **Step 2: 更新中英文 README**

分别说明：

- `depends` 只引用前项 path 原值；
- 仅原始用例全部 PASS 才算 path 成功；
- 依赖失败生成 BLOCK 和原因日志；
- 父类用普通实例 setup/teardown；
- 只执行父类自身声明的方法；
- setup 外到内、teardown 内到外；
- cleanup 规则和独立报告条目。

英文和中文示例使用完全相同的 YAML 与类名。

- [ ] **Step 3: 运行完整测试集**

Run:

```bash
venv/bin/python tests/run.py
```

Expected: 所有测试 PASS，进程退出码为 0。

- [ ] **Step 4: 运行静态检查**

Run:

```bash
venv/bin/python -m compileall -q xbot tests
git diff --check
```

Expected: 两条命令退出码均为 0，无语法或空白错误。

- [ ] **Step 5: 检查最终范围**

Run:

```bash
git status --short
git diff --stat HEAD~4
```

Expected: 仅包含设计批准范围内的 framework、模板、README、测试和
Superpowers 文档；没有构建产物或无关文件。

- [ ] **Step 6: 提交文档与示例**

```bash
git add \
  README.md \
  README.zh.md \
  xbot/framework/statics/initdir/testsets/testset_example.yml
git commit -m 'docs: explain testset dependencies and lifecycle cases'
```

- [ ] **Step 7: 最终验证提交后的工作树**

Run:

```bash
venv/bin/python tests/run.py
git status --short
```

Expected: 完整测试集 PASS，工作树干净。
