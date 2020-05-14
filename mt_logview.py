#!/usr/bin/env python

#-*- coding:utf-8 -*-

"""
# general Info :
* name : mt_logview.py
* Purpose :  Analyze log of multitalk on a mt client

# History
* 2020.05.08, kyung, version 0.1, init

# RFP
* 도구없이 기본적 확인은 가능해야 한다 -> cat, grep
* 최대한 SW 설치 없이 동작해야 한다 -> pyhon 3.7 ok
* 추가 SW 설치시 통계정보를 제공할 수 있어야 한다. -> pandas, matplotlib, scikit, pandoc

# 사전준비
* Anaconda 설치(권고대로만 설치)
* run 'Anaconda Prompt' on Windows Menu

  conda update conda # -n base -c defaults conda
  conda create -n venv python=3.7
  conda activate venvconda 
  conda install tabulate
  conda install matplotlib
  conda install pandoc
  conda install -c conda-forge jupyterlab
  conda install -c conda-forge pylint
  conda env export > venv.yml

# Usage : on Anaconda power Shell Prompt
  
  type .\multitalk.log | python .\mt_logview.py
  pandoc .\report.md -f markdown -t html -o report.html -c pandoc.css -s --toc
  
# 제약사항
* 로그 중, 즉 초반과 뒤부분의 불완전한 로그믄 경고만 수행하며 완전형태인 A-G까지 구성된 로그만 통계로 사용
* Without warning automatically make & write some files, [1|2].png and report.*.

# misc
{
    "python.jediEnabled": false,
    "editor.fontSize": 11,
    "python.pythonPath": "C:\\Users\\kyung\\anaconda3\\envs\\venv\\python.exe",
    "terminal.integrated.shellArgs.windows": [
        "/K", 
        "C:\\Users\\kyung\\anaconda3\\Scripts\\activate.bat C:\\Users\\kyung\\anaconda3"
    ]
}

"""

import re
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
from datetime import datetime

def report_legend():
    legend = """
    
---
title: MultiTalk 로그 분석
date: 분석일시(%s)
---

# 1. 분석결과

MultiTalk의 Client 로그를 분석하고 통계를 도식화

## 범례

Job : A~H로 구분된 사용자의 1회 로그인 과정을 1개의 Job으로 식별하며, 1개의 job은 아래와 같은 step으로 구성된다.

* A : 사용자 정보 조회 
* B : 서버 접속 
* C : 서버 로그인 
* D : 플러그인 정보 추출
* E : 별칭 사용여부 조회 
* F : 사용자 별칭 조회
* G : 회의실 목록 표시
* H : 조직도 트리 표시

""" % (datetime.today().strftime('%Y-%m-%d %H:%M'))
    print(legend)
 
