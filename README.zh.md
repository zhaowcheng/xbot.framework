<p align="center">
  <br>中文 | <a href="README.md">English</a>
</p>

***

## 简介

xbot 是一个 `轻量`、`易用`、`可扩展` 的自动化测试框架。

## 安装

使用 pip 进行安装:

```
pip install xbot.framework
```

安装成功后即可调用 xbot 命令:

```
$ xbot --help
usage: xbot [-h] [-d DIRECTORY] [-b TESTBED] [-s TESTSET] [-f {verbose,brief}] [-v] {init,run}

positional arguments:
{init,run}

optional arguments:
-h, --help            show this help message and exit
-d DIRECTORY, --directory DIRECTORY
                        directory to init (required by `init` command)
-b TESTBED, --testbed TESTBED
                        testbed filepath (required by `run` command)
-s TESTSET, --testset TESTSET
                        testset filepath (required by `run` command)
-f {verbose,brief}, --outfmt {verbose,brief}
                        output format (option for `run` command, options: verbose/brief, default: brief)
-v, --version         show program's version number and exit
```

## 入门

初始化工程目录:

```
$ xbot init -d ./testproj
Initialized ./testproj
```

工程目录结构如下:

```
./testproj
├── README.md
├── lib  # 测试库目录
│   ├── __init__.py
│   ├── testbed.py  # 测试床基类
│   └── testcase.py  # 测试用例基类
├── requirements.txt
├── testbeds  # 测试床目录
│   └── testbed_example.yml 
├── testcases  # 测试用例目录
│   ├── __init__.py
│   └── examples
│       ├── __init__.py
│       ├── nonpass
│       │   ├── __init__.py
│       │   ├── tc_eg_nonpass_error_clsname.py
│       │   ├── tc_eg_nonpass_error_syntax.py
│       │   ├── tc_eg_nonpass_fail_setup_with_failfast_false.py
│       │   ├── tc_eg_nonpass_fail_setup_with_failfast_true.py
│       │   ├── tc_eg_nonpass_fail_step_with_failfast_false.py
│       │   ├── tc_eg_nonpass_fail_step_with_failfast_true.py
│       │   ├── tc_eg_nonpass_skip_excluded.py
│       │   ├── tc_eg_nonpass_skip_not_included.py
│       │   └── tc_eg_nonpass_timeout.py
│       └── pass
│           ├── __init__.py
│           ├── tc_eg_pass_create_dirs_and_files.py
│           └── tc_eg_pass_get_values_from_testbed.py
└── testsets  # 测试套目录
    └── testset_example.yml
```

测试床示例(`testbeds/testbed_example.yml`):

```yaml
# Testbed is used to store the information about the test environment.
# The information can be accessed by self.testbed.get() in the testcases.
example:
  key1: value1
  key2: 
    key2-1: value2-1
    key2-2: value2-2
  key3:
    - value3-1
    - value3-2
    - value3-3
  key4:
    - name: jack
      age: 20
    - name: tom
      age: 30
```

测试套示例(`testsets/testset_example.yml`):

```yaml
# Testset is used to organize testcases to be executed.
tags:  # `exclude` has higher priority than `include`.
  include:  # Include testcases with these tags.
    - tag1
  exclude:  # Exclude testcases with these tags.
    - tag2
paths:
  - testcases/examples/pass/tc_eg_pass_get_values_from_testbed.py
  - testcases/examples/pass/tc_eg_pass_create_dirs_and_files.py
  # Recursively include all testcases in the directory, 
  # only match files with the prefix 'tc_' and suffix '.py'.
  - testcases/examples/nonpass/
```

执行测试(测试工程目录下执行命令):

