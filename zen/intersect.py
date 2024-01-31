from zen.removeDuplicates import removeDuplicates
from zen.removeAll import removeAll
from zen.iterable import iterable

def intersect(*args,**keywords):
	
	for k in keywords:
		if k in locals():
			exec(k+'=keywords[k]')
		elif k in shortNames:
			exec(shortNames[k]+'=keywords[k]')
			
	sel=[]		
	for a in args:
		sel.append(list(iterable(a)))
	
	intersected=[]		
	for s in sel[0]:
		inAll=True
		for ss in sel[1:]:
			if s not in ss:
				inAll=False
				break
		if inAll:
			intersected.append(s)
			
	return intersected
