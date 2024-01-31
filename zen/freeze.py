import maya.cmds as mc
import maya.mel as mel
from zen.iterable import iterable
from zen.removeDuplicates import removeDuplicates
from zen.isIterable import isIterable

def freeze(*args,**keywords):
	
	shapes=False
	translate=False
	rotate=False
	scale=False
	
	shortNames=\
	{
		'sh':'shapes',
		's':'scale',
		'r':'rotate',
		't':'translate'
	}

	for k in keywords:
		if k in locals():
			exec(k+'=keywords[k]')
		if k in shortNames:
			exec(shortNames[k]+'=keywords[k]')

	sel=[]
	if len(args)==0:
		sel=mc.ls(sl=True)
		
	for a in args:
		sel.extend(iterable(a))
		
	trs=iterable(mc.listRelatives(sel,ad=True,type='transform'))
	trs.extend(sel)
	
	worldMatrices={}
	worldRotations={}
	worldRotationAxis={}
	worldTranslations={}
	worldRotatePivots={}
	worldScalePivots={}
		
	for tr in trs:
		
		worldMatrices[tr]=mc.xform(tr,q=True,ws=True,m=True)
		worldRotations[tr]=mc.xform(tr,q=True,ws=True,ro=True)
		worldRotationAxis[tr]=mc.xform(tr,q=True,ws=True,ra=True)
		worldTranslations[tr]=mc.xform(tr,q=True,ws=True,t=True)
		worldRotatePivots[tr]=mc.xform(tr,q=True,ws=True,rp=True)
		worldScalePivots[tr]=mc.xform(tr,q=True,ws=True,sp=True)
		
	mc.makeIdentity(sel,apply=shapes,r=rotate,t=translate,s=scale)
	
	for tr in trs:
		
		if tr not in sel:
			mc.xform(tr,ws=True,m=worldMatrices[tr])
			mc.xform(tr,ws=True,ro=worldRotations[tr])
			mc.xform(tr,ws=True,t=worldTranslations[tr])
			
		mc.xform(tr,ws=True,ra=worldRotationAxis[tr])
		mc.xform(tr,ws=True,rp=worldRotatePivots[tr])
		mc.xform(tr,ws=True,sp=worldScalePivots[tr])

