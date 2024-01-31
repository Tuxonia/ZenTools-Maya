import maya.cmds as mc
from zen.iterable import iterable
from zen.shape import shape

def duplicateShape(*args,**keywords):
	
	asHistory=False
	shortNames=\
	{
		'ah':'asHistory'
	}
	
	for k in keywords:
		if k in locals():
			exec(k+'=keywords[k]')
		elif k in shortNames:
			exec(shortNames[k]+'=keywords[k]')
			
	if len(args)==0: args=mc.ls(sl=True)
	
	sel=[]
	for a in args:
		sel.extend(iterable(a))
		
	for i in range(0,len(sel)):
		sel[i]=shape(sel[i])
		
	returnVal=[]
		
	for sh in sel:
		tr=mc.listRelatives(sh,p=True)[0]
		trDup=mc.duplicate(tr,rc=True)[0]
		shDup=mc.listRelatives(trDup,s=True)[mc.listRelatives(tr,s=True).index(sh)]
		mc.parent(shDup,tr,s=True,add=True)
		mc.delete(trDup)
		returnVal.append(shDup)
		if asHistory:
			hist=''
			plugIn=''
			plugOut=''
			if mc.nodeType(sh)=='mesh':
				plugIn='.inMesh'
				plugOut='.outMesh'
				if mc.connectionInfo(sh+'.inMesh',id=True):
					hist=mc.connectionInfo(sh+'.inMesh',sfd=True)
			elif  'nurbs' in mc.nodeType(sh):
				plugIn='.create'
				plugOut='.local'
				if mc.connectionInfo(sh+'.create',id=True):
					hist=mc.connectionInfo(sh+'.create',sfd=True)
			if mc.objExists(sh+plugIn) and mc.objExists(shDup+plugIn):
				if mc.objExists(hist): 
					mc.connectAttr(hist,shDup+plugIn,f=True)
				mc.connectAttr(shDup+plugOut,sh+plugIn,f=True)
				mc.setAttr(shDup+'.io',True)
				
	if len(returnVal)==1:
		return returnVal[0]
	elif len(returnVal)==0:
		return ''
	else:
		return returnVal
