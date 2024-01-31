import maya.cmds as mc
from zen.listNodeConnections import listNodeConnections

def disconnectNodes(*args,**keywords):
	connections=listNodeConnections(*args,**keywords)
	for c in connections:
		mc.disconnectAttr(c[0],c[1])
