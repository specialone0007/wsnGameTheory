import random
import json
from time import time


def AverageList(lst):
    if not lst:
        return 0
    return sum(lst) / len(lst)


def add_edge(inputGraph, vertex, vertexTo):
    inputGraph[vertex]["neighbours"].append(vertexTo)
    inputGraph[vertexTo]["neighbours"].append(vertex)


def add_vertex(inputGraph, vertex):
    inputGraph[vertex] = {"neighbours": [], "type": None, "action": None}


def createRandomWSN(V, E, M):
    malicious_nodes = []
    graph = {}
    vertices = list(range(V))
    random.shuffle(vertices)
    setMaliciousNodes = set(vertices[:M])

    for i in range(V):
        add_vertex(graph, i)
        if i in setMaliciousNodes:
            graph[i]["type"] = "malicious"
            malicious_nodes.append(i)
        else:
            graph[i]["type"] = "normal"

    for i in range(V):
        selectRandomIndex = random.randint(0, V - 1)
        while selectRandomIndex in graph[i]["neighbours"]:
            selectRandomIndex = random.randint(0, V - 1)
        add_edge(graph, i, selectRandomIndex)

    for _ in range(V, E):
        selectRandomIndex = random.randint(0, V - 1)
        while len(graph[selectRandomIndex]) == V - 1:
            selectRandomIndex = random.randint(0, V - 1)
        selectRandomIndex2 = random.randint(0, V - 1)
        while selectRandomIndex2 == selectRandomIndex or selectRandomIndex2 in graph[selectRandomIndex]["neighbours"]:
            selectRandomIndex2 = random.randint(0, V - 1)
        add_edge(graph, selectRandomIndex, selectRandomIndex2)
    return graph, malicious_nodes


def createRandomActions(graph):
    for v in graph:
        randomNumber = random.randint(0, 99)
        if randomNumber < 25:
            graph[v]["action"] = "F"
        elif randomNumber < 50:
            if graph[v]["type"] == "malicious":
                graph[v]["action"] = "J"
            else:
                graph[v]["action"] = "D"
        elif randomNumber < 75:
            graph[v]["action"] = "R"
        else:
            graph[v]["action"] = "S"


def initializePayOffDict(graph, payOff):
    for v_index in graph:
        payOff[v_index] = {}
        for n in graph[v_index]["neighbours"]:
            payOff[v_index][n] = None


def initializeMaliciousPayOffDict():
    for m in malicious_nodes_wsn:
        maliciousPayOffs[m] = {"F": [], "J": [], "R": [], "S": []}


def updateMaliciousPayOffDict():
    for m in maliciousPayOffs:
        maliciousPayOffs[m][wsn[m]["action"]].append(resulting_pay_offs[m])


def getActionsString(a1, a2):
    return a1 + "-" + a2


def getPairwiseGamePayOff(graph, node1, node2):
    type1 = graph[node1]["type"]
    type2 = graph[node2]["type"]
    action1 = graph[node1]["action"]
    action2 = graph[node2]["action"]
    if type1 == "normal" and type2 == "normal":
        return [normal_normal[getActionsString(action1, action2)], normal_normal[getActionsString(action2, action1)]]
    elif type1 == "malicious" and type2 == "normal":
        return [malicious_normal[getActionsString(action1, action2)],
                normal_malicious[getActionsString(action2, action1)]]
    elif type1 == "normal" and type2 == "malicious":
        return [normal_malicious[getActionsString(action1, action2)],
                malicious_normal[getActionsString(action2, action1)]]
    elif type1 == "malicious" and type2 == "malicious":
        return [malicious_malicious[getActionsString(action1, action2)],
                malicious_malicious[getActionsString(action2, action1)]]


def pairwiseGame(graph, vertex, payOff):
    for neighbour in graph[vertex]["neighbours"]:
        payOffPairArr = getPairwiseGamePayOff(graph, vertex, neighbour)
        if payOff[vertex][neighbour] is None:
            payOff[vertex][neighbour] = payOffPairArr[0]
        if payOff[neighbour][vertex] is None:
            payOff[neighbour][vertex] = payOffPairArr[1]


