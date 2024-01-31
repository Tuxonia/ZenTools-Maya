from zen.isIterable import isIterable

def removeDuplicates(iterable):
	if not isIterable(iterable):
		if isinstance(iterable,(str,float,int)):
			return [iterable]
		else:
			return []
	returnVal=[]
	for item in iterable:
		if item not in returnVal:
			returnVal.append(item)
	return returnVal
