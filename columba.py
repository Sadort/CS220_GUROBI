# -*- coding: utf-8 -*-
#!/usr/bin/python
from gurobipy import *
import array as arr
import re
import json
import sys

with open ("columba.json", 'r') as f:
    read_json = json.loads(f.read())

M = 5000000
MIN_SPACE = 10 #define minimum distance between each components
flow_span = 25
control_span = 25 #default flow/control port span, assuming x-span always equals to y-span

mixer_dict = {}
vmixer_dict = {}
colchamber_dict = {}
inflow_dict = {}
outflow_dict = {}
ucontrol_dict = {}
lcontrol_dict = {}
trim_components = {}


for component in read_json["components"]:
    temp = {
        "entity": locals()["component"]["entity"],
        "name": locals()["component"]["name"],
        "id": locals()["component"]["id"],
        "x-span": int(locals()["component"]["x-span"]),
        "y-span": int(locals()["component"]["y-span"]),
        "x": 0,
        "y": 0
    }
    if component["entity"] == "mixer":
        mixer_dict[len(mixer_dict)] = temp
    elif component["entity"] == "vertical-mixer":
        vmixer_dict[len(vmixer_dict)] = temp
    elif component["entity"] == "column-chamber":
        colchamber_dict[len(colchamber_dict)] = temp
    elif component["entity"] == "flow-port":
        flow_span = int(component["x-span"])
        if re.search('flow-input', component["name"]):
            inflow_dict[len(inflow_dict)] = temp
        else: outflow_dict[len(outflow_dict)] = temp
    elif component["entity"] == "control-port":
        control_span = int(component["x-span"])
        if  component["ports"]["y"] == 0:
            lcontrol_dict[len(lcontrol_dict)] = temp
        else: ucontrol_dict[len(ucontrol_dict)] = temp

referral = {
    "mixer": [len(mixer_dict), -1], #length, start point
    "vmixer": [len(vmixer_dict), -1],
    "colchamber": [len(colchamber_dict), -1],
    "inflow": [len(inflow_dict), -1],
    "outflow": [len(outflow_dict), -1],
    "ucontrol": [len(ucontrol_dict), -1],
    "lcontrol": [len(lcontrol_dict), -1]
}
num_components = 0
for x in referral:
    num_components += referral[x][0]

cnt = 0
tmp = 0
for x in referral:
    if referral[x][0] != 0:
        referral[x][1] = cnt
        cnt += referral[x][0]
print referral
for x in referral:
    if referral[x][1] != -1:
        for i in range(referral[x][1], referral[x][1] + referral[x][0]):
            if x == "mixer":
                trim_components[i] = mixer_dict[i - referral[x][1]]
            elif x == "vmixer":
                trim_components[i] = vmixer_dict[i - referral[x][1]]
            elif x == "colchamber":
                trim_components[i] = colchamber_dict[i - referral[x][1]]
            elif x == "inflow":
                trim_components[i] = inflow_dict[i - referral[x][1]]
            elif x == "outflow":
                trim_components[i] = outflow_dict[i - referral[x][1]]
            elif x == "ucontrol":
                trim_components[i] = ucontrol_dict[i - referral[x][1]]
            elif x == "lcontrol":
                trim_components[i] = lcontrol_dict[i - referral[x][1]]
if len(trim_components) != num_components:
    print "error in trimming componnets"

#print trim_components

with open("params.txt") as f:
    alpha = int(f.readline().strip('\n'))
    beta = int(f.readline().strip('\n'))
    gamma = int(f.readline().strip('\n'))
    kappa = int(f.readline().strip('\n'))

m = Model("Columba")

#######ADD VARIABLES#######
for i in trim_components:
    trim_components[i]["x"] = m.addVar(vtype=GRB.INTEGER, lb=0)
    trim_components[i]["y"] = m.addVar(vtype=GRB.INTEGER, lb=0)

X_MAX = m.addVar(vtype=GRB.INTEGER, lb=0)
Y_MAX = m.addVar(vtype=GRB.INTEGER, lb=0)
XY_MAX = m.addVar(vtype=GRB.INTEGER, lb=0)
L_TOTAL = m.addVar(vtype=GRB.INTEGER, lb=0)

q = {}
for i in range(2 * num_components * (num_components - 1)):
    q[i] = m.addVar(vtype=GRB.BINARY)

###########################

def in_range(i, com):
    if i >= referral[com][1] and i < (referral[com][1] + referral[com][0]):
        return 1
    else: return 0

#######ADD CONSTRAINTS#######

