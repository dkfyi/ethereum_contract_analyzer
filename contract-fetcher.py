import json
import multiprocessing
import sys
import time

import psycopg2
import requests
from mythril.disassembler.disassembly import Disassembly
from psycopg2.extras import execute_values

# db structure: address block code hash funcs asm duplicated original
# parity --allow-ips=public --max-peers=256 --max-pending-peers=256  --tracing on

def get_last_block():
    response = requests.post("http://127.0.0.1:8545",
                                json={"id": "0", "jsonrpc": "2.0", "method": "eth_blockNumber",
                                    "params": []}).json()["result"]

    return int(response, 0)

def decode(code):
    dis = Disassembly(code)
    asm = dis.get_easm()
    tmp = dict()
    for line in asm.splitlines():
        lst = line.split()
        tmp[lst[0]] = ' '.join(lst[1:])
    return (json.dumps(dis.address_to_function_name), json.dumps(tmp))

def fetch_block(blockNumber):
    result = []

    if blockNumber > 7280067:
        return result
    response = requests.post("http://127.0.0.1:8545",
                                json={"id": "0", "jsonrpc": "2.0", "method": "trace_block",
                                    "params": [hex(blockNumber)]}).json()["result"]

    for trace in response:
        if trace["type"] == "create":
            if "result" in trace and "address" in trace["result"]:
                if check_tx(trace["transactionHash"], response):
                    transactionHash = trace["transactionHash"]
                    address = trace["result"]["address"]
                    code = trace["result"]["code"]
                    funcs, asm = decode(code)
                    result.append([address, blockNumber, code, transactionHash, funcs, asm, None, None])

    return result

try:
    conn = psycopg2.connect("dbname='postgres' user='postgres' host='localhost' password='password'")
    cur = conn.cursor()
except:
    print("Unexpected error:", sys.exc_info()[0])


def check_tx(txHash, blockTrace):
    return not any([(trace["transactionHash"] == txHash and "error" in trace) for trace in blockTrace])


def check_duplicated(code):
    cur.execute("SELECT address FROM unique_contracts WHERE DECODE(MD5(code), 'HEX') = DECODE(MD5(%s), 'HEX') AND code=%s;", (code, code))
    record = cur.fetchone()
    if record:
        return True, record
    else:
        return False, ''

def get_total_contracts():
    cur.execute("SELECT COUNT(*) FROM test;")
    totalContracts = cur.fetchone()[0]
    if not totalContracts:
        return 0
    else:
        return int(totalContracts)

def get_last_processed_block():
    cur.execute("SELECT MAX(block) FROM test;")
    currentBlock = cur.fetchone()[0]
    if not currentBlock:
        return 47205 # first block with contract
    else:
        return int(currentBlock) + 1



totalContracts = get_total_contracts()
currentBlock = get_last_processed_block()

while True:
    if get_last_block() == currentBlock:
        time.sleep(1)
        continue

    print("processing block {}".format(currentBlock))

    with multiprocessing.Pool(processes=12) as pool:
        results = pool.map(fetch_block, range(currentBlock, currentBlock + 1000))

    for result in results:
        currentBlock += 1
        for record in result:
            isDuplicated, original = check_duplicated(record[2])
           
            record[-1] = original
            record[-2] = isDuplicated
            cur.execute("INSERT INTO test (address, block, code, hash, funcs, asm, duplicated, original) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                               tuple(record))
            if not isDuplicated:
                cur.execute("INSERT INTO unique_contracts (address, code) VALUES (%s, %s)", (record[0], record[2]))
            totalContracts += 1
    conn.commit()

    print("total contracts: {}".format(totalContracts))

cur.close()
conn.close()
