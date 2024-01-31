import maya.cmds as mc
import maya.mel as mel
from zen.iterable import iterable
from zen.removeDuplicates import removeDuplicates
from zen.isIterable import isIterable

def goToDagPose(*args,**keywords):
	
	bindPose=False
	
	shortNames={'bp':'bindPose'}

	for k in keywords:
		if k in locals():
			exec(k+'=keywords[k]')
		if k in shortNames:
			exec(shortNames[k]+'=keywords[k]')

	sel=[]
	if len(args)==0:
		sel=mc.ls(sl=True)
		
	for a in args:
		if isIterable(a):
			sel.extend(a)
		else:
			sel.append(a)

	if len(iterable(mc.ls(sel,type='dagPose')))==0 or bindPose:
		sel=removeDuplicates(mc.dagPose(mc.listConnections(mc.ls(mc.listHistory(sel)),type='transform'),q=True,bp=True))
		
	if len(sel)==0: return

	mel.eval('DisableAll')
		
	success=True
	err=True
	
	for i in range(0,10):
		try: 
			mc.dagPose(sel[0],r=True)
			err=False
			break
		except:
			err=True
			
	mel.eval('EnableAll')
		
	if err and len(iterable(mc.dagPose(q=True,ap=True))):
		success=False

	if success: return sel[0]
	else: return
