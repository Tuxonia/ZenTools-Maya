from zen.isIterable import isIterable
from zen.iterable import iterable
import re

def getIDs(*args):
	
	sel=[]
	ids=[]
	for a in args:
		sel.extend(iterable(a))
	
	compRE=re.compile('(?<=\[)\d*?(?=\])')
	
	for s in sel:
		try:
			ids.append(int(compRE.search(s).group()))
		except:
			return
			#raise Exception('Could not find comp id for '+s+'.')
	
	if len(ids)==1: return ids[0]
	else: return ids
