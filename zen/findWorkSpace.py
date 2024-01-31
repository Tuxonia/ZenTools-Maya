import maya.cmds as mc
from zen import iterable
import os

def findWorkSpace(set=False):
	ws=''
	d=os.path.dirname(mc.file(q=True,loc=True))
	while ws=='' and d!=os.path.dirname(d):
		if 'workspace.mel' in iterable(os.listdir(d)):
			ws=d
		else:
			d=os.path.dirname(d)
	if set: mc.workspace(ws,o=True)
	return ws