```
$ xbot run -b testbeds/testbed_example.yml -s testsets/testset_example.yml 
(1/11)   PASS     0:00:01  tc_eg_pass_get_values_from_testbed
(2/11)   PASS     0:00:01  tc_eg_pass_create_dirs_and_files
(3/11)   ERROR    0:00:00  tc_eg_nonpass_error_clsname
(4/11)   ERROR    0:00:00  tc_eg_nonpass_error_syntax
(5/11)   FAIL     0:00:01  tc_eg_nonpass_fail_setup_with_failfast_false
(6/11)   FAIL     0:00:01  tc_eg_nonpass_fail_setup_with_failfast_true
(7/11)   FAIL     0:00:01  tc_eg_nonpass_fail_step_with_failfast_false
(8/11)   FAIL     0:00:01  tc_eg_nonpass_fail_step_with_failfast_true
(9/11)   SKIP     0:00:00  tc_eg_nonpass_skip_excluded
(10/11)  SKIP     0:00:00  tc_eg_nonpass_skip_not_included
(11/11)  TIMEOUT  0:00:03  tc_eg_nonpass_timeout

report: /Users/wan/CodeProjects/xbot.framework/testproj/logs/testbed_example/2024-07-02_12-19-43/report.html 
```

执行完成后会在测试工程下根据测试床名称和时间戳生成日志目录保存 html 格式的用例日志和测试报告。

测试报告:

![report_example](https://github.com/zhaowcheng/xbot.framework/blob/master/xbot/framework/statics/report_example.png?raw=True)

用例日志:

![log_example](https://github.com/zhaowcheng/xbot.framework/blob/master/xbot/framework/statics/log_example.png?raw=True)

## 用例开发

测试用例存放在工程目录的 `testcases` 子目录下，以下为 `testcases/examples/pass/tc_eg_pass_create_dirs_and_files.py` 用例内容:

```python
import os
import tempfile
import shutil

from xbot.framework.utils import assertx
from lib.testcase import TestCase


class tc_eg_pass_create_dirs_and_files(TestCase):
    """
    Test creating directories and files.
    """
    TIMEOUT = 60
    FAILFAST = True
    TAGS = ['tag1']

    def setup(self):
        """
        Prepare test environment.
        """
        self.workdir = tempfile.mkdtemp()
        self.info('Created workdir: %s', self.workdir)

    def step1(self):
        """
        Create a subdirectory 'dir' under the temporary working directory and check if it is created successfully.
        """
        self.dir1 = os.path.join(self.workdir, 'dir1')
        os.mkdir(self.dir1)
        assertx(os.path.exists(self.dir1), '==', True)

    def step2(self):
        """
        Create an empty file 'file1' under 'dir1' and check if it is created successfully.
        """
        self.file1 = os.path.join(self.dir1, 'file1')
        open(self.file1, 'w').close()
        assertx(os.path.exists(self.file1), '==', True)

    def step3(self):
        """
        Write 'hello world' to 'file1' and check if it is written successfully.
        """
        with open(self.file1, 'w') as f:
            f.write('hello world')
        with open(self.file1, 'r') as f:
            assertx(f.read(), '==', 'hello world')

    def teardown(self):
        """
        Clean up test environment.
        """
        shutil.rmtree(self.workdir)
        self.info('Removed workdir: %s', self.workdir)
        self.sleep(1)
```

- 用例 `必须` 继承自 TestCase 基类；
- 用例 `必须` 在 setup 方法内实现预置步骤，如无具体步骤则写 pass；
- 用例 `必须` 在 teardown 方法内实现清理步骤，如无具体步骤则写 pass；
- 测试步骤以 `step1, step2, ...` 这样的方式命名，末尾数字为执行顺序；
- `TIMEOUT` 属性定义测试用例最大执行时长(单位：`秒`)，超过该时长将被强制结束且置结果为 TIMEOUT；
- `FAILFAST` 属性为 *True* 时，当某个测试步骤失败时，则会跳过后续测试步骤立即执行清理步骤；
- `TAGS` 属性定义用例 *标签*，可用于测试套中对待执行测试用例列表进行筛选；


## 测试库开发

测试库存放在工程目录的 `lib` 子目录下，根据业务开发所需测试库放入该目录下，然后在测试用例中导入使用即可。

## 插件

| Name                                                               | Description                           |
|--------------------------------------------------------------------|---------------------------------------|
| [xbot.plugins.ssh](https://github.com/zhaowcheng/xbot.plugins.ssh) | SSH library for xbot.framework        |
| xbot.plugins.http(`planning`)                                      | HTTP library for xbot.framework       |
| xbot.plugins.wui(`planning`)                                       | WebUI library for xbot.framework      |
| xbot.plugins.gui(`planning`)                                       | GUI library for xbot.framework        |
| xbot.plugins.pgsql(`planning`)                                     | PostgreSQL library for xbot.framework |
