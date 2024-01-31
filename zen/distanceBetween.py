import maya.cmds as mc
from zen.isIterable import isIterable
from math import sqrt

def distanceBetween(*args): # distance between two points
	
	if len(args)==0: args=mc.ls(sl=True)
	if len(args)==0: return
	
	p=[]
	for a in args:
		if isIterable(a) and len(a)>=3 and isinstance(a[0],(float,int)) and len(a)>=3:
			p.append(a)
			
		elif isinstance(a,str) and mc.objExists(a):
			
			if len(a.split('.'))>1:
				try: p.append(mc.pointPosition(a))
				except: pass
			else:
				try: p.append(mc.pointPosition(a+'.rp'))
				except: err=True
	
	if len(p)<1: return
	if len(p)>2: p[:]=p[:2]
	
		
	dx = abs(p[0][0]-p[1][0])

	dy = abs(p[0][1]-p[1][1])

	dz = abs(p[0][2]-p[1][2])

	return sqrt(dx*dx+dy*dy+dz*dz)
