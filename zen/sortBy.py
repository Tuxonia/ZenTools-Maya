from zen.isIterable import isIterable

def sortBy(*args,**keywords):
	
	sorted=[]
	sel=[]
	
	if len(args)==1:
		if isIterable(args[0]) and len(args[0])>1:
			sorted=list(args[0][-1])
			sel=list(args[0][0])
			inputType=type(args[0][0]).__name__
		else:
			return
	elif len(args)>1:
		sorted=list(args[-1])
		sel=list(args[0])
		inputType=type(args[0]).__name__
	
	l=sorted[:]
	for s in l:
		if s not in sel:
			sorted.remove(s)
		
	unsorted=sel[0:0]
	
	for s in sel:
		if s not in sorted:
			unsorted=unsorted+[s]
	
	if inputType=='str' or inputType=='unicode':
		unsorted=''.join(unsorted)
		sorted=''.join(sorted)
	elif inputType=='dict':
		sorted=list(sorted)
		unsorted=list(unsorted)
	else:
		exec('sorted='+inputType+'(sorted)')
		exec('unsorted='+inputType+'(unsorted)')
			
	return(sorted+unsorted)
