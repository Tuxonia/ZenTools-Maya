import maya.mel as mel
import maya.cmds as mc
from zen.iterable import iterable

def exactLocalBoundingBox(*args,**keywords):

	if len(args)==0:
		args=mc.ls(sl=True)
		
	obj=args[0]
	
	r=False #relative to the rotate pivot
	
	for k in keywords:
		if k=='r' or k=='relative':
			r=keywords[k]
		if k in locals():
			exec(k+'=keywords[k]')		
	
	t,r,s=mc.getAttr(obj+'.t')[0],mc.getAttr(obj+'.r')[0],mc.getAttr(obj+'.s')[0]

	mc.setAttr(obj+'.t',0,0,0)
	mc.setAttr(obj+'.r',0,0,0)
	mc.setAttr(obj+'.s',1,1,1)
	
	if r:
		rp=mc.xform(obj,q=True,ws=True,rp=True)
		mc.xform(obj,ws=True,t=(-rp[0],-rp[1],-rp[2]))
		
	returnVal=mc.exactWorldBoundingBox(obj)
	
	mc.setAttr(obj+'.t',*t)
	mc.setAttr(obj+'.r',*r)
	mc.setAttr(obj+'.s',*s)
	
	return returnVal
