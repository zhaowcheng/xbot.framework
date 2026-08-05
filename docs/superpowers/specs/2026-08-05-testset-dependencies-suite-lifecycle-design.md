# 测试套依赖与父类生命周期用例设计

## 目标

为 `xbot.framework` 增加两项能力：

1. 测试套 `paths` 中的每一项可依赖前面的一个或多个 path 项。只有全部
   依赖项成功，当前项才执行，否则当前项展开出的原始用例全部置为
   `BLOCK`，并在日志中记录原因。
2. Runner 根据用例继承关系，把父类自身声明的 `setup` 和 `teardown`
   分别作为独立用例插入执行序列，使控制台和最终报告包含完整的父类
   生命周期日志。

不恢复已回滚的 `@classmethod` suite API。父类继续使用现有普通实例方法：

```python
def setup(self) -> None:
    pass

def teardown(self) -> None:
    pass
```

## 测试套格式

现有字符串格式保持兼容：

```yaml
paths:
  - testcases/hgdb/access/level/
```

需要声明依赖时使用字典格式：

```yaml
paths:
  - testcases/hgdb/access/level/
  - path: testcases/hgdb/access/rl/
    depends:
      - testcases/hgdb/access/level/
```

`depends` 引用前面 path 项的 `path` 原值。每个 path 在同一测试套中必须
唯一。

以下情况在解析时抛出 `TestSetError`：

- path 项不是字符串或合法字典；
- 字典缺少 `path`；
- `path` 不是字符串；
- `depends` 不是字符串列表；
- path 重复或不存在；
- path 未展开出任何 `tc_*.py` 用例；
- 依赖自身、不存在的项或后面的项。

`TestSet.paths` 继续返回按现有规则展开后的原始用例路径，不包含父类
生命周期用例。TestSet 另外保留有序的 path 项及其依赖，供 Runner 编译
执行计划。

## Path 依赖语义

一个 path 项的成功状态只由该项展开出的原始用例决定。仅当全部原始用例
结果都是 `PASS` 时，该项成功。

以下任一结果都会使 path 项不成功：

- `FAIL`
- `ERROR`
- `TIMEOUT`
- `SKIP`
- `BLOCK`

每个 path 项开始前检查其全部依赖。存在未成功的依赖时：

1. 当前项不执行；
2. 当前项展开出的全部原始用例生成 `BLOCK` HTML 日志；
3. 日志原因列出未成功的依赖 path 及其原始用例结果；
4. 被阻塞用例不调用自身的 setup、steps 或 teardown。

父类生命周期用例仍显示在总报告中，但不直接参与 path 项成功状态计算。
父类 setup 失败会使原始用例 `BLOCK`，因此会间接使 path 项失败。父类
teardown 是清理阶段，其失败不追溯改变已完成的 path 状态，也不阻塞后续
path 依赖。

## 父类生命周期识别

Runner 导入原始用例类后，从其 MRO 中提取框架 `TestCase` 与叶子用例类
之间的父类，顺序遵循 Python MRO。

仅当 `vars(parent)` 中存在 `setup` 或 `teardown` 时，才把相应方法识别为
该父类自身的生命周期方法。继承来的方法不在子层重复插入。框架
`TestCase` 和叶子用例类自身不作为父类生命周期节点。

用例导入失败时继续生成现有 `ErrorTestCase`。由于没有可用用例类，不为
该用例推断父类生命周期。

## 执行计划

Runner 在执行前把原始用例和父类生命周期展开成一个有序列表，不实现
通用 DAG 或并行调度器。

对相邻原始用例的父类链计算最长公共前缀：

1. 离开父类链时，从内向外插入 teardown；
2. 进入新父类链时，从外向内插入 setup；
3. 插入原始叶子用例；
4. 全部原始用例结束后，从内向外插入剩余 teardown。

例如：

```text
TC.setup
TC_HGDB.setup
TC_HGDB_ACCESS.setup
TC_HGDB_ACCESS_LEVEL.setup
TC_HGDB_ACCESS_LEVEL_003
TC_HGDB_ACCESS_LEVEL_ALTERTABLE_001
TC_HGDB_ACCESS_LEVEL_ALTERUSER_002
TC_HGDB_ACCESS_LEVEL.teardown
TC_HGDB_ACCESS_RL.setup
TC_HGDB_ACCESS_RL_ROWLEVEL_002
TC_HGDB_ACCESS_RL_TABLELEVEL_001
TC_HGDB_ACCESS_RL.teardown
TC_HGDB_ACCESS.teardown
TC_HGDB.teardown
TC.teardown
```

