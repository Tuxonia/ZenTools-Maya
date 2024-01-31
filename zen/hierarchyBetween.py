import maya.cmds as mc
from zen.isIterable import isIterable
def hierarchyBetween(*args,**keywords):
	sel=[]
	type=''
	if len(args)==0:
		sel=mc.ls(sl=True)
	for a in args:
		if isIterable(a):
			sel.extend(a)
		else:
			sel.append(a)
	for k in keywords:
		if k=='t' or k=='type':
			type=keywords[k]
		elif k in locals():
			exec(k+'=keywords[k]')
	shortNames=mc.ls(sel,sn=True)
	longNames=mc.ls(sel,l=True)
	if shortNames[0] not in longNames[-1].split('|'):
		shortNames.reverse()
		longNames.reverse()
	hierarchy=longNames[-1].split('|')
	if shortNames[0] not in hierarchy: return []
	hierarchyBetween=[]
	for i in range(hierarchy.index(shortNames[0]),len(hierarchy)):
		if type=='':
			h=mc.ls('|'.join(hierarchy[:i+1]))
		else:
			h=mc.ls('|'.join(hierarchy[:i+1]),type=type)
		if isIterable(h) and len(h)>0:
			hierarchyBetween.append(h[0])
	return hierarchyBetween
