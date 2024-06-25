# Copyright (c) 2022-2023, zhaowcheng <zhaowcheng@163.com>

"""
Execution report.
"""

import os
import re

from typing import Tuple
from datetime import datetime

from xbot.framework import utils
from xbot.framework import common


def find_value(html: str, id_: str) -> str:
    """
    Get text of a element by id from html.

    :param html: html content.
    :param id_: element id.
    :return: text of element.
    """
    return re.search(r'id="%s".*>(.*)<.*' % id_, html).group(1)


def gen_report(logdir: str) -> Tuple[str, bool]:
    """
    Generate report for all testcase logfiles in `logdir`.

    :param logdir: testcase logfile directory.
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
            # report.ok.html is only for unittest.
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
