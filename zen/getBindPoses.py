import maya.cmds as mc
from zen.removeDuplicates import removeDuplicates
from zen.isIterable import isIterable
from zen.iterable import iterable

def getBindPoses(*args):
	
	sel=[]
	if len(args)==0:
		sel=iterable(mc.ls(sl=True))
		
	for a in args:
		sel.extend(iterable(a))
		
	if len(sel)==0: return
	
	trs=iterable(mc.listConnections(iterable(mc.ls(mc.listHistory(sel))),type='transform'))+sel

	return removeDuplicates(mc.dagPose(trs,q=True,bp=True))
