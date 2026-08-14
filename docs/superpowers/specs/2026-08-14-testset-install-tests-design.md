# TestSet 安装分组测试设计

## 目标

完善 `testcases.install/test` 新结构的测试，并验证以下运行语义：

1. `install` 和 `test` 分组分别解析、展开并保持既定顺序；
2. `install` 用例忽略测试套的 tags 过滤；
3. 任一 `install` 用例未通过时，后续安装和测试用例均不再执行；
4. 所有安装用例通过后，测试用例继续按顺序执行。

本次只覆盖新结构直接引入的行为，不增加兼容旧 `paths` 格式、测试框架或
公共测试抽象。

## TestSet 单元测试

修改 `tests/test_testset.py`：

- 将现有测试数据中的 `paths` 改为必需的 `testcases.install/test`；
- 验证文件路径原样保留；
- 验证目录递归展开后只包含 `tc_*.py`，并保持字母顺序；
- 验证 `install` 和 `test` 分组相互独立；
- 验证两个分组允许为空；
- 验证缺少 `testcases`、`testcases.install` 或 `testcases.test` 时抛出
  `TestSetError`；
- 验证分组不是列表及路径不存在时抛出 `TestSetError`；
- 保留现有 tags 正常值、空值、缺失和类型错误测试。

测试直接使用现有临时目录结构，不新增夹具框架或辅助模块。

## Runner 集成测试

修改 `tests/test_runner.py`，复用 `INIT_DIR` 复制出的临时工程和真实
`TestCase` 执行路径：

### 安装成功

- 测试套 tags 故意不匹配安装用例；
- 安装用例仍执行并生成结果为 `PASS` 的日志；
- 后续测试用例继续执行并生成既有预期结果。

这条测试同时验证 `Runner` 到 `TestCase` 执行线程的“忽略 tags”参数传递，
避免只验证方法调用表面。

### 安装失败

- 使用失败安装用例作为第一项；
- 失败安装用例生成非 `PASS` 日志；
- 后续安装用例和测试用例不生成日志；
- 输出包含安装失败导致执行中断的提示。

断言观察到的日志和输出，不绑定循环下标等内部实现。

## 最小配套修正

测试暴露实现问题时，只做以下直接修正：

- `TestCase.run()` 将 `never_skip` 参数传给实际执行线程；
- 实际执行逻辑仅在 `never_skip` 为假时应用 tags 过滤；
- 统一新增示例安装用例的文件名及测试套引用中的 `software` 拼写；
- 清理本次改动引入的行尾空白。

不调整无关生命周期、报告、日志格式或公共 API。

## 验证

先运行：

```text
../venv/bin/python -m unittest tests.test_testset tests.test_runner
```

再运行受调用变化影响的测试：

```text
../venv/bin/python -m unittest \
    tests.test_testset \
    tests.test_testcase \
    tests.test_runner \
    tests.test_main \
    tests.test_report
```

最后运行 `git diff --check`，确认没有空白错误。
