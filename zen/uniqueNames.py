import maya.cmds as mc
from zen.iterable import iterable
from zen.isIterable import isIterable
from zen.removeDuplicates import removeDuplicates
from zen.removeAll import removeAll
from zen.shape import shape
from zen.getReversed import getReversed
from zen.hierarchyOrder import hierarchyOrder
from zen.intersect import intersect
import re
			
def uniqueNames(*args,**keywords):
	
	"""
With no keywords, returns a unique version of the given name(s).
With re=True or raiseException=True : Ensures unique names are used in the scene and raises an error if there are duplicates present.
With rn=True or rename=True : renames any object which have duplicate names.
	"""
	
	rename=False
	raiseException=False
	validate=False
	
	shortNames=\
	{
		'rn':'rename',
		'v':'validate',
		're':'raiseException'
	}
	
	for k in keywords:
		if k in locals():
			exec(k+'=keywords[k]')
		elif k in shortNames:
			exec(shortNames[k]+'=keywords[k]')
	
	if len(args)==0: args=mc.ls(sl=True)
	if len(args)==0: args=mc.ls()

	sel=[]
	for a in args:
		sel.extend(iterable(a))
		
	shapes=[]	
	for s in sel:
		if mc.objExists(s) and shape(s)==s:
			shapes.append(s)
			
	sel=removeAll(shapes,sel)+shapes
	
	if validate:
		rename=False
		raiseException=False	
	
	if rename:
		raiseException=False
		validate=False	
		
	if raiseException:
		rename=False
		validate=False	
	
	max=0
	if rename or validate or raiseException:
		max=1
		
	
	names=[]
	nonUnique=[]
	newNames={}
	baseNameRE=re.compile('(^[^0-9].*[^0-9])')
		
	for s in sel:

		sn=iterable(s.split('|'))[-1]
		ln=hierarchyOrder(removeDuplicates(mc.ls(sn,l=True)),r=True)
		
		if len(ln)>max:

			try:
				baseName=baseNameRE.match(sn).group(0)
			except:
				baseName=sn
				
			i=1
			rn=s
			un=[]
			while mc.objExists(rn) or len(un)<len(ln):
				rn=baseName+str(i)
				if not mc.objExists(rn):
					un.append(rn)
				i+=1
			
			names.append(un[0])
					
			for i in range(0,len(ln)):
				if validate or rename: 
					newNames[ln[i]]=un[i]
					if rename:
						mc.rename(ln[i],un[i])
				else:
					nonUnique.append(ln[i])
		else:
			names.append(s)

	if raiseException:
		if len(nonUnique)>0:
			print(('##Non-unique names:##\n'+str(nonUnique)))
			raise Exception('Non-unique names found.')
		return nonUnique
		
	elif validate or rename:
		return newNames
		
	else:
		if len(sel)==1 and len(names)==1:
			return names[0]
		else:
			return names
	