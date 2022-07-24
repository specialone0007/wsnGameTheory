import json
import matplotlib.pyplot as plt
import numpy as np

"""
plotDictB1 = json.load(open("b1.txt"))

x_axisB1 = list(plotDictB1.keys())
x_axisB1 = [int(i) for i in x_axisB1]
y_axisB1 = list(plotDictB1.values())

plotDictB2 = json.load(open("b2.txt"))

x_axisB2 = list(plotDictB2.keys())
x_axisB2 = [int(i) for i in x_axisB2]
y_axisB2 = list(plotDictB2.values())

plotDictDeltaB1 = json.load(open("deltab1.txt"))

x_axisDeltaB1 = list(plotDictDeltaB1.keys())
x_axisDeltaB1 = [int(i) for i in x_axisDeltaB1]
y_axisDeltaB1 = list(plotDictDeltaB1.values())

plotDictDeltaB2 = json.load(open("deltab2.txt"))

x_axisDeltaB2 = list(plotDictDeltaB2.keys())
x_axisDeltaB2 = [int(i) for i in x_axisDeltaB2]
y_axisDeltaB2 = list(plotDictDeltaB2.values())
"""

plotS = json.load(open("s.txt"))

x_axisS = list(plotS.keys())
x_axisS = [int(i) for i in x_axisS]
y_axisS = list(plotS.values())

plotP = json.load(open("p.txt"))

x_axisP = list(plotP.keys())
x_axisP = [int(i) for i in x_axisP]
y_axisP = list(plotP.values())

fig = plt.figure()

"""
plt.scatter(x_axisB1, y_axisB1, marker='x', label=r'$B_{1}$')
plt.scatter(x_axisB2, y_axisB2, marker='d', label=r'$B_{2}$')
plt.scatter(x_axisDeltaB1, y_axisDeltaB1, marker='+', label=r'$DeltaB_{1}$')
plt.scatter(x_axisDeltaB2, y_axisDeltaB2, label=r'$DeltaB_{2}$')

plt.plot(x_axisB1, y_axisB1)
plt.plot(x_axisB2, y_axisB2)
plt.plot(x_axisDeltaB1, y_axisDeltaB1)
plt.plot(x_axisDeltaB2, y_axisDeltaB2)
"""

plt.scatter(x_axisS, y_axisS, marker='x', label='S')
plt.plot(x_axisS, y_axisS)

plt.scatter(x_axisP, y_axisP, label='P')
plt.plot(x_axisP, y_axisP)
plt.legend()

plt.xlabel("P/S")
plt.ylabel(r'$P_{J}$')

"""
plt.xlabel(r'$B_{1}/B_{2}/DeltaB_{1}/DeltaB_{2}$')
plt.ylabel(r'$P_{J}$')
"""


plt.xticks(np.arange(min(x_axisS), max(x_axisS)+1, 1.0))
plt.show()
