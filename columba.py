# -*- coding: utf-8 -*-
#!/usr/bin/python
from gurobipy import *
import array as arr
import re
import json
import sys
#grbgetkey c26269ac-de92-11e8-804a-02e454ff9c50
#grbgetkey 69b8a336-f619-11e8-a50c-02e454ff9c50
with open ("input.json", 'r') as f:
    read_json = json.loads(f.read())

M = 500000
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


#construct component dictionary
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

#construct connection dictionary
trim_connections = {}
cnt = 0
for connection in read_json["connections"]:
    temp = {
        "name": locals()["connection"]["name"],
        "id": locals()["connection"]["id"],
        "layer": "flow-layer-id",
        "source": {
            "number": -1,
            "relative_x": 0,
            "relative_y": 0,
            "x": 0,
            "y": 0,
            "l_total": 0
        },
        "sinks": {}
    }
    sink_temp = {
        "number": -1,
        "relative_x": 0,
        "relative_y": 0,
        "x": 0,
        "y": 0,
        "l_x": 0,
        "l_y": 0
    }
    #assuming "id-layer-001" is flow layer, "id-layer-002" is control layer.
    if connection["layer"] == "id-layer-002":
        temp["layer"] = "control-layer-id"

    for i in range(num_components):
        if connection["source"]["component"] == trim_components[i]["id"]:
            temp["source"]["number"] = i
    for j in range(len(connection["sinks"])):
        for i in range(num_components):
            if connection["sinks"][j]["component"] == trim_components[i]["id"]:
                #print trim_components[i]["id"]
                #print trim_components[i]["id"]
                sink_temp["number"] = i
                temp["sinks"][j] = sink_temp.copy()
    for component in read_json["components"]:
        if connection["source"]["component"] == component["id"]:
            for port in component["ports"]:
                if connection["source"]["port"] == port["label"]:
                    temp["source"]["relative_x"] = port["x"]
                    temp["source"]["relative_y"] = port["y"]
    for i in range(len(connection["sinks"])):
        for component in read_json["components"]:
            if connection["sinks"][i]["component"] == component["id"]:
                for port in component["ports"]:
                    if connection["sinks"][i]["port"] == port["label"]:
                        temp["sinks"][i]["relative_x"] = port["x"]
                        temp["sinks"][i]["relative_y"] = port["y"]
    trim_connections[cnt] = temp
    cnt += 1


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

for i in trim_connections:
    trim_connections[i]["source"]["x"] = m.addVar(vtype=GRB.INTEGER, lb=0)
    trim_connections[i]["source"]["y"] = m.addVar(vtype=GRB.INTEGER, lb=0)
    trim_connections[i]["source"]["l_total"] = m.addVar(vtype=GRB.INTEGER, lb=0)
    for j in trim_connections[i]["sinks"]:
        trim_connections[i]["sinks"][j]["x"] = m.addVar(vtype=GRB.INTEGER, lb=0)
        trim_connections[i]["sinks"][j]["y"] = m.addVar(vtype=GRB.INTEGER, lb=0)
        trim_connections[i]["sinks"][j]["l_x"] = m.addVar(vtype=GRB.INTEGER, lb=0)
        trim_connections[i]["sinks"][j]["l_y"] = m.addVar(vtype=GRB.INTEGER, lb=0)


###########################


#######ADD CONSTRAINTS#######

#connection constraints
for i in trim_connections:
    m.addConstr(trim_connections[i]["source"]["x"] == trim_components[trim_connections[i]["source"]["number"]]["x"] + trim_connections[i]["source"]["relative_x"])
    m.addConstr(trim_connections[i]["source"]["y"] == trim_components[trim_connections[i]["source"]["number"]]["y"] + trim_connections[i]["source"]["relative_y"])
    for j in trim_connections[i]["sinks"]:
        m.addConstr(trim_connections[i]["sinks"][j]["x"] == trim_components[trim_connections[i]["sinks"][j]["number"]]["x"] + trim_connections[i]["sinks"][j]["relative_x"])
        m.addConstr(trim_connections[i]["sinks"][j]["y"] == trim_components[trim_connections[i]["sinks"][j]["number"]]["y"] + trim_connections[i]["sinks"][j]["relative_y"])

def in_range(i, com):
    if i >= referral[com][1] and i < (referral[com][1] + referral[com][0]):
        return 1
    else: return 0

#basic layout of components
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

