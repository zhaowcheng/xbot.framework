# Copyright (c) 2022-2023, zhaowcheng <zhaowcheng@163.com>

"""
用例执行报告相关模块。
"""

import os
import bisect

from typing import Tuple
from datetime import datetime
from bs4 import BeautifulSoup

from lib import util
from lib import common


def gen_report(logdir: str) -> Tuple[str, bool]:
    """
    生成报告。

    :param logdir: 日志目录。
    :return: (报告文件路径, 是否全 PASS)。
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
    for top, dirs, files in os.walk(logdir):
        for f in files:
            if f.endswith('.html'):
                reltop = os.path.relpath(top, logdir)
                caselog = os.path.join(reltop, f).replace('\\', '/')
                casepath = 'testcase/' + caselog.replace('.html', '.py')
                with open(os.path.join(top, f)) as fp:
                    soup = BeautifulSoup(fp.read(), 'html.parser')
                    result = soup.find(id="result").text
                    if result != 'PASS':
                        allpassed = False
                    counter[result] += 1
                    caseinfo = {
                        'result': result,
                        'path': casepath,
                        'log': caselog,
                        'starttime': soup.find(id="starttime").text,
                        'endtime': soup.find(id="endtime").text,
                        'duration': soup.find(id="duration").text,
                    }
                    bisect.insort(cases, caseinfo, 
                                  key=lambda x: x['starttime'])
    strptime = lambda t: datetime.strptime(t, '%Y-%m-%d %H:%M:%S')
    total_duration = str(
        strptime(cases[-1]['endtime']) - strptime(cases[0]['starttime'])
    )
    util.render_write(
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
