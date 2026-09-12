---
name: xbot-framework-readme-update
description: 根据当前代码、新初始化的 testproj 和真实运行结果，同步 xbot.framework 的 README.md 与 README.zh.md。默认只更新已有内容，不新增章节，不自动截图。
---

# xbot.framework README 更新

1. 在 `xbot.framework` 根目录检查暂存、未暂存差异和相关代码变化，保留用户已有修改及暂存状态。

2. 获取干净基准：
   - 若删除现有 `testproj` 尚未得到授权，先询问用户。
   - 初始化前暂时移走 `xbot/framework/statics/initdir` 下残留的 `logs` 和 `__pycache__`，完成后原样恢复。
   - 删除并重新初始化：

     ```bash
     xbot init -d ./testproj
     ```

   - 在运行测试前记录目录树，避免把新产生的 `logs` 和 `__pycache__` 写入 README。

3. 在 `testproj` 中真实执行：

   ```bash
   cd testproj
   xbot run \
       -b testbeds/testbed_example.yml \
       -s testsets/testset_example.yml
   ```

   示例包含预期的非通过用例，退出码非零不等于执行异常。

4. 同步两份 README 的已有内容：
   - 目录结构以运行前的新 `testproj` 为准。
   - TestBed 和 TestSet YAML 直接复制自 `testproj`。
   - 示例用例直接复制自 `testproj/testcases/examples/pass/tc_eg_pass_create_dirs_and_files.py`。
   - 运行示例使用本次真实终态输出，去掉被回车覆盖的 `RUNNING` 行。
   - 命令、数量、结果、路径和已有说明随实际变化更新。
   - 不新增章节；如有必要，只向用户提出建议。

5. 截图由用户手动完成。向用户提供本次生成的：
   - `report.html`
   - `tc_eg_pass_create_dirs_and_files.html`

6. 验证：
   - README 中的 YAML 和示例用例与 `testproj` 源文件逐字一致。
   - 运行示例与真实终态输出一致。
   - 报告统计与运行结果一致。
   - 两张截图宽度一致。
   - 执行：

     ```bash
     git diff --check HEAD -- README.md README.zh.md
     ```

   - 确认没有修改无关内容或改变原有暂存状态。