def main():
    regex = re.compile('ETIME|_START_|_END_|ERROR')
    regex_etime = re.compile('ETIME')
    regex_start = re.compile('_START_')
    
    df = pd.DataFrame(columns=['birth', 'job_num', 'step', 'elapsed'])
    job_num = 0;
    for line in sys.stdin:
        #line = line.decode('cp949').encode('utf8')
        line = line.replace(r'시작', '_START_')
        mo = regex.search(line)
        if mo != None:
            line = line.rstrip()
            line = line.replace('] [', ', ')
            line = line.replace('] ', ', ')
            line = line.replace('[', '')
            line = line.replace(' ', '')
            # DEBUG print('SRC: ', line)
            mo = regex_etime.search(line)
            if mo != None:
                data = []
                line = line.replace('ETIME:', 'ETIME,')
                m = re.split(',', line)
                #  0                          1        2                        3       4     5        6
                # ['2020-05-0715:47:25:590', 'DEBUG', 'MultiTalkGroupManager', 'ETIME', 'G', '18114', 'searchSortOrders'] 
                elapsed = float(m[5])/1000
                if m[4] == 'A' :
                    job_num = job_num + 1
                df = df.append({'birth': m[0], 'job_num': int(job_num), 'step': m[4], 'elapsed': elapsed}, ignore_index=True)
                    
    df['birth'] = pd.to_datetime(df['birth'], format="%Y-%m-%d%H:%M:%S:%f", errors='raise')
    df['job_num'] = pd.to_numeric(df['job_num'], downcast='integer')
    
    sys.stdout = open( 'report.md', 'w', encoding='utf8')
    report_legend()
    
    print('\n\n## 분석 대상 자료')
    print( '* 로그 시작시간 : ', df['birth'].min())
    print( '* 로그 종료시간 : ', df['birth'].max())
    print( '* 분석 job 수 : ', df['job_num'].max())
    
    # commmon
    font_path = 'C:/Windows/Fonts/NanumBarunGothic.ttf'
    fontprop = fm.FontProperties(fname=font_path, size=12)

    # 1. 시계열 분석
    by_time = df
    #by_time.plot(figsize=(11,4))
    by_time.plot(x='step', y='elapsed',figsize=(11,4))
    #plt.title('처리시간 그래프', fontproperties=fontprop)
    plt.xlabel('time(step)')
    plt.ylabel('elapsed time(sec)')
    plt.savefig('1.png')
    print('\n## 시계열 분석')
    print('\n![그림 1. 시간 경과에 따른 처리시간](./1.png){ width=100% }')
    
    # 2. step별 처리시간 그래프
    by_step = df.pivot(index='job_num', columns='step', values='elapsed')
    print('\n## 단계별 통계 분석') 
    print('* 각 단계의 job count, 평균, 편차, min, 25%, 50%, 75%, max값을 도출하여 처리시간 및 불안정 요소를 식별')
    print('* 중요도 : std > max\n')
    
    print('\n주요 점검사항\n')
    print('* 누락: count 수가 모두 같은가')
    print('* 불안정성 : std 중 큰 숫자 점검')
    print('* 최대시간소모 : max 중 가장 큰 숫자\n')
    print(': 표1. 각 단계별 통계분석\n')
    print(by_step.describe().to_markdown())
    
    print('\n## Job별 각 단계 처리시간 분석') 
    print('* 각 Job별 처리시간을 시계열로 도식함') 
    plt.figure(clear=True)
    plt.figure(figsize=(11,4))
    plt.plot(by_step.index, by_step['A'])
    plt.plot(by_step.index, by_step['B'])
    plt.plot(by_step.index, by_step['C'])
    plt.plot(by_step.index, by_step['D'], linestyle=':')
    plt.plot(by_step.index, by_step['E'])
    plt.plot(by_step.index, by_step['F'])
    plt.plot(by_step.index, by_step['G'])
    plt.plot(by_step.index, by_step['H'], linestyle='--')
    plt.title('각 단계별 소요시간', fontproperties=fontprop)
    plt.xlabel('step')
    plt.ylabel('elapsed(sec)')
    plt.legend(['A','B','C','D','E','F','G','H'])
    plt.savefig('2.png')
    print('\n![그림-2 위 그림의 상세값](./2.png){ width=100% }\n')
    
    print('* A~H : 단계별 처리시간')
    print('* sum : sum(A:H)')
    print('* start : 시작시간')
    print('* end : 종료시간')
    print('* lap : end-start(lap>sum)\n')
    
    # 2+1. job별 처리시간
    by_job = df.pivot(index='job_num', columns='step', values='birth')    
    by_step['sum'] = by_step[['A','B','C','D','E','F','G','H']].sum(axis=1)
    by_job['start'] = by_job[['A','B','C','D','E','F','G','H']].min(axis=1)
    by_job['end'] = by_job[['A','B','C','D','E','F','G','H']].max(axis=1)
    #by_step['sum'] = by_step[['A','B','C','D','E','F','G']].sum(axis=1)
    #by_job['start'] = by_job[['A','B','C','D','E','F','G']].min(axis=1)
    #by_job['end'] = by_job[['A','B','C','D','E','F','G']].max(axis=1)
    by_step['lap'] = by_job['end'] - by_job['start']
    print(': 표2. job별 각단계 소요시간\n')
    print(by_step.to_markdown())

    # 99. 부록
    print('\n# 2. 부록')
    #print('\n## 자료유형') 
    #print(df.dtypes.to_markdown())
    print(': 표3. 분석 세부자료\n')
    print(df.to_markdown())
    # close()
        
if __name__ == "__main__":
    main()
