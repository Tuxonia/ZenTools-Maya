import maya.cmds as mc
from zen.iterable import iterable
from zen.isIterable import isIterable

def shape(*args,**keywords):

	all=False
	shortNames=\
	{
		'a':'all'
	}

	for k in keywords:
		if k in shortNames:
			exec(shortNames[k]+'=keywords[k]')
		if k in locals():
			exec(k+'=keywords[k]')

	if len(args)==0: args=iterable(mc.ls(sl=True))

	sel=[]
	for a in args:
		if isIterable(a) or mc.objExists(a):
			sel.append(mc.ls(a,o=True))

	shapes=[]
	for s in sel:
		sh=iterable(mc.ls(s,s=True))
		if len(sh)==0:
			sh=mc.listRelatives(s,c=True,s=True,ni=True)
		if len(iterable(sh))>0:
			if all:
				shapes.append(sh)
			else:
				shapes.append(sh[0])

	if len(shapes)==1:
		return shapes[0]
	elif len(shapes)==0:
		return ''
	else:
		return shapes