def equilibriumStateRatio():
    jammingCount = 0
    for m in maliciousPayOffs:
        averages = []
        for a in ["F", "J", "R"]:
            if maliciousPayOffs[m][a]:
                averages.append(AverageList(maliciousPayOffs[m][a]))
        if averages:
            if averages.index(max(averages)) == 1:
                jammingCount += 1
    return jammingCount


def rule(graph, node1, node2, node3, payOff):
    type1 = graph[node1]["type"]
    type2 = graph[node2]["type"]
    type3 = graph[node3]["type"]
    action1 = graph[node1]["action"]
    action2 = graph[node2]["action"]
    action3 = graph[node3]["action"]
    if type1 == type2 == type3 == "normal":
        if action1 == "F" and action2 == "R" and payOff[node1][node2] == af * y - B2:
            payOff[node1][node3] = 0
        if action1 == "F" and payOff[node1][node2] == B2:
            if action3 != "R":
                payOff[node1][node3] = 0
            else:
                payOff[node1][node3] = af * y
        if action1 == "D" and (payOff[node1][node2] == - (B1 + DeltaB1) or payOff[node1][node2] == - B1):
            payOff[node1][node3] = 0
        if action1 == "R" and payOff[node1][node2] == -B1:
            if action3 != "F":
                payOff[node1][node3] = 0
    elif type1 == type2 == "normal" or type3 == "normal":
        changedNode2, changedNode3 = node2, node3
        changedAction2, changedAction3 = action2, action3
        if type2 == "malicious":
            changedNode3, changedNode2 = node2, node3
            changedAction3, changedAction2 = action2, action3

        if action1 == "F" and changedAction2 == "R" and payOff[node1][changedNode2] == af * y - B2:
            payOff[node1][changedAction3] = 0
        if action1 == "F" and payOff[node1][changedNode2] == B2:
            if changedAction3 != "R":
                payOff[node1][changedAction3] = 0
            else:
                payOff[node1][changedAction3] = af * y
        if action1 == "D" and (payOff[node1][changedNode2] == - (B1 + DeltaB1) or payOff[node1][changedNode2] == - B1):
            payOff[node1][changedNode3] = 0
        if action1 == "R" and payOff[node1][changedNode2] == -B1:
            if changedAction3 != "F":
                payOff[node1][changedNode3] = 0
        if changedAction3 == "J" and action1 == "R" and payOff[changedNode3][node1] == aj * y - (B2 + DeltaB2):
            if changedAction2 == "F" and action1 == "R":
                payOff[changedNode2][node1] = -B2
        if changedNode3 in graph[changedNode2]["neighbours"]:
            if changedAction3 == "J" and action1 == "R" and payOff[changedNode3][node1] == aj * y - (B2 + DeltaB2):
                if action1 == "F" and changedAction2 == "R":
                    payOff[node1][changedNode2] = -B2

    elif type1 == "normal" and type2 != "normal" and type3 != "normal":
        if action1 == "F" and action2 == "R" and payOff[node1][node2] == af * y - B2:
            payOff[node1][node3] = 0
        if action1 == "F" and payOff[node1][node2] == B2:
            if action3 != "R":
                payOff[node1][node3] = 0
            else:
                payOff[node1][node3] = af * y
        if action1 == "R" and payOff[node1][node2] == -B2:
            if action3 == "R" or action3 == "S":
                payOff[node1][node3] = 0
        if action2 == "J" and action1 == "R" and payOff[node2][node1] == aj * y - (B2 + DeltaB2):
            if action3 == "F":
                payOff[node3][node1] = -B2
        if node2 in graph[node3]["neighbours"]:
            if action2 == "J" and action1 == "R" and payOff[node2][node1] == aj * y - (B2 + DeltaB2):
                if action1 == "F" and action3 == "R":
                    payOff[node1][node3] = -B2
    elif type1 == "malicious":
        if action1 == "J" and action2 == "R" and type2 == "normal":
            payOff[node1][node2] += (B1 + DeltaB1) * y * aj
        if action1 == "J" and action2 == "R" and type3 == "normal":
            payOff[node1][node3] += (B1 + DeltaB1) * y * aj


