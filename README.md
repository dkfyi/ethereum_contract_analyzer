# ethereum_contract_analyzer

## Overview
This application scans Ethereum contracts in real-time, finds similar and unique ones, predicts vulnerabilities.


## Dependencies
* `psycopg2`
* `sklearn`
* `mythril`
* `pandas`
* `matplotlib`
* `numpy`
* `scikitplot`

This application was tested with Python 3.6
## Setup
* PostgreSQL
* clone https://github.com/paritytech/parity-ethereum and build `parity`
* run `parity --allow-ips=public --max-peers=256 --max-pending-peers=256  --tracing on` 

## Usage
* run `python3 contract_fetcher.py` 
* run `python3 predictor.py` to test perceptron and show ROC-curves
* run `python3 graph_generator.py`
