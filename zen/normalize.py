from math import sqrt
from zen.isIterable import isIterable

def normalize(*args): # normalize a vector
	
	aa=[]
	v=[]
	
	for a in args:
		if isIterable(a):
			aa.extend(a)
		else:
			aa.append(a)
			
	for a in aa:
		if isinstance(a,(float,int)):
			v.append(float(a))
	
	if len(v)<3: 
		raise Exception('normalize requires an input of 3 numbers')
	if len(v)>3: v[:]=v[:3]
			
	factor = 1.0
	vLen=v[0]*v[0]+v[1]*v[1]+v[2]*v[2];

	if vLen==0: return
	
	factor=1.0/sqrt(vLen)

	if factor!=1.0:
		v[0] *= factor
		v[1] *= factor
		v[2] *= factor

	return v
