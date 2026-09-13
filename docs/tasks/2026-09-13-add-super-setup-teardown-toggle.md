# Add Super Setup Teardown Toggle

## 需求

- 测试报告筛选区增加一个按钮，统一显示或隐藏 super setup 和 super teardown 行。
- 默认保持现有行为：这些行可见；按钮文字随状态切换为 `HIDE SUPER SETUPS/TEARDOWNS` 或 `SHOW SUPER SETUPS/TEARDOWNS`。
- 点击 `ALL/PASS/FAIL/ERROR/TIMEOUT/BLOCK/SKIP` 后，仍保持用户选择的显示/隐藏状态。
- 不改变测试结果统计、报告生成规则及普通测试用例筛选行为。

## 实现

1. 修改 `xbot/framework/statics/report_template.html`：
   - 增加默认值为“显示”的 super 行状态。
   - 增加切换函数，同时控制 `.setup` 和 `.teardown` 行。
   - 调整 `filterCase()`，先处理 super 行状态，再处理普通用例的结果筛选。
   - 在现有筛选区添加按钮并复用现有按钮样式；按钮文字随状态变化。
2. 更新 `tests/resources/logs/report.ok.html`，使期望报告与模板输出一致。
3. 在 `tests/test_report.py` 中补充针对按钮、默认状态及筛选组合逻辑的断言，不增加浏览器或第三方依赖。

不修改 `report.py`、统计规则或报告数据结构。

## 测试

1. 报告生成回归
   - 前置条件：使用现有 `tests/resources/logs`。
   - 操作：调用 `gen_report()`。
   - 预期结果：生成内容与更新后的 `report.ok.html` 一致；用例数量、状态统计及普通筛选结构不变。
2. 默认状态
   - 前置条件：打开包含 super setup/teardown 行的报告。
   - 操作：不点击按钮。
   - 预期结果：两类 super 行均可见，按钮显示 `HIDE SUPER SETUPS/TEARDOWNS`。
3. 隐藏与恢复
   - 前置条件：报告包含 super setup/teardown 行和普通用例行。
   - 操作：点击按钮隐藏，再次点击恢复。
   - 预期结果：setup 和 teardown 行同时隐藏、同时恢复；普通用例行不受影响；按钮文字同步切换。
4. 与结果筛选组合
   - 前置条件：报告包含多种结果的普通用例以及 super setup/teardown 行。
   - 操作：隐藏 super 行后依次点击现有结果筛选按钮，再恢复显示并重复筛选。
   - 预期结果：隐藏状态不会被结果筛选重置；显示状态下 super 行保持现有的始终可见行为；普通用例仍按结果正确筛选。

自动化测试使用现有 `unittest` 检查生成结果、按钮及脚本结构；交互行为使用生成的本地报告在浏览器中验证，不引入浏览器测试依赖。
