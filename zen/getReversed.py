from copy import copy
from zen.isIterable import isIterable
from zen.iterable import iterable
def getReversed(*args):
	sel=[]
	for a in args:
		sel.extend(iterable(a))
	sel.reverse()
	return sel