#basic layout
for i in trim_components:
    if trim_components[i]["entity"] == "flow-port":
        if in_range(i, "inflow"):
            m.addConstr(trim_components[i]["x"] == MIN_SPACE)
            m.addConstr(trim_components[i]["y"] >= 2 * MIN_SPACE + control_span)
        else:
            m.addConstrs(trim_components[i]["x"] >= MIN_SPACE + trim_components[j]["x"] + trim_components[j]["x-span"] for j in range(referral["outflow"][1]))
            m.addConstrs(trim_components[i]["x"] >= MIN_SPACE + trim_components[j]["x"] + trim_components[j]["x-span"] for j in range(referral["outflow"][1] + referral["outflow"][0], len(trim_components)))
            m.addConstr(trim_components[i]["y"] >= 2 * MIN_SPACE + control_span)
    elif trim_components[i]["entity"] == "control-port":
        if in_range(i, "ucontrol"):
            m.addConstr(trim_components[i]["x"] >= 2 * MIN_SPACE + flow_span)
            m.addConstr(trim_components[i]["y"] == MIN_SPACE)
        else:
            m.addConstrs(trim_components[i]["y"] >= MIN_SPACE + trim_components[j]["y"] + trim_components[j]["y-span"] for j in range(referral["lcontrol"][1]))
    else:
        m.addConstr(trim_components[i]["x"] >= 2 * MIN_SPACE + flow_span)
        m.addConstr(trim_components[i]["y"] >= 2 * MIN_SPACE + control_span)

for i in range(referral["outflow"][1] + 1, referral["outflow"][1] + referral["outflow"][0]):
    m.addConstr(trim_components[referral["outflow"][1]]["x"] == trim_components[i]["x"])
for i in range(referral["lcontrol"][1] + 1, referral["lcontrol"][1] + referral["lcontrol"][0]):
    m.addConstr(trim_components[referral["lcontrol"][1]]["y"] == trim_components[i]["y"])

#MAX
if referral["outflow"][0] != 0:
    m.addConstr(X_MAX >= trim_components[referral["outflow"][1]]["x"] + flow_span + MIN_SPACE)
else:
    m.addConstrs(X_MAX >= MIN_SPACE + trim_components[i]["x"] + trim_components[i]["x-span"] for i in range(num_components))

if referral["lcontrol"][0] != 0:
    m.addConstr(Y_MAX >= trim_components[referral["lcontrol"][1]]["y"] + control_span + MIN_SPACE)
else:
    m.addConstrs(Y_MAX >= MIN_SPACE + trim_components[j]["y"] + trim_components[j]["y-span"] for j in range(num_components))

m.addConstr(XY_MAX >= X_MAX)
m.addConstr(XY_MAX >= Y_MAX)
#get rid of overlap
cnt = 0
for i in range(num_components):
    for j in range(i+1, num_components):
        m.addConstr(trim_components[i]["x"] + trim_components[i]["x-span"] + MIN_SPACE <= trim_components[j]["x"] + q[cnt] * M)
        m.addConstr(trim_components[j]["x"] + trim_components[j]["x-span"] + MIN_SPACE <= trim_components[i]["x"] + q[cnt+1] * M)
        m.addConstr(trim_components[i]["y"] + trim_components[i]["y-span"] + MIN_SPACE <= trim_components[j]["y"] + q[cnt+2] * M)
        m.addConstr(trim_components[j]["y"] + trim_components[j]["y-span"] + MIN_SPACE <= trim_components[i]["y"] + q[cnt+3] * M)
        m.addConstr(q[cnt] + q[cnt+1] + q[cnt+2] + q[cnt+3] == 3)
        cnt += 4

#############################

########ADD OBJECTIVE########

m.setObjective(alpha * X_MAX + beta * Y_MAX + gamma * XY_MAX + kappa * L_TOTAL, GRB.MINIMIZE)

m.optimize()

#############################

print "X_MAX:", X_MAX.x
print "Y_MAX:", Y_MAX.x
print "XY_MAX:", XY_MAX.x

for i in range(num_components):
    print trim_components[i]["name"], " ( ", trim_components[i]["x"].x, ", ", trim_components[i]["y"].x, " )"

#######WRITE INTO JSON######

component_feature = {"features": {}}
#components

def generate_components(trim_components, i):
    return {
                "type": "component",
                "name": trim_components[i]["name"],
                "id": trim_components[i]["id"],
                "location": {
                    "x" : int(trim_components[i]["x"].x),
                    "y" : int(trim_components[i]["y"].x)
                },
                "x-span": trim_components[i]["x-span"],
                "y-span": trim_components[i]["y-span"],
                "depth": 5
            }

component_feature["features"] = [generate_components(trim_components, k) for k in range(num_components)]
print component_feature
read_json.update(component_feature)

with open('data.json', 'w') as fp:
    json.dump(read_json, fp, indent=4)
