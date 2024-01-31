def isIterable(obj):
	
	return hasattr(obj,'__iter__') and not isinstance(obj,str)
