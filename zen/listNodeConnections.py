import maya.cmds as mc
from zen.isIterable import isIterable
from zen.removeDuplicates import removeDuplicates

def listNodeConnections(*args,**keywords):

	s=True
	d=True
	sn=False
	
	sel=[]
	if len(args)==0:
		sel=mc.ls(sl=True)
		
	for a in args:
		if isIterable(a):
			sel.extend(a)
		else:
			sel.append(a)
			
	for k in keywords:
		if k=='s' or k=='source':
			s=keywords[k]
		if k=='d' or k=='destination':
			d=keywords[k]
		if k=='sn' or k=='shortName':
			sn=keywords[k]
		elif k in locals():
			exec(k+'=keywords[k]')
	
	connections=[]
	
	for conn in removeDuplicates(mc.listConnections(sel[0],s=s,d=d,p=True)):
		
		if len(sel)==1 or mc.ls(conn,o=True)[0]==sel[1]:
			if mc.connectionInfo(conn,isSource=True):
				for dfs in mc.connectionInfo(conn,dfs=True):
					if mc.ls(dfs,o=True)[0]==sel[0]:
						if sn:
							connections.append\
							(
								[
									mc.ls(conn,o=True)[0]+'.'+mc.listAttr(conn,sn=True)[0],
									mc.ls(dfs,o=True)[0]+'.'+mc.listAttr(dfs,sn=True)[0]
								]
							)
						else:
							connections.append([conn,dfs])
			if mc.connectionInfo(conn,id=True):
				sfd=mc.connectionInfo(conn,sfd=True)
				if mc.ls(sfd,o=True)[0]==sel[0]:
					if sn:
						connections.append\
						(
							[
								mc.ls(sfd,o=True)[0]+'.'+mc.listAttr(sfd,sn=True)[0],
								mc.ls(conn,o=True)[0]+'.'+mc.listAttr(conn,sn=True)[0]
							]
						)
					else:
						connections.append([sfd,conn])
						
	return removeDuplicates(connections)