同一父类在连续用例间保持打开；离开后再次进入时执行新一轮 setup 和
teardown。

父类下全部原始用例均被标签过滤时，不执行该父类的 setup 和 teardown；
原始用例仍按现有规则生成 `SKIP` 日志。只有部分用例被过滤时，父类
生命周期正常执行。

## 生命周期依赖与清理

子父类 setup 和叶子用例依赖其所有父类 setup 成功。任一父类 setup 结果
不是 `PASS` 时，后代 setup 和原始用例均生成 `BLOCK` 日志。

清理遵循以下规则：

- 某层 setup 只要实际开始执行，即使结果为 `FAIL`、`ERROR` 或
  `TIMEOUT`，该层 teardown 仍执行；
- 因父级失败或 path 依赖失败而未执行 setup 的层，其 teardown 为
  `BLOCK`；
- 原始用例失败不阻止父类 teardown；
- 子层 teardown 失败不阻止外层 teardown。

一个 path 因依赖条件而阻塞时，只为该项新进入的父类 setup 生成
`BLOCK`。已经由前一项成功进入且仍处于打开状态的公共父类保持有效，并在
正常离开时执行 teardown。

同一轮父类 setup 和 teardown 共用一个父类实例，保证 teardown 能访问
setup 写入的实例状态。

## 生命周期用例与日志

父类 setup 和 teardown 各由一个轻量生命周期用例承载，复用现有
`TestCase` 的线程、超时、计时、日志和 HTML 输出。

用例 ID 使用：

```text
TC.setup
TC_HGDB.teardown
```

日志位于父类源码对应的测试目录，例如：

```text
logs/<testbed>/<timestamp>/testcases/hgdb/access/
    TC_HGDB_ACCESS.setup.html
```

生命周期日志包含父类源码、测试床内容、时间、结果和钩子产生的日志。
setup 与 teardown 是两个独立报告条目，但共享父类实例。

生命周期方法沿用现有结果规则：

- 普通异常为 `FAIL`；
- `TestCaseError` 为 `ERROR`；
- 超时为 `TIMEOUT`；
- 无异常为 `PASS`。

## BLOCK 与报告

`TestCase` 增加带原因的阻塞执行入口。BLOCK 用例：

1. 设置开始和结束时间；
2. 不调用任何用户方法；
3. 在日志中输出明确原因；
4. 设置结果为 `BLOCK`；
5. 生成与普通用例一致的 HTML 日志。

控制台简要输出显示 `BLOCK`。报告模板增加 BLOCK 计数，存在 BLOCK 时
总结果不通过。

Runner 为每个执行节点分配顺序号并写入日志元数据。报告优先按顺序号
排序，避免多个快速生命周期用例在同一秒内被按文件名重排。缺少顺序号的
旧日志继续使用现有时间和路径排序方式。

## 修改范围

- `xbot/framework/testset.py`
  - 解析、校验并展开带依赖的 path 项。
- `xbot/framework/runner.py`
  - 编译并执行扁平计划，维护 path 状态和父类链。
- `xbot/framework/testcase.py`
  - 支持 BLOCK 和父类生命周期用例。
- `xbot/framework/report.py`
  - 识别 BLOCK 并按执行顺序生成报告。
- `xbot/framework/statics/log_template.html`
  - 保存执行顺序元数据。
- `xbot/framework/statics/report_template.html`
  - 展示 BLOCK 计数。
- `tests/`
  - 覆盖解析、执行顺序、失败传播、日志和报告。
- `README.md`、`README.zh.md`
  - 记录测试套依赖格式和父类生命周期 API。

不增加第三方依赖、通用依赖图、并行调度器或额外框架模块。

## 验证

测试至少覆盖：

1. 新旧 YAML 格式和全部依赖校验；
2. 单个及多个前置 path 的成功和 BLOCK 传播；
3. `FAIL`、`ERROR`、`TIMEOUT`、`SKIP`、`BLOCK` 对 path 状态的影响；
4. 多层继承从外到内 setup、从内到外 teardown；
5. 同级父类切换和公共父类复用；
6. 仅识别父类自身声明的方法；
7. setup 失败后代 BLOCK，且已开始层仍清理；
8. 未开始层 teardown BLOCK；
9. 原始用例或子 teardown 失败不阻止外层清理；
10. setup 和 teardown 共享父类实例状态；
11. 全部及部分标签过滤的生命周期行为；
12. 生命周期日志、BLOCK 原因、报告计数和报告顺序；
13. 原有完整测试集回归。
