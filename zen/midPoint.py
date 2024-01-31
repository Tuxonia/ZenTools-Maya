import maya.cmds as mc
from zen.isIterable import isIterable
from zen.iterable import iterable
	
def midPoint(*args,**keywords): # weighted midPoint
	
	world=False
	local=False
	
	bias=0.5 # 0.0==point1, 1.0==point2
	
	shortNames=\
	{
		'w':'world',
		'l':'local',
		'b':'bias'
	}
	
	for k in keywords:
		if k in locals():
			exec(k+'=keywords[k]')
		if k in shortNames:
			exec(shortNames[k]+'=keywords[k]')
			
	if not(world or local): world=True
		
	if len(args)==0: args=mc.ls(sl=True)
	if len(args)==0: return
	
	p=[]
	for a in args:
		if isIterable(a) and len(a)>=3 and isinstance(a[0],(float,int)) and len(a)>=3:
			p.append(a)
			
		elif isinstance(a,str) and mc.objExists(a):
			
			if len(a.split('.'))>1:
				try: 
					p.append(mc.pointPosition(a,w=world,l=local))
				except: 
					if mc.nodeType(mc.ls(a,o=True))=='mesh':
						for v in iterable(mc.ls(mc.polyListComponentConversion(a,tv=True),fl=True)):
							p.append(mc.pointPosition(v,w=world,l=local))
			else:
				try: p.append(mc.pointPosition(a+'.rp',w=world,l=local))
				except: err=True
	
	if len(p)<1: return
	if len(p)==1: return p[0]
	
	mp=[0.0,0.0,0.0]
	
	if len(p)==2: # use bias
		
		mp=\
		(
			(float(p[0][0])*(1-bias)+float(p[-1][0])*bias),
			(float(p[0][1])*(1-bias)+float(p[-1][1])*bias),
			(float(p[0][2])*(1-bias)+float(p[-1][2])*bias)
		)
		
	else: # disregard bias
		
		for pp in p:
			
			mp=\
			(
				mp[0]+(float(pp[0])*(1.0/float(len(p)))),
				mp[1]+(float(pp[1])*(1.0/float(len(p)))),
				mp[2]+(float(pp[2])*(1.0/float(len(p))))
			)
			
	return mp
