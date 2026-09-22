# AGENTS.md

本项目是一个基础的自动化测试框架，可在此基础上为指定项目开发专用的自动化测试框架。

## 术语表

| **术语** | **说明** |
| ------- | -------- |
| 测试床（testbed）| 环境信息声明文件 |
| 测试套（testset）| 待执行用例声明文件 |

## 项目结构

```
.
├── docs
│   └── tasks/  # AGENT 开发任务记录文档。
├── tests
│   ├── resources
│   │   └── logs/  # 用于测试报告生成函数的日志。
│   ├── run.py  # 执行所有测试的脚本。
└── xbot
    └── framework
        ├── common.py   # 全局变量定义。
        ├── errors.py   # 异常类定义。
        ├── logger.py   # 用例执行日志处理。
        ├── main.py     # 入口脚本。
        ├── report.py   # 报告生成和处理。
        ├── runner.py   # 用例执行。
        ├── statics  
        │   ├── initdir/               # 用于初始化新项目的模板。
        │   ├── log_example.png        # 用例日志示例截图。
        │   ├── log_template.html      # 用例日志模板。
        │   ├── report_example.png     # 测试报告示例截图。
        │   └── report_template.html   # 测试报告模板。
        ├── testbed.py   # 测试床解析管理。
        ├── testcase.py  # 测试用例基类。
        ├── testset.py   # 测试套解析管理。
        ├── utils.py     # 实用函数。
        └── version.py   # 版本号。
```