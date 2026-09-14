# AGENTS.md

## 适用范围

- 本文件适用于整个 `xbot.framework` 仓库。
- 这是 `/Users/zhaowcheng/Code/xbot` 下的嵌套 Git 仓库；Git、测试和构建命令必须在本仓库根目录执行。
- 修改前先检查工作区状态，保留用户已有的暂存和未暂存改动。

## 项目结构

- `xbot/framework/`：框架实现。
- `xbot/framework/statics/`：HTML 模板、图片和 `xbot init` 使用的初始工程模板。
- `tests/`：基于标准库 `unittest` 的测试。
- `tests/resources/`：测试使用的报告等快照。
- `README.md`、`README.zh.md`：英文和中文文档。
- `testproj/`、`dist/`、`*.egg-info/`：生成内容，不作为源码直接维护。

## 修改原则

- 修复问题时先定位共同根因并检查所有调用方，避免只修复单一路径。
- 保持现有公开 API、`xbot` 命令行参数、配置格式和执行顺序；需求明确要求变更时除外。
- 不手工修改生成目录来代替修改源文件。

## 测试约定

- 支持 Python 3.10 及以上版本。
- 测试沿用 `unittest` 和现有测试风格，不为单个改动引入新测试框架。

## 生成基准 testproj

更新报告快照或 README 时，使用当前代码重新初始化 `testproj`：

1. 若需要删除已有 `testproj`，先获得用户授权。
2. 初始化前暂时移走 `xbot/framework/statics/initdir/` 中残留的 `logs/` 和 `__pycache__/`，完成后原样恢复。
3. 在仓库根目录执行：

   ```sh
   xbot init -d ./testproj
   ```

4. 在运行示例前记录目录树，避免把随后生成的 `logs/` 和 `__pycache__/` 当作初始工程内容。
5. 在 `testproj/` 中执行：

   ```sh
   xbot run \
       -b testbeds/testbed_example.yml \
       -s testsets/testset_example.yml
   ```

示例包含预期的非通过用例，命令退出码非零不等于执行异常。

## 报告和日志快照

当报告的内容或样式发生变化时：

1. 按上一节使用当前代码初始化 `testproj` 并运行示例用例。
2. 用本次最新日志目录中的全部内容替换 `tests/resources/logs/` 中的旧快照，保留 `.gitignore`。
3. 将复制后的 `report.html` 重命名为 `report.ok.html`。
4. 执行以下测试，确保新生成的报告与快照一致：

   ```sh
   ../venv/bin/python tests/test_report.py
   ```

## README 自动更新

修改影响 README 中已有的 CLI、初始化工程结构、TestBed/TestSet 配置、示例用例、运行输出、结果数量、报告路径或用户说明时，自动同步更新 `README.md` 和 `README.zh.md`，无需等待用户再次要求。

更新规则：

- 默认只更新已有内容，不新增章节；如确有必要，只向用户提出建议。
- 使用上一节流程得到的全新 `testproj` 和真实运行结果作为唯一基准。
- 目录结构使用运行示例前记录的 `testproj`。
- TestBed 和 TestSet YAML 直接复制自 `testproj`。
- 示例用例直接复制自 `testproj/testcases/examples/pass/tc_eg_pass_create_dirs_and_files.py`。
- 运行示例使用本次真实终态输出，去掉被回车覆盖的 `RUNNING` 行。
- 两份 README 的结构、示例和语义保持一致。
- 截图不自动更新；向用户提供本次生成的 `report.html` 和 `tc_eg_pass_create_dirs_and_files.html`，由用户手动截图。

验证 README 时确认：

- README 中的 YAML 和示例用例与 `testproj` 源文件逐字一致。
- 运行示例与真实终态输出一致，报告统计与运行结果一致。
- 两张新截图的宽度一致。
- 没有修改无关内容或改变原有暂存状态。
- 执行：

  ```sh
  git diff --check HEAD -- README.md README.zh.md
  ```

## 验证

优先运行受影响的测试模块，例如：

```sh
../venv/bin/python -m unittest tests.test_report
```

提交结果前运行完整测试和差异检查：

```sh
../venv/bin/python -m unittest
git diff --check
```

若修改了 CLI、初始化模板或报告页面，再执行对应的真实命令或页面交互验证。无法在当前环境完成的验证必须明确说明，不得把静态检查描述为运行时验证。