def algorithm1(graph, v, payOff):
    pairwiseGame(graph, v, payOff)
    neighbours = graph[v]["neighbours"]
    for i in range(len(neighbours)):
        for k in range(i + 1, len(neighbours)):
            n1, n2 = neighbours[i], neighbours[k]
            rule(graph, v, n1, n2, payOff)
    payOffForNode = 0
    for node in payOff[v]:
        payOffForNode += payOff[v][node]
    return payOffForNode


def bfs(visited, graph, node, queue, resultingPayOffs, payOff):
    visited.append(node)
    queue.append(node)
    while queue:
        s_node = queue.pop(0)
        resultingPayOffs[s_node] = algorithm1(graph, s_node, payOff)
        for neighbour in graph[s_node]["neighbours"]:
            if neighbour not in visited:
                visited.append(neighbour)
                queue.append(neighbour)


def algorithm2():
    createRandomActions(wsn)
    pairwisePayOff = {}
    initializePayOffDict(wsn, pairwisePayOff)

    resultingPayOffs = {}
    queue = []
    visited = []
    bfs(visited, wsn, 0, queue, resultingPayOffs, pairwisePayOff)
    return resultingPayOffs


numberOFNodes = 1000
maliciousNodeNumbers = numberOFNodes // 10
averageEdgeNumberPerNode = 8
totalDistinctWsn = 1000
stepsToCalculateEquilibrium = 250

t0 = time()
results = {}
for i in range(0, 11):
    results[i] = []

for _ in range(totalDistinctWsn):

    wsn, malicious_nodes_wsn = createRandomWSN(numberOFNodes, numberOFNodes * averageEdgeNumberPerNode // 2,
                                               maliciousNodeNumbers)
    for B1 in range(0, 11):
        maliciousPayOffs = {}
        initializeMaliciousPayOffDict()

        y = 1
        af = 0.75
        aj = 1
        s = 1
        DeltaB1 = 1
        DeltaB2 = 1
        p = 1
        B2 = 1
        malicious_normal = {"F-F": -B2, "F-D": -B2, "F-R": af * y - B2, "F-S": -B2, "J-F": -(B2 + DeltaB2),
                            "J-D": -p - (B2 + DeltaB2), "J-R": aj * y - (B2 + DeltaB2), "J-S": -(B2 + DeltaB2), "R-F":
                                -B1, "R-D": -B1, "R-R": -B1, "R-S": -B1, "S-F": 0, "S-D": 0, "S-R": 0, "S-S": 0}

        malicious_malicious = {"F-F": -B2, "F-J": -B2, "F-R": af * y - B2, "F-S": -B2, "J-F": -(B2 + DeltaB2),
                               "J-J": -(B2 + DeltaB2), "J-R": aj * y - (B2 + DeltaB2), "J-S": -(B2 + DeltaB2), "R-F":
                                   -B1, "R-J": -B1, "R-R": -B1, "R-S": -B1, "S-F": 0, "S-J": 0, "S-R": 0, "S-S": 0}

        normal_normal = {"F-F": -B2, "F-D": -B2, "F-R": af * y - B2, "F-S": -B2, "D-F": -(B1 + DeltaB1), "D-D": -B1,
                         "D-R": -B1, "D-S": -B1, "R-F": -B1, "R-D": -B1, "R-R": -B1, "R-S": -B1, "S-F": 0, "S-D": 0,
                         "S-R": 0, "S-S": 0}

        normal_malicious = {"F-F": -B2, "F-J": -B2, "F-R": af * y - B2, "F-S": -B2, "D-F": -(B1 + DeltaB1),
                            "D-J": s - (B1 + DeltaB1), "D-R": -B1, "D-S": -B1, "R-F": -B1, "R-J": -B1, "R-R": -B1,
                            "R-S": -B1, "S-F": 0, "S-J": 0, "S-R": 0, "S-S": 0}
        for _ in range(stepsToCalculateEquilibrium):
            resulting_pay_offs = algorithm2()
            updateMaliciousPayOffDict()
        jammingRatio = equilibriumStateRatio() / (maliciousNodeNumbers - 0.25 * maliciousNodeNumbers)
        results[B1].append(jammingRatio)

for k in results:
    results[k] = AverageList(results[k])

with open('b1.txt', 'w') as file:
    file.write(json.dumps(results))