for i in trim_connections:
    for j in trim_connections[i]["sinks"]:
        m.addConstr(trim_connections[i]["sinks"][j]["l_x"] >= trim_connections[i]["source"]["x"] - trim_connections[i]["sinks"][j]["x"])
        m.addConstr(trim_connections[i]["sinks"][j]["l_x"] >= trim_connections[i]["sinks"][j]["x"] - trim_connections[i]["source"]["x"])
        m.addConstr(trim_connections[i]["sinks"][j]["l_y"] >= trim_connections[i]["source"]["y"] - trim_connections[i]["sinks"][j]["y"])
        m.addConstr(trim_connections[i]["sinks"][j]["l_y"] >= trim_connections[i]["sinks"][j]["y"] - trim_connections[i]["source"]["y"])
    m.addConstr(trim_connections[i]["source"]["l_total"] == quicksum(trim_connections[i]["sinks"][j]["l_x"] for j in trim_connections[i]["sinks"]) + quicksum(trim_connections[i]["sinks"][j]["l_y"] for k in trim_connections[i]["sinks"]))

m.addConstr(L_TOTAL >= quicksum(trim_connections[i]["source"]["l_total"] for i in trim_connections))

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

#no larger than M
for i in range(num_components):
    m.addConstr(trim_components[i]["x"] + trim_components[i]["x-span"] + MIN_SPACE <= M)
    m.addConstr(trim_components[i]["y"] + trim_components[i]["y-span"] + MIN_SPACE <= M)
#############################

########ADD OBJECTIVE########

m.setObjective(alpha * X_MAX + beta * Y_MAX + gamma * XY_MAX + kappa * L_TOTAL, GRB.MINIMIZE)

m.optimize()

#############################

print "X_MAX:", X_MAX.x
print "Y_MAX:", Y_MAX.x
print "XY_MAX:", XY_MAX.x
print "L_MAX:", L_TOTAL.x

for i in range(num_components):
    print trim_components[i]["name"], " ( ", trim_components[i]["x"].x, ", ", trim_components[i]["y"].x, " )"

for i in trim_connections:
    print "SOURCE: ", trim_connections[i]["name"], " ( ", trim_connections[i]["source"]["x"].x, ", ", trim_connections[i]["source"]["y"].x, " )"
    for j in trim_connections[i]["sinks"]:
        print "SINKS:  ( ", trim_connections[i]["sinks"][j]["x"].x, ", ", trim_connections[i]["sinks"][j]["y"].x, " )"

#######WRITE INTO JSON######

num_channels = 0
for i in range(len(trim_connections)):
    num_channels += len(trim_connections[i]["sinks"])

referral_sinks = {}
cnt = 0
for i in range(len(trim_connections)):
    temp = [cnt, len(trim_connections[i]["sinks"])]
    referral_sinks[i] = temp
    cnt += len(trim_connections[i]["sinks"])

def generate_sinks(trim_connections, i, j):
    return {
                "x": int(trim_connections[i]["sinks"][j]["x"].x),
                "y": int(trim_connections[i]["sinks"][j]["y"].x)
            }

features = {"features": {}}
def generate_features(trim_components, trim_connections, i):
    if i < num_components:
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
    else:
        j = i - num_components
        index_sinks = 0
        for k in range(len(referral_sinks)):
            if j >= referral_sinks[k][0] and j < referral_sinks[k][0] + referral_sinks[k][1]:
                index_sinks = k
                break
        feature_id = "-" + str(j - index_sinks)
        return {
                    "type": "channel",
                    "name": trim_connections[index_sinks]["name"],
                    "id": trim_connections[index_sinks]["name"] + feature_id,
                    "connection": trim_connections[index_sinks]["id"],
                    "layer": trim_connections[index_sinks]["layer"],
                    "width": 5,
                    "depth": 5,
                    "source": {
                        "x": int(trim_connections[index_sinks]["source"]["x"].x),
                        "y": int(trim_connections[index_sinks]["source"]["y"].x)
                    },
                    "sink": {
                        "x": int(trim_connections[index_sinks]["sinks"][j-referral_sinks[index_sinks][0]]["x"].x),
                        "y": int(trim_connections[index_sinks]["sinks"][j-referral_sinks[index_sinks][0]]["y"].x)
                    }
                        
                }

features["features"] = [generate_features(trim_components, trim_connections, i) for i in range(num_components+num_channels)]
#print component_feature
read_json.update(features)

with open('columba.json', 'w') as fp:
    json.dump(read_json, fp, indent=4)


