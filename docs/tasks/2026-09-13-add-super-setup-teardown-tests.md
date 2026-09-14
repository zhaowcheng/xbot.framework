# Add Super Setup Teardown Tests

## 需求

1. 覆盖多层父类 setup 按从外到内执行、teardown 按从内到外执行，且每层只执行一次。
2. 覆盖同一父类下多个用例及不同分支切换时的生命周期行为。
3. 覆盖父类 setup 失败后子层和用例被 `BLOCK`，同时必要的 teardown 仍执行。
4. 覆盖安装用例失败、中途终止时已启动父类的 teardown。
5. 覆盖父类缺失、继承关系错误、未实现 setup/teardown 时抛出 `SuperClassError`。
6. 原则上仅补测试；允许最小修复 `TestSet.superclses` 的错误，使父类缺少 setup 或 teardown 时正确抛出 `SuperClassError`，不改变其他生产行为。
7. 允许在 `tc_eg_nonpass_fail_setup_with_failfast_false.py` 中恢复 `FAILFAST = False`，修复父类功能提交引入的示例行为回归。
8. 新增测试及受影响的现有测试全部通过。

## 实现

1. 修改 `xbot/framework/testset.py`：
   - 在发现父类后立即计算 `parentclsloc`，供继承关系和 setup/teardown 实现校验共同使用。
   - 确保父类缺少 setup 或 teardown 时抛出 `SuperClassError`，不修改其他生产逻辑。
2. 修改 `tests/test_testset.py`：
   - 将临时测试工程补成有效且可导入的父类层级，并清理测试工程模块缓存。
   - 保留现有测试集解析测试。
   - 增加 `superclses` 层级解析测试。
   - 增加父类缺失、继承关系错误、缺少 setup 和缺少 teardown 的异常测试。
3. 修改 `tests/test_runner.py`：
   - 复用现有示例测试的运行输出，验证正常生命周期顺序、执行次数及分支切换。
   - 增加多层父类 setup 失败场景，验证后代 setup 和用例的 `BLOCK` 结果及 teardown 顺序。
   - 扩展安装用例失败测试，验证中断时已启动父类按从内到外的顺序执行 teardown。
   - 复用现有临时工程和 `unittest`，不增加依赖或生产代码。
4. 更新 `tests/resources/logs`：
   - 使用从 `testproj` 最新一次执行结果中直接复制的完整日志目录覆盖测试资源。
   - 使用最新日志生成并更新 `report.ok.html`。
   - `TestReport.test_gen_report` 仅比较生成的报告内容与 `report.ok.html`，不再添加针对报告元素或统计值的独立断言。
5. 修改 `xbot/framework/statics/initdir/testcases/examples/nonpass/tc_eg_nonpass_fail_setup_with_failfast_false.py`：
   - 在示例类中恢复 `FAILFAST = False`。
   - 不修改其他示例或框架行为。
6. 执行 `tests.test_testset`、`tests.test_runner`、`tests.test_testcase`、`tests.test_report`、完整测试集及 `git diff --check`。

## 测试

1. 有效父类链解析：
   - 创建多层合法父类。
   - 确认 `superclses` 的目录映射和继承关系。
2. 父类定义校验：
   - 分别构造父类缺失、继承关系错误、缺少 setup、缺少 teardown 的场景。
   - 确认均抛出包含具体位置和原因的 `SuperClassError`。
3. 正常生命周期：
   - 运行多个同层及跨分支用例。
   - 确认 setup 从外到内、teardown 从内到外，每层只执行一次。
4. 父类 setup 失败：
   - 构造失败父类、子层父类和用例。
   - 确认失败父类、子层父类和用例的结果依次为 `FAIL`、`BLOCK`、`BLOCK`。
   - 确认相应 teardown 的状态和执行顺序。
5. 安装用例失败：
   - 确认后续安装及普通用例停止执行，输出包含中断提示。
   - 确认已启动父类仍按从内到外的顺序执行 teardown。
6. 报告资源：
   - 从 `testproj` 最新一次执行结果中直接复制完整日志目录到 `tests/resources/logs`。
   - 生成报告并与 `report.ok.html` 比较，确认内容一致。
7. 示例 `FAILFAST` 回归：
   - 实例化 `tc_eg_nonpass_fail_setup_with_failfast_false`，确认 `FAILFAST` 为 `False`。
   - 确认 setup 失败后测试步骤不执行、teardown 执行一次，最终结果为 `FAIL`。
8. 回归验证：
   - 运行目标测试和完整测试集，确认无意外跳过。
   - 执行 `git diff --check`。
