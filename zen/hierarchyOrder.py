import maya.cmds as mc
from zen.iterable import iterable
from zen.isIterable import isIterable
from zen.removeDuplicates import removeDuplicates
from zen.removeAll import removeAll
from zen.getReversed import getReversed
from zen.intersect import intersect
	
def hierarchyOrder(*args,**keywords):
	
	reverse=False
	
	shortNames={'r':'reverse'}
	
	for k in keywords:
		if k in locals():
			exec(k+'=keywords[k]')
		elif k in shortNames:
			exec(shortNames[k]+'=keywords[k]')
			
	if len(args)==0: args=mc.ls(sl=True)
			
	sel=[]		
	for a in args:
		sel.extend(iterable(a))	
		
	sel=removeDuplicates(mc.ls(sel,type='dagNode'))
	if len(sel)<2: return sel

	sorted=[]
	unsorted=list(sel)	
	
	i=0
	while len(unsorted)>0:
		used=[]
		for x in unsorted:
			if len(x.split('|'))==i:
				sorted.append(x)
				used.append(x)
		unsorted=removeAll(used,unsorted)
		i+=1
				
	if reverse:
		return getReversed(sorted)
	else:
		return sorted
