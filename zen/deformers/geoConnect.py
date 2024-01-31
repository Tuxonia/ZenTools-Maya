import maya.cmds as mc
import maya.mel as mel
import maya.utils as mu
import os
from math import ceil
from zen.iterable import iterable
from zen.shape import shape
from zen.getIDs import getIDs
from zen.midPoint import midPoint
from zen.removeDuplicates import removeDuplicates
from zen.getIDs import getIDs
from zen.melGlobalVar import MelGlobalVar
from zen.findFile import findFile
from zen.intersect import intersect
from zen.deformers.blendShape import BlendShape
from zen.deformers.wrap import Wrap

def geoConnect(*args,**keywords):
	
	"""
Connects shapes and worldSpace transforms of one shape to another, or all shapes in one file or namespace to another.
Accepts an input of 2 or more file names, 2 or more name spaces, or any even number of objects.
	"""
	
	# default options
	driverNameSpace=''
	drivenNameSpace=''
	drivers=[]
	driven=[]
	hide=[]
	recursive=False
	maintainOffset=False
	output=''
	
	returnVal=[]
	
	shortNames=\
	{
		'r':'recursive',
		'mo':'maintainOffset',
		'o':'output',
		'rv':'returnVal',
		'h':'hide'
	}
			
	for k in keywords:
		if k in locals():
			exec(k+'=keywords[k]')
		elif k in shortNames:
			exec(shortNames[k]+'=keywords[k]')
			
	if len(args)==0 and driverNameSpace=='' and drivenNameSpace=='':
		sel=iterable(mc.ls(sl=True))
		
	sel=[]
	for a in args:
		sel.extend(iterable(a))
		
	for i in range(0,len(sel)):
		if sel[i]=='':
			sel[i]=':'
	
	fromFiles=True
	for i in range(0,len(sel)):
		if len(sel[i].split('.'))>1:
			if not os.path.isfile(sel[i]):
				filePath=findFile(sel[i])
				if os.path.isfile(filePath):
					sel[i]=filePath
				else:
					fromFiles=False
					break
		else:
			fromFiles=False
			break
			
	hide=iterable(hide)
						
	while len(hide)<len(sel):
		hide.append(False)

	matchByNameSpace=True
	
	if fromFiles:
		if len(sel)==1:
			sel.append(sel[0])
			sel[0]=mc.file(q=True,l=True)[0]
		else:
			if mc.file(q=True,l=True)[0]!=sel[0]:
				mc.file(sel[0],o=True,f=True)
		driverNameSpace=mc.namespaceInfo(cur=True)
		drivenNameSpace=os.path.basename(sel[1].split('.')[0])
		mc.file(sel[1],i=True,ra=True,namespace=drivenNameSpace,pr=True,loadReferenceDepth='all',options='v=1')
	else:
		nameSpaces=[':']+iterable(mc.namespaceInfo(lon=True))
		for s in sel:
			if s not in nameSpaces:
				matchByNameSpace=False
				break
			
		if not matchByNameSpace:
			sel=iterable(mc.ls(sel))
		
	matchNames=False
	
	if matchByNameSpace:
		
		currentNameSpace=mc.namespaceInfo(cur=True)
		
		if not fromFiles:
			if len(sel)>1:
				driverNameSpace=sel[0]
			if len(sel)==1:
				driverNameSpace=':'
			drivenNameSpace=sel[1]
			mc.namespace(set=driverNameSpace)
				
		for d in iterable(mc.ls(mc.namespaceInfo(ls=True),type=('mesh','nurbsCurve','nurbsSurface'))):
			if mc.getAttr(d+'.io')==False:
				drivers.append(d)
		
		mc.namespace(set=drivenNameSpace)
				
		for d in iterable(mc.ls(mc.namespaceInfo(ls=True),type=('mesh','nurbsCurve','nurbsSurface'))):
			if mc.getAttr(d+'.io')==False:
				driven.append(d)
		
		mc.namespace(set=currentNameSpace)
		
		drivers.sort()
		driven.sort()
		
		matchNames=True
		
	elif len(sel)>1:
			
		driven=sel[int(len(sel)/2):int(len(sel)/2)*2]
		drivers=sel[:int(len(sel)/2)]
		
		if recursive:
			
			matchNames=True

			drs=drivers
			dns=driven
			
			if len(drs)<=len(dns):
				r=len(drs)
			else:
				r=len(dns)
			
			for i in range(0,r):
				
				dr=drs[i]
				dn=dns[i]
				
				if shape(dr)!=dr or shape(dn)!=dn:
					
					drivers.remove(dr)
					driven.remove(dn)
					
				if shape(dr)!=dr and shape(dn)!=dn:
					
					drc=[]
					for dr in iterable(mc.listRelatives(dr,ad=True,type=('mesh','nurbsCurve','nurbsSurface'))):
						if mc.getAttr(dr+'.io')==False:
							drc.append(dr)
					drc.sort()
					
					dnc=[]
					for dn in iterable(mc.listRelatives(dn,ad=True,type=('mesh','nurbsCurve','nurbsSurface'))):
						if mc.getAttr(dn+'.io')==False:
							dnc.append(dn)
					dnc.sort()
							
					drivers.extend(drc)
					driven.extend(dnc)
							
		else:
			
			#check to see if we can match by name spaces
			if len(drivers[0].split(':'))>1 or len(driven[0].split(':'))>1:

				if len(drivers[0].split(':'))>1:
					driverNameSpace=':'.join(drivers[0].split(':')[:-1])
				if len(driven[0].split(':'))>1:
					drivenNameSpace=':'.join(driven[0].split(':')[:-1])
					
				matchNames=True
				
				if len(drivers)<=len(driven):
					r=len(drivers) 
				else:
					r=len(driven)
				
				for i in range(0,r):
					
					if\
					(
						(
							(driverNameSpace=='' and len(drivers[i].split(':'))<2) or
							':'.join(drivers[i].split(':')[:-1])==driverNameSpace
						)
						and
						(
							(drivenNameSpace=='' and len(driven[i].split(':'))<2) or
							':'.join(driven[i].split(':')[:-1])==drivenNameSpace
						)
						and
						(
							drivers[i].split(':')[-1]==driven[i].split(':')[-1]
						)
					):
						pass
					else:
						matchNames=False
						break
						
			driversHold=drivers
			drivenHold=driven
			drivers=[]
			driven=[]
			
			if len(drivers)<=len(driven):
				r=len(drivers)
			else:
				r=len(driven)
				
			for i in range(0,r):
				if shape(driversHold[i])!='' and shape(drivenHold[i])!='':
					drivers.append(shape(drivers[i]))
					drivers.append(shape(driven[i]))		
	else:
		return
		
	if matchNames: # match names
		
		driverParents=[]
		driverHasSiblings=[]
		driversBN=[]
		for i in range(0,len(drivers)):
			driversBN.append(drivers[i].split('|')[-1].split(':')[-1])
			driverParents.append(mc.listRelatives(drivers[i],p=True)[0].split('|')[-1].split(':')[-1])
			sib=False
			for c in mc.listRelatives(driverParents[-1],c=True,type=mc.nodeType(drivers[i])):
				if  c!=drivers[i] and mc.getAttr(c+'.io')==False:
					sib=True
			driverHasSiblings.append(sib)

		drivenParents=[]
		drivenParentLists=[]
		drivenBN=[]
		for i in range(0,len(driven)):
			#if driven[i].split(':')>1:
			drivenBN.append(driven[i].split('|')[-1].split(':')[-1])
			drivenParentLists.append(iterable(mc.ls(driven[i],l=True)[0].split('|')[:-1]))
			for n in range(0,len(drivenParentLists[-1])):
				drivenParentLists[-1][n]=drivenParentLists[-1][n].split(':')[-1]
			drivenParents.extend(drivenParentLists[-1])
		
		driversHold=drivers
		drivenHold=driven
		driven=[]
		drivers=[]
				
		for i in range(0,len(driversBN)):
			
			matched=False
			
			if (driverParents[i] in drivenParents) and not driverHasSiblings[i]: # match by transform names
				for n in range(0,len(drivenParentLists)):
					if driverParents[i] in drivenParentLists[n]:
						drivers.append(driversHold[i])
						driven.append(drivenHold[n])
			elif driversBN[i] in drivenBN:	# match by shape names
				drivers.append(driversHold[i])
				driven.append(drivenHold[drivenBN.index(driversBN[i])])
						
	for i in range(0,len(drivers)):
							
		driverSh=drivers[i]
		drivenSh=driven[i]
				
		driverTr=mc.listRelatives(driverSh,p=True)[0]
		drivenTr=mc.listRelatives(drivenSh,p=True)[0]

		#drive shape
		if maintainOffset==False:
			shapeMatch=True
		else:
			shapeMatch=False
		
		if shapeMatch and mc.nodeType(driverSh)!=mc.nodeType(drivenSh):
			
			shapeMatch=False
			
		if shapeMatch and mc.nodeType(driverSh)=='nurbsCurve' or mc.nodeType(driverSh)=='nurbsSurface':
			
			if mc.ls(driverSh+'.cv[*]')!=mc.ls(drivenSh+'.cv[*]'):
				shapeMatch=False
				
		if shapeMatch and mc.nodeType(driverSh)=='mesh':
			
			if\
			(
				len(mc.ls(driverSh+'.vtx[*]',fl=True))!=len(mc.ls(drivenSh+'.vtx[*]',fl=True)) or
				len(mc.ls(driverSh+'.f[*]',fl=True))!=len(mc.ls(drivenSh+'.f[*]',fl=True)) or
				len(mc.ls(driverSh+'.e[*]',fl=True))!=len(mc.ls(drivenSh+'.e[*]',fl=True))
			):
				shapeMatch=False
				
		# try to connect with blendShape
			
		if shapeMatch:
			
			try:
				bs=BlendShape(driverSh,drivenSh,w=10,c=False)[0]
				returnVal.append(bs)
			except:
				shapeMatch=False
				
		# connect transforms
		
		mm=mc.createNode('multMatrix')
		dm=mc.createNode('decomposeMatrix')
		
		mc.connectAttr(driverTr+'.wm[0]',mm+'.i[1]')
		mc.connectAttr(drivenTr+'.pim',mm+'.i[0]')
		mc.connectAttr(mm+'.o',dm+'.imat')
		mc.connectAttr(dm+'.os',drivenTr+'.s')
		mc.connectAttr(dm+'.osh',drivenTr+'.sh')
		
		if shapeMatch:
			mc.parentConstraint(driverTr,drivenTr,mo=False)
		else:
			mc.parentConstraint(driverTr,drivenTr,mo=True)
		
		for attr in ['rp','rpt','sp','spt','ra','ro','it','rq']:
			for a in mc.listAttr(driverTr+'.'+attr):
				mc.connectAttr(driverTr+'.'+a,drivenTr+'.'+a,f=True)		
		
		if not shapeMatch: # connect with wrap

			if mc.nodeType(driverSh)=='mesh' and mc.nodeType(drivenSh)=='mesh':
				
				driverArea=mc.polyEvaluate(driverSh,a=True)
				drivenArea=mc.polyEvaluate(drivenSh,a=True)
				areaPercDiff=(driverArea-drivenArea)/drivenArea

			if mc.nodeType(driverSh)=='mesh' and mc.nodeType(drivenSh)=='mesh' and areaPercDiff>.1:			
							
				cpom=mc.createNode('closestPointOnMesh')
				mc.connectAttr(driverSh+'.worldMesh[0]',cpom+'.im')
				
				driverFaces=[]
				drivenFaces=iterable(mc.ls(drivenSh+'.f[*]',fl=True))
								
				mc.progressWindow(st='Analyzing mesh...',title='Working',max=len(drivenFaces)/20,ii=True)
				
				n=0
				for f in drivenFaces:
					
					mc.setAttr(cpom+'.ip',*midPoint(f))
					driverFaces.append(driverSh+'.f['+str(mc.getAttr(cpom+'.f'))+']')
					
					if float(n)/20.0==int(n/20):
						mc.progressWindow(e=True,s=1)
						if mc.progressWindow(q=True,ic=True):
							if mc.objExists(cpom): mc.delete(cpom)
							mc.progressWindow(e=True,ep=True)
							raise Exception('User interupt.')
					n+=1
				
				mc.progressWindow(e=True,ep=True)
								
				driverFaces=removeDuplicates(driverFaces)
				wrap=Wrap(driverFaces,drivenSh)
				if mc.objExists(cpom): mc.delete(cpom)
			else:
				wrap=Wrap(driverSh,drivenSh)
					
			returnVal.append(wrap)

		if hide[0]:
			mc.hide(driverSh)
		if hide[1]:
			mc.hide(drivenSh)

	if (fromFiles or matchByNameSpace) and len(sel)>2:
		
		return geoConnect(o=output,r=recursive,mo=maintainOffset,rv=returnVal,h=(hide[0]+hide[2:]),*(sel[0]+sel[2:]))
		
	elif output!='': # save
		
		if len(output.split('.'))<2:
			output=output+'.'+sel[0].split('.')[-1]
		
		if not os.path.isdir(os.path.dirname(output)):
			output=os.path.dirname(sel[0])+'/'+output
			
		if output.split('.')[-1]=='.ma':
			outputType='mayaAscii'
		else:
			outputType='mayaBinary'
		
		mc.file(rename=output)
		mc.file(f=True,save=True,type=outputType)
		
	else:
		
		return returnVal

