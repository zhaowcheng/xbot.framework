# Copyright (c) 2022-2023, zhaowcheng <zhaowcheng@163.com>

"""
Report module.
"""

import os
import re
import bisect

from datetime import datetime

from xbot import util
from xbot import common


def find_value(content, key):
    """
    Find value in html logfile by key.

    :param data: html logfile content.
    :param key: key.
    :return: value.
    """
    return re.search(r'id="%s".*>(.*)<.*' % key, content).group(1)


def gen_report(logdir):
    """
    Generate report.

    :param logdir: log directory.
    :return: (report_filepath, is_allpassed)。
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
                    content = fp.read()
                    result = find_value(content, 'result')
                    if result != 'PASS':
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
                    bisect.insort(cases, caseinfo, key=lambda x: x['starttime'])
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
