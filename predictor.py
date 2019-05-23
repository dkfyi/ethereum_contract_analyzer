import csv
from sklearn.cluster import KMeans
from sklearn.linear_model import Perceptron
from sklearn.neural_network import MLPClassifier
import os
import operator
import numpy as np
from sklearn.externals import joblib
import scikitplot as skplt
import matplotlib.pyplot as plt
from sklearn.metrics import accuracy_score
is_vuln_presented = [0, 1, 0, 0, 1, 1, 1, 1, 0, 0, 1, 1, 1, 1, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0]

def load_vuln():
    vuln = {}
    
    with open("data/table.txt", "r") as input:
        reader = csv.DictReader(input)

        for row in reader:
            vals = list(row.values())
            vuln[vals[0]] = []
            tmp = vals[1:]
            for i in range(len(tmp)):
                if is_vuln_presented[i] == 1:
                    vuln[vals[0]].append(tmp[i])
    
    return vuln

def load_funcs_ids(target_count):
    funcs_id = {}
    cur_id = 0
    with open("data/funcs-stats.txt", "r") as stats:
        for line in stats:
            vals = line.split(":")
            sign = vals[0].strip()
            count = int(vals[1].strip())
            if count == target_count:
                break
            
            funcs_id[sign] = cur_id
            cur_id += 1
    return funcs_id

vuln = load_vuln()
funcs_ids = load_funcs_ids(19)

files = os.listdir("./data/funcs")

if not os.path.exists("./saved_model_perc.pkl"):
    address_to_funcs_ids = {}

    for i in range(0, int(len(files) / 2)):
        filename = files[i]
        address = filename.split(".")[0].strip()
        current_funcs_ids = [0 for _ in range(len(funcs_ids))]
        with open("./data/funcs/" + filename, "r") as input:
            for line in input:
                sign = line.strip()

                if sign in funcs_ids:
                    current_funcs_ids[funcs_ids[sign]] = 1
        
        if any(i == 1 for i in current_funcs_ids):
            address_to_funcs_ids[address] = current_funcs_ids

    X = []
    Y = {i:[] for i in range(11)}

    for address in address_to_funcs_ids.keys():
        if address in vuln:
            X.append(address_to_funcs_ids[address])
            
            for i in range(len(vuln[address])):
                Y[i].append(vuln[address][i])

    percs = []
    for i in range(11):
        percs.append(Perceptron(random_state=0).fit(X, Y[i]))

    joblib.dump(percs, 'saved_model.pkl')
else:
    percs = joblib.load('saved_model_perc.pkl')


address_to_funcs_ids_target = {}
for i in range(int(len(files)/2) + 1, len(files)):
    filename = files[i]
    address = filename.split(".")[0].strip()
    current_funcs_ids = [0 for _ in range(len(funcs_ids))]
    with open("./funcs/" + filename, "r") as input:
        for line in input:
            sign = line.strip()

            if sign in funcs_ids:
                current_funcs_ids[funcs_ids[sign]] = 1
    
    if any(i == 1 for i in current_funcs_ids):
        address_to_funcs_ids_target[address] = current_funcs_ids

count_all = 0
count_exact = [0 for _ in range(11)]
y_true = {i:[] for i in range(11)}
y_pred = {i:[] for i in range(11)}
y_probas = {i:[] for i in range(11)}
for address in address_to_funcs_ids_target.keys():
    if address in vuln and any(i == 1 for i in address_to_funcs_ids_target[address]):
        count_all += 1

        for i in range(11):
            y_pred[i].append(percs[i].predict([address_to_funcs_ids_target[address]])[0])
            y_true[i].append(vuln[address][i])
            prob = percs[i].decision_function([address_to_funcs_ids_target[address]])[0]
            y_probas[i].append([1-prob, prob])
    
            if y_pred[i][-1] == vuln[address][i]:   
                count_exact[i] += 1

    print("all: {}, exact: {}".format(count_all, count_exact))

# joblib.dump(y_probas, "y_probas.pkl")
# joblib.dump(y_true, "y_true.pkl")
# joblib.dump(y_pred, "y_pred.pkl")
print("all: {}, exact: {}".format(count_all, count_exact))
for i in range(11):
    print("acc {}: {}".format(i, accuracy_score(y_true[i], y_pred[i])))
    skplt.metrics.plot_roc_curve(y_true[i], y_probas[i])
    plt.savefig("{}.jpg".format(i))