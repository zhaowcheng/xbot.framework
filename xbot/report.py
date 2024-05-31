# Copyright (c) 2022-2023, zhaowcheng <zhaowcheng@163.com>

"""
报告模块。
"""

import os
import re

from typing import Tuple
from datetime import datetime

from xbot import utils
from xbot import common


def find_value(html: str, id_: str) -> str:
    """
    通过 id 获取 html 元素的文本。

    :param html: html 内容。
    :param id_: 元素 id。
    :return: 元素的文本。
    """
    return re.search(r'id="%s".*>(.*)<.*' % id_, html).group(1)


def gen_report(logdir: str) -> Tuple[str, bool]:
    """
    生成报告。

    :param logdir: 日志目录。
    :return: (report_filepath, is_allpassed)
    """
    cases = []
    counter = {
        'PASS': 0,
        'FAIL': 0,
        'ERROR': 0,
        'TIMEOUT': 0,
        'SKIP': 0
    }
    report = os.path.join(logdir, 'report.html')
    allpassed = True
    for top, dirs, files in utils.ordered_walk(logdir):
        for f in files:
            # report.ok.html 是单元测试时用于对比生成的报告是否正确的文件。
            if f.endswith('.html') and f not in ['report.html', 'report.ok.html']:
                reltop = os.path.relpath(top, logdir)
                caselog = os.path.join(reltop, f).replace('\\', '/')
                casepath = caselog.replace('.html', '.py')
                with open(os.path.join(top, f), encoding='utf8') as fp:
                    content = fp.read()
                    result = find_value(content, 'result')
                    if result not in counter:
                        raise ValueError(f'Unknown result: {result}: {os.path.join(top, f)}')
                    if result not in ['PASS', 'SKIP']:
                        allpassed = False
                    counter[result] += 1
                    caseinfo = {
                        'result': result,
                        'path': casepath,
                        'log': caselog,
                        'starttime': find_value(content, 'starttime'),
                        'endtime': find_value(content, 'endtime'),
                        'duration': find_value(content, 'duration')
                    }
                    cases.append(caseinfo)
    cases.sort(key=lambda x: (x['starttime'], x['path']))
    strptime = lambda t: datetime.strptime(t, '%Y-%m-%d %H:%M:%S')
    total_duration = str(
        strptime(cases[-1]['endtime']) - strptime(cases[0]['starttime'])
    )
    utils.render_write(
        common.REPORT_TEMPLATE,
        report,
        passcnt=counter['PASS'],
        failcnt=counter['FAIL'],
        errorcnt=counter['ERROR'],
        timeoutcnt=counter['TIMEOUT'],
        skipcnt=counter['SKIP'],
        allcnt=sum(counter.values()),
        total_duration=total_duration,
        cases=cases
    )
    return report, allpassed
