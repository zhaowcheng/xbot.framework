# Pin framework version on init

## 需求

1. `xbot init -d <dir>` 生成的项目中，`requirements.txt` 里的 `xbot.framework` 依赖必须带上下界版本范围，避免新项目被后续不兼容的大版本自动升级。
2. 版本范围按当前框架版本 `x.y.z` 动态计算：下界为主版本 `x`，上界为 `x+1`。以当前 1.0.0 为例，生成文件内容为：
   ```
   xbot.framework>=1,<2; python_version >= '3.10'
   ```
3. 版本号来源为运行中框架的版本号（`xbot.framework.version.__version__`），随发布自动变化，无需人工同步。
4. 保留 `python_version >= '3.10'` 环境标记，其内容与模板保持一致。
5. 模板文件 `xbot/framework/statics/initdir/requirements.txt` 保持现状，不因本需求修改其内容；模板目录单独使用时仍然有效。
6. 版本号形如预发布（如 `1.0.0rc1`、`2.1.0.dev1`）时，仍按主版本加一取上界。
7. 仅影响 `xbot init` 新生成的项目；`xbot run` 行为、依赖解析方式、初始化目录结构均不变。
8. 非目标：不处理已存在项目的 `requirements.txt`；不引入版本锁定、哈希校验或额外运行时依赖。

## 实现

1. 修改 `xbot/framework/main.py` 的 `init()`：在 `shutil.copytree(INIT_DIR, directory)` 之后追加 7 行，不加新函数、不加新 import。
   - 由 `int(__version__.split('.')[0])` 取主版本，拼出 `xbot.framework>=%d,<%d`（major，major + 1）。
   - 以 utf8 读取生成目录下的 `requirements.txt`，用 `str.replace('xbot.framework', specifier, 1)` 只替换首次出现的依赖名后写回，环境标记和行尾换行原样保留。
   - 已知取舍：依赖模板首个 `xbot.framework` 字样即依赖名；若将来在模板依赖行之前加入含该字样的注释行会被误替换。
2. `xbot/framework/statics/initdir/requirements.txt` 保持现状：仍为 `xbot.framework; python_version >= '3.10'`。
3. 修改 `tests/test_main.py`：
   - `samedir()` 增加可选参数 `ignore: list[str] | None = None`，透传给 `filecmp.dircmp`，递归调用时同样透传。
   - `test_init()` 的目录比对排除 `requirements.txt`，并断言生成文件的依赖行等于按 `__version__` 计算出的 `xbot.framework>={major},<{major+1}; python_version >= '3.10'\n`，同时断言模板文件未被改动。
   - 新增用例：patch `xbot.framework.main.INIT_DIR` 为临时模板目录，其 `requirements.txt` 在框架依赖行之外另有一行其他依赖，断言初始化后其他依赖行保留、框架依赖行被限定。
4. 文档：`README.md`、`README.zh.md` 仅在目录树中列出 `requirements.txt` 文件名、不展示内容，本次行为变化不影响文档描述，不做修改。
5. 验证方式：`../venv/bin/python -m unittest` 全量通过，并执行 `git diff --check`。

## 测试

复用现有 `unittest` 框架与 `tests/test_main.py`，不引入新依赖。

1. T1 生成的依赖被限定（正常）：
   - 场景：初始化新项目后检查框架依赖的版本范围。
   - 前置：临时目录不存在，当前版本为 `__version__`（1.0.0）。
   - 操作：调用 `main.init(tmpdir)`，读取 `<tmpdir>/requirements.txt`。
   - 预期：内容恰为 `xbot.framework>={major},<{major+1}; python_version >= '3.10'\n`，major 由 `__version__.split('.')[0]` 动态计算，无多余内容或空行。
2. T2 其余初始化内容不变（回归）：
   - 场景：确认除依赖限定外初始化行为未变。
   - 前置：同 T1。
   - 操作：递归比对 `<tmpdir>` 与 `INIT_DIR`，忽略 `requirements.txt`。
   - 预期：无多余、无缺失、无内容不同的文件，子目录同样一致。
3. T3 模板文件保持原样（回归）：
   - 场景：确认初始化过程不修改包内模板。
   - 前置：调用 `main.init` 前读取 `INIT_DIR/requirements.txt`。
   - 操作：调用 `main.init(tmpdir)`。
   - 预期：模板内容仍为 `xbot.framework; python_version >= '3.10'\n`。
4. T4 其他依赖行不受影响（边界）：
   - 场景：模板中除框架依赖外还有其他依赖行。
   - 前置：patch `xbot.framework.main.INIT_DIR` 指向临时模板目录，其 `requirements.txt` 为 `jinja2\nxbot.framework; python_version >= '3.10'\njmespath\n`。
   - 操作：调用 `main.init(tmpdir)`，读取生成文件。
   - 预期：内容为 `jinja2\nxbot.framework>=1,<2; python_version >= '3.10'\njmespath\n`，其他依赖行与顺序原样保留。
5. T5 目标目录已存在（异常，保留现有断言）：
   - 场景：初始化一个已存在的目录。
   - 前置：临时目录已存在。
   - 操作：调用 `main.init(tmpdir)`。
   - 预期：仍以退出码 1 报 `... already exists`，不写入或覆盖任何文件。
6. T6 全量回归（集成）：
   - 场景：确认改动未影响其他模块。
   - 前置：`/Users/zhaowcheng/Code/xbot/xbot.framework` 工作区。
   - 操作：执行 `../venv/bin/python -m unittest`，并执行 `git diff --check`。
   - 预期：全部用例通过，无目标用例被跳过或被过滤条件排除，无空白/格式错误。
7. 不在覆盖范围：真实 `pip install` 安装生成的 `requirements.txt`（需联网解析）；预发布版本号场景按要求不单独覆盖。
