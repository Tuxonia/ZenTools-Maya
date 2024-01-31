import maya.cmds as mc
from zen.iterable import iterable
from zen.isIterable import isIterable
from zen.listNodeConnections import listNodeConnections

def firstOpenPlug(*args):
	
	sel=[]
	for a in args:
		sel.extend(iterable(a))
		
	attributes=[]
	for s in sel:
		if mc.objExists(s): 
			attributes.append(mc.ls(s)[0])
			
	objects=[]
	indices=[]
	for attr in attributes:
		
		objects.append(mc.ls(attr,o=True)[0])
		
		objConn=[]
		for oc in listNodeConnections(objects[-1]):
			objConn.extend(oc)
			
		connections=[]
		for conn in objConn:
			if attr in conn:
				connections.append(conn)
		
		endPlug=-1
		i=0
		while endPlug==-1:
			ic=False
			for c in connections:
				if (attr+'['+(str(i))+']') in c:
					ic=True
					break
			if ic==False:
				endPlug=i
			i+=1
			
		indices.append(endPlug)
	
	if len(indices)>1:
		return indices
	elif len(indices)==1:
		return indices[0]
	else:
		return
