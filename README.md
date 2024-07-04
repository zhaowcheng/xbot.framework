<p align="center">
  <br>English | <a href="README.zh.md">中文</a>
</p>

***

## Introduction

xbot is a `lightweight`, `easy-to-use`, and `extensible` test automation framework.

## Installation

Install xbot via pip:

```
pip install xbot.framework
```

Type `xbot --help` to check:

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


## Getting Started

Initialize a test project:

```
$ xbot init -d ./testproj
Initialized ./testproj
```

The test project directory structure:

```
./testproj
├── README.md
├── lib  # test libraries
│   ├── __init__.py
│   ├── testbed.py  # testbed base
│   └── testcase.py  # testcase base
├── requirements.txt
├── testbeds  # directory storing testbeds
│   └── testbed_example.yml 
├── testcases  # directory storing testcases
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
└── testsets  # directory storing testsets
    └── testset_example.yml
```

Testbed example(`testbeds/testbed_example.yml`):

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

Testset example(`testsets/testset_example.yml`):

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

Run the testcases(must execute under the test project directory):

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

Test report and logs will be generated in the `logs` subdirectory.

Example report:

![report_example](https://github.com/zhaowcheng/xbot.framework/blob/master/xbot/framework/statics/report_example.png?raw=True)

Example log:

![log_example](https://github.com/zhaowcheng/xbot.framework/blob/master/xbot/framework/statics/log_example.png?raw=True)


## Testcase Development

Testcases are stored in the `testcases` subdirectory, below is a example(`testcases/examples/pass/tc_eg_pass_create_dirs_and_files.py`):

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

- Testcase `MUST` inherit from the `TestCase` base class;
- Testcase `MUST` implement the preset steps in the setup method, write pass if there are no specific steps;
- Testcase `MUST` implement the cleanup steps in the teardown method, write pass if there are no specific steps;
- Test steps are named in the form of `step1, step2, ...`, the number at the end is the execution order;
- The `TIMEOUT` attribute defines the maximum execution time of the testcase(unit: `seconds`), the testcase will be forced to end and the result will be set to TIMEOUT if it exceeds the time limit;
- When `FAILFAST` attribute is *True*, the subsequent test steps will be skipped and the teardown will be executed immediately if a test step fails;
- The `TAGS` attribute defines the testcase *tags*, which can be used to filter testcases to be executed in the testset;

## Test libraries development

Test libraries are stored in the `lib` subdirectory, write the test libraries according to the business requirements, import and use them in the testcases.

## Plugins

| Name                                                               | Description                           |
|--------------------------------------------------------------------|---------------------------------------|
| [xbot.plugins.ssh](https://github.com/zhaowcheng/xbot.plugins.ssh) | SSH library for xbot.framework        |
| xbot.plugins.http(`planning`)                                      | HTTP library for xbot.framework       |
| xbot.plugins.wui(`planning`)                                       | WebUI library for xbot.framework      |
| xbot.plugins.gui(`planning`)                                       | GUI library for xbot.framework        |
| xbot.plugins.pgsql(`planning`)                                     | PostgreSQL library for xbot.framework |
