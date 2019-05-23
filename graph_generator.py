import multiprocessing
import psycopg2
from mythril.disassembler.disassembly import Disassembly
from psycopg2.extras import execute_values
import json
import time
import sys

records = []
def get_edges(i):
    record = records[i]
    funcs = record[1]
    edges = dict()
    if len(funcs) != 0:
        for j in range(i+1, len(records)):
            check_record = records[j]
            intersect = get_intersect(funcs, check_record[1])
            if len(intersect) != 0:
                edges[check_record[0]] = intersect
    return edges

original_funcs = {}
def get_intersect(l, r):
    return (list(set(l).intersection(set(r))))

conn = psycopg2.connect(
    "dbname='postgres' user='postgres' host='localhost' password='password'")   
cur = conn.cursor()
cur.execute("SELECT COUNT(*) FROM unique_contracts WHERE NOT processed;")
remaining = cur.fetchone()[0]
cur.execute("SELECT address, funcs, processed FROM unique_contracts WHERE NOT processed;")

records = cur.fetchall()
count = 0

while True:
    with multiprocessing.Pool(processes=12) as pool:
        results = pool.map(get_edges, range(count, min(count + 100, len(records))))

    cur_count = 0
    updateTime = 0
    insertTime = 0
    edges_list = []
    for i in range(count, min(count + 100, len(records))):
        record = records[i]
        address = record[0]
        edges = results[cur_count]
        cur_count += 1
        edges_list.append((json.dumps(edges), address))

        cur.execute("UPDATE unique_contracts SET processed=%s WHERE address=%s;", (True, address))
    execute_values(cur, "INSERT INTO contracts_intersect (edges, address) (VALUES %s);", edges_list)
    conn.commit()
    
    count += cur_count
    print(remaining - count)
