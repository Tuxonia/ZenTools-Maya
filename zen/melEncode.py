import maya.cmds as mc
from zen.isIterable import isIterable

def melEncode(arg):
	
	if isinstance(arg,str):
		return '"'+mc.encodeString(arg)+'"'
	elif isIterable(arg):
		returnVal='{'
		for i in range(0,len(arg)):
			if(isIterable(arg[i])):
				returnVal+='"'
				for n in range(0,len(arg[i])):
					returnVal+=str(arg[i][n])
					if n<len(arg[i])-1 and len(str(arg[i][n]))>0: 
						returnVal+=','
				returnVal+='"'		
			else:
				returnVal+=melEncode(arg[i])
			if i<len(arg)-1 and len(str(arg[i]))>0: 
				returnVal+=','
		returnVal+='}'
		return returnVal
	return 	str(arg)
