import maya.cmds as mc
import maya.mel as mel
from platform import python_version
from zen.isIterable import isIterable
from zen.removeDuplicates import removeDuplicates
from zen.disconnectNodes import disconnectNodes
from zen.removeAll import removeAll
from zen.deferExec import deferExec

def constrainShape(shape):

	parentTr=mc.listRelatives(shape,p=True)
	while isIterable(parentTr): parentTr=parentTr[0]
	objCenter=mc.objectCenter(shape,gl=True)
	objCenterLocal=mc.objectCenter(shape,l=True)

	obj=mc.ls(parentTr,o=True)[0]

	constraintAttrs=mc.listConnections(parentTr,p=True,s=True,d=True,type='constraint')
	constraints=[]
	for c in mc.ls(constraintAttrs,o=True):
		if c not in constraints: constraints.append(c)

	if not isIterable(constraintAttrs) or len(constraintAttrs)==0:
		raise Exception(shape+' is not under a constrained transform.')

	tgNode=mc.createNode('transformGeometry')
	type=mc.nodeType(shape)
	base=mc.listRelatives(mc.duplicate(parentTr,rc=True)[0],c=True,type=type,s=True,ni=True)[0]
	mel.eval('zenParentShape {"'+base+'","'+parentTr+'"}')

	creationAttr=''
	creationIn=''
	creationOut=''
	if type=='mesh':
		creationIn='.inMesh'
		creationOut='.outMesh'
	elif type in ('nurbsCurve','nurbsSurface'):
		creationIn='.create'
		creationOut='.local'

	dummyTr=mc.createNode('unknownTransform',p=parentTr,n='dummyTr#')
	for c in constraints:
		mc.connectAttr(dummyTr+'.t',c+'.restTranslate',f=True)

	mc.xform(dummyTr,ws=True,t=objCenter)

	mc.connectAttr(base+creationOut,tgNode+".inputGeometry")
	mc.connectAttr(tgNode+".outputGeometry",shape+creationIn,f=True)
	mc.setAttr(base+'.intermediateObject',True)

	constraintAttrs=removeDuplicates(constraintAttrs)

	for c in constraintAttrs:
		connectedFrom=removeDuplicates(mc.listConnections(c,p=True,s=False,d=True))
		connectedTo=removeDuplicates(mc.listConnections(c,p=True,s=True,d=False))
		for cf in connectedFrom:
			if mc.ls(cf,o=True)[0]==obj:
				if mc.isConnected(c,cf):
					mc.disconnectAttr(c,cf)
				mc.connectAttr(c,dummyTr+'.'+mc.listAttr(cf)[0],f=True)
		for ct in connectedTo:
			if mc.ls(ct,o=True)[0]==obj:
				attr=mc.listAttr(ct)[0]
				if mc.isConnected(ct,c):
					mc.disconnectAttr(ct,c)
				mc.connectAttr(dummyTr+'.'+attr,c,f=True)

	mc.xform(parentTr,ws=True,piv=objCenter)
	for c in constraints:
		mc.xform(c,ws=True,piv=objCenter)

	for c in constraints:
		mc.disconnectAttr(dummyTr+'.t',c+'.restTranslate')

	mc.connectAttr(dummyTr+'.matrix',tgNode+'.transform',f=True)
	mel.eval('rigZenMakeNodesNonKeyable({"'+dummyTr+'"})')

	return(dummyTr)
