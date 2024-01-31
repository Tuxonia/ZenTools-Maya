import maya.cmds as mc
import maya.mel as mel
import maya.utils as mu
from zen.melEncode import melEncode
from zen.isIterable import isIterable
from zen.removeDuplicates import removeDuplicates
from zen.removeAll import removeAll
from zen.deferExec import deferExec
from zen.deferExec import deferExec
from zen.getBindPoses import getBindPoses
from zen.disconnectNodes import disconnectNodes
from zen.distanceBetween import distanceBetween
from zen.goToDagPose import goToDagPose
from zen.hierarchyOrder import hierarchyOrder
from zen.iterable import iterable
from zen.listNodeConnections import listNodeConnections
from zen.getIDs import getIDs
from zen.getReversed import getReversed
from zen.uniqueNames import uniqueNames
from zen.geometry import PolyEdgeList
from zen.controls import ArcCtrl
from decimal import Decimal
from zen.geometry import ClosestPoints
from zen.constraints import ParentSpace

class Rivet(list):

	def __init__(self,*args,**keywords):

		#check to make sure unique names are used in scene
		uniqueNames(iterable(mc.ls(type='dagNode')),re=True)

		#default options
		self.number=1 #if there are no transforms, create this many rivets
		self.distribute=''
		self.parents=['','']
		self.rebuild=False
		self.taper='none' # none, normal, distance
		self.scale='none' # none, uniform, or relative
		self.scaleDirection=['length','width'] # length, width
		self.createAimCurve=False
		self.aimCurve=''
		self.handles=[]
		self.handleShapes=[]
		self.autoFlexGroups=[]
		self.mo=True # maintain offset
		self.ctrls=[] #by default control attributes are placed on given transforms
		self.keepPivot=True
		self.snapToSurface=False
		self.realign=False
		self.rivets=[]
		self.ClosestPoints=[]
		self.aimGroups=[]
		self.softParents=[]
		self.ArcCtrl=[]
		self.arcWeight=.5
		self.closestPoint='' # geometry, pivot
		self.organize=True
		self.constraint=False # use a parent constraint
		self.parent=False # create a transform and parent objects to it

		self.spaceTr=''
		self.surfaceAttr=''
		self.bindPoses=[]
		self.parentSpaces=[]
		self.hasGeometry=True
		self.skipRotate=[]
		self.skipTranslate=[]
		self.skipScale=[]
		self.skipScaleObjects=[]
		self.skipRotateObjects=[]
		self.skipTranslateObjects=[]
		self.minScaleWidth=0
		self.maxScaleWidth=1
		self.minScaleLength=0
		self.maxScaleLength=1
		self.surfaceMatrix=''
		self.surfaceInverseMatrix=''
		self.worldMatrix=''
		self.trs=[]
		self.uSpans=-1
		self.vSpans=-1
		self.skins=[]

		self.shortNames=\
		{
			'sd':'scaleDirection',
			'p':'parents',
			'sp':'softParents'
		}

		sel=[]
		if len(args)==0:
			sel=mc.ls(sl=True)
		for a in args:
			sel.extend(iterable(a))

		self.bindPoses=iterable(getBindPoses(sel))

		if len(self.bindPoses)>0:
			goToDagPose(self.bindPoses[0])

		self.edges=PolyEdgeList(sel,f=True)
		self.trs=removeDuplicates(mc.ls(self.edges.etcObj,tr=True))

		if len(self.edges)==0: #look for a surface or surface attribute
			reversedObjList=getReversed(self.edges.etcObj)
			for obj in reversedObjList:
				if len(obj.split('.'))>1 and mc.getAttr(obj,type=True)=='nurbsSurface':
					self.surfaceAttr=obj
					obj=mc.ls(self.surfaceAttr,o=True)[0]
					if mc.nodeType(obj)=='nurbsSurface':
						self.uSpans=mc.getAttr(obj+'.spansU')
						self.vSpans=mc.getAttr(obj+'.spansV')
						self.spaceTr=mc.listRelatives(obj,p=True)[0]
					break
				elif mc.nodeType(obj)=='nurbsSurface':
					self.surfaceAttr=obj+'.worldSpace[0]'
					self.spaceTr=mc.listRelatives(obj,p=True)[0]
					self.uSpans=mc.getAttr(obj+'.spansU')
					self.vSpans=mc.getAttr(obj+'.spansV')
					self.trs.remove(obj)
					break
				else:
					children=mc.listRelatives(obj,c=True,s=True,ni=True,type='nurbsSurface')
					if isIterable(children) and len(children)>0:
						self.spaceTr=mc.ls(obj)[0]
						self.surfaceAttr=children[0]+'.worldSpace[0]'
						self.uSpans=mc.getAttr(children[0]+'.spansU')
						self.vSpans=mc.getAttr(children[0]+'.spansV')
						self.trs.remove(obj)
						break
		else:
			self.spaceTr=self.edges.getTr()

		for k in keywords:
			if k in self.__dict__:
				exec('self.'+k+'=keywords[k]')
			elif k in self.shortNames:
				exec('self.'+self.shortNames[k]+'=keywords[k]')

		if len(iterable(self.parents))==1:
			self.parents=[iterable(self.parents)[0],iterable(self.parents)[0]]
		if len(iterable(self.softParents))==1:
			self.softParents=[iterable(self.softParents)[0],iterable(self.softParents)[0]]

		if len(self.ctrls)==0:
			self.ctrls=self.trs
		while len(self.ctrls)<len(self.trs):
			self.ctrls.append(self.ctrls[-1])

		if len(self.skipRotate)>0:
			for i in self.skipRotate:
				self.skipRotateObjects.append(self.trs[self.skipRotate[i]])
		if len(self.skipTranslate)>0:
			for i in self.skipTranslate:
				self.skipTranslateObjects.append(self.trs[self.skipTranslate[i]])
		if len(self.skipScale)>0:
			for i in self.skipScale:
				self.skipScaleObjects.append(self.trs[self.skipScale[i]])

		if len(self.trs)>0:
			for t in self.trs:
				shCount=len\
				(
					removeDuplicates(mc.listRelatives(t,c=True,type='nurbsSurface'))+
					removeDuplicates(mc.listRelatives(t,c=True,type='nurbsCurve'))+
					removeDuplicates(mc.listRelatives(t,c=True,type='mesh'))
				)

				if shCount==0:
					self.hasGeometry=False
					self.closestPoint='pivot'
					break

		if self.closestPoint=='' and self.hasGeometry: # default to pivot if using snap to surface, otherwise defualts to geometry
			if self.snapToSurface:
				self.closestPoint='pivot'
			else:
				self.closestPoint='geometry'

		if len(self.trs)!=0:
			self.number=len(self.trs)

		if len(self.ctrls)<len(self.trs):
			self.ctrls=self.trs

		if not self.parent and not self.constraint:
			self.parent=True

		if self.createAimCurve:
			self.parent=True
			#self.constraint=False

		#find the root joint if present
		try:
			joints=removeDuplicates(mc.listConnections(iterable(mc.ls(iterable(mc.listHistory(self.surfaceAttr)))),type='joint'))
			if len(joints)>0: self.spaceTr=hierarchyOrder(joints)[0]
		except:
			pass

		self.create()

	def create(self):

		worldMatrixNode=mc.createNode('fourByFourMatrix')
		wm=\
		[
			[1,0,0,0],
			[0,1,0,0],
			[0,0,1,0],
			[0,0,0,1]
		]
		for a in range(0,4):
			for b in range(0,4):
				mc.setAttr( worldMatrixNode+'.in'+str(a)+str(b), wm[a][b] )

		self.worldMatrix=worldMatrixNode+'.o'

		wsMatrices=[]

		cleanup=[]

		lattices=[]
		uvPos=[]
		antipodes=[]

		cpos=mc.createNode('closestPointOnSurface')

		if 'surfaceAttr' not in self.__dict__ or len(self.surfaceAttr)==0 and len(self.edges)>0:
			mc.select(self.edges)
			rebuildNode,surfaceNodeTr=mel.eval('zenLoftBetweenEdgeLoopPathRings(2)')[:2]
			self.surfaceAttr=rebuildNode+'.outputSurface'

			children=mc.listRelatives(surfaceNodeTr,c=True,s=True,ni=True,type='nurbsSurface')
			if isIterable(children) and len(children)>0:
				self.uSpans=mc.getAttr(children[0]+'.spansU')
				self.vSpans=mc.getAttr(children[0]+'.spansV')

			mc.disconnectAttr(self.surfaceAttr,surfaceNodeTr+'.create')
			mc.delete(surfaceNodeTr)


		if self.uSpans<0 or self.vSpans<0:
			tempTr=mc.createNode('transform')
			tempCurve=mc.createNode('nurbsCurve',p=tempTr)
			mc.connectAttr(self.surfaceAttr,tempCurve+'.create')
			self.uSpans=mc.getAttr(tempCurve+'.spansU')
			self.vSpans=mc.getAttr(tempCurve+'.spansV')
			mc.disconnectAttr(self.surfaceAttr,tempCurve+'.create')
			mc.delete(tempTr)

		orderedTrs=[]
		orderedCtrls=[]

		if self.distribute not in ['u','v']: #calculate the axis of distribution
			if len(self.trs)!=0:
				mc.connectAttr(self.surfaceAttr,cpos+'.inputSurface')
				uMin=100
				vMin=100
				uMax=0
				vMax=0
				uPosList=[]
				vPosList=[]

				for i in range(0,self.number):

					orderedTrs.append('')
					orderedCtrls.append('')
					t=self.trs[i]

					if mc.objExists(t): # find the closest point
						if self.hasGeometry:
							center=mc.objectCenter(t)
							mc.setAttr(cpos+'.ip',*center)
							posCenter,uCenter,vCenter=mc.getAttr(cpos+'.p')[0],mc.getAttr(cpos+'.u'),mc.getAttr(cpos+'.v')

						rp=mc.xform(t,ws=True,q=True,rp=True)
						mc.setAttr(cpos+'.ip',*rp)
						posRP,uRP,vRP=mc.getAttr(cpos+'.p')[0],mc.getAttr(cpos+'.u'),mc.getAttr(cpos+'.v')

						# see which is closer - object center or rotate pivot
						if self.hasGeometry:
							distCenter=distanceBetween(posCenter,center)
							distRP=distanceBetween(posRP,rp)

						if self.hasGeometry==False or abs(distCenter)>abs(distRP) :
							uPosList.append(uRP)
							vPosList.append(vRP)
							if uRP<uMin: uMin=uRP
							if uRP>uMax: uMax=uRP
							if vRP<vMin: vMin=vRP
							if vRP>vMax: vMax=vRP
						else:
							uPosList.append(uCenter)
							vPosList.append(vCenter)
							if uCenter<uMin: uMin=uCenter
							if uCenter>uMax: uMax=uCenter
							if vCenter<vMin: vMin=vCenter
							if vCenter>vMax: vMax=vCenter

			cfsi=mc.createNode('curveFromSurfaceIso')

			mc.connectAttr(self.surfaceAttr,cfsi+'.is')
			mc.setAttr(cfsi+'.idr',0)
			mc.setAttr(cfsi+'.iv',.5)
			mc.setAttr(cfsi+'.r',True)
			mc.setAttr(cfsi+'.rv',True)

			if len(self.trs)!=0:
				mc.setAttr(cfsi+'.min',uMin)
				mc.setAttr(cfsi+'.max',uMax)

			ci=mc.createNode('curveInfo')
			mc.connectAttr(cfsi+'.oc',ci+'.ic')
			uLength=mc.getAttr(ci+'.al')

			mc.setAttr(cfsi+'.idr',1)

			if len(self.trs)!=0:
				mc.setAttr(cfsi+'.min',vMin)
				mc.setAttr(cfsi+'.max',vMax)

			vLength=mc.getAttr(ci+'.al')

			mc.delete(cfsi,ci)

			if uLength>vLength:
				self.distribute='u'

				if len(self.trs)!=0:
					searchList=uPosList
					orderedList=uPosList[:]
					orderedList.sort()
			else:
				self.distribute='v'

				if len(self.trs)!=0:
					searchList=vPosList
					orderedList=vPosList[:]
					orderedList.sort()

			reverseTrs=False

			orderIDList=[]
			for n in range(0,self.number):
				s=searchList[n]
				for i in range(0,self.number):
					if s==orderedList[i] and i not in orderIDList:
						orderIDList.append(i)
						orderedTrs[i]=self.trs[n]
						orderedCtrls[i]=self.ctrls[n]
						if n==0 and i>len(self.trs)/2:
							reverseTrs=True
						break

			if reverseTrs:
				orderedTrs.reverse()
				self.trs=orderedTrs
				orderedCtrls.reverse()
				self.ctrls=orderedCtrls
			else:
				self.trs=orderedTrs
				self.ctrls=orderedCtrls

		if self.rebuild: # interactive rebuild, maintains even parameterization over the rivet surface, use with caution

			if self.distribute=='u':
				self.surfaceAttr=mel.eval('zenUniformSurfaceRebuild("'+self.surfaceAttr+'",'+str(self.uSpans*2)+',-1)')+'.outputSurface'
			else:
				self.surfaceAttr=mel.eval('zenUniformSurfaceRebuild("'+self.surfaceAttr+'",-1,'+str(self.vSpans*2)+')')+'.outputSurface'

		if not mc.isConnected(self.surfaceAttr,cpos+'.inputSurface'):
			mc.connectAttr(self.surfaceAttr,cpos+'.inputSurface',f=True)

		if self.taper=='distance' or self.createAimCurve or self.closestPoint=='geometry': # find the closest points ( and antipodes )

			for i in range(0,self.number):
				t=self.trs[i]
				cp=ClosestPoints(self.surfaceAttr,t)
				self.ClosestPoints.append(cp)

				if self.taper=='distance' or self.createAimCurve: # antipodes are used for lattice allignment and curve calculations
					antipodes.append(cp.getAntipodes(1))

		if self.taper!='none' or self.scale!='none': # measures scale with scaling

			cfsiLength=mc.createNode('curveFromSurfaceIso')
			ciLength=mc.createNode('curveInfo')
			lengthMultiplierNode=mc.createNode('multDoubleLinear')

			mc.setAttr(cfsiLength+'.relative',True)
			mc.setAttr(cfsiLength+'.relativeValue',True)

			if self.distribute=='u':
				mc.setAttr(cfsiLength+'.isoparmDirection',0)
			else:
				mc.setAttr(cfsiLength+'.isoparmDirection',1)

			mc.setAttr(cfsiLength+'.minValue',0)
			mc.setAttr(cfsiLength+'.maxValue',1)

			mc.setAttr(cfsiLength+".isoparmValue",.5)

			mc.connectAttr(self.surfaceAttr,cfsiLength+'.inputSurface')

			if mc.objExists(self.spaceTr):

				lengthCurve=mc.createNode('nurbsCurve',p=self.spaceTr)
				lengthCurveTG=mc.createNode('transformGeometry')

				mc.connectAttr(self.spaceTr+'.worldMatrix[0]',lengthCurveTG+'.txf')
				mc.connectAttr(cfsiLength+'.outputCurve',lengthCurveTG+'.ig')
				mc.connectAttr(lengthCurveTG+'.og',lengthCurve+'.create')
				mc.connectAttr(lengthCurve+'.worldSpace',ciLength+'.inputCurve')
				mc.setAttr(lengthCurve+'.intermediateObject',True)

				cleanup.extend([lengthCurveTG,cfsiLength])

			else:

				mc.connectAttr(cfsiLength+'.outputCurve',ciLength+'.inputCurve')

			mc.connectAttr(ciLength+'.al',lengthMultiplierNode+'.i1')
			mc.setAttr(lengthMultiplierNode+'.i2',1.0/float(mc.getAttr(ciLength+'.al')))

			lengthMultiplier=lengthMultiplierNode+'.o'


		uvPos=[]
		closestDistanceToCenter=Decimal('infinity')
		centerMostRivetID=0
		closestDistancesToCenter=[Decimal('infinity'),Decimal('infinity')]
		centerMostRivetIDs=[0,0]

		uvMultipliers=[]
		aimGroups=[]

		for i in range(0,self.number):

			pTrs=mc.listRelatives(self.trs[i],p=True)
			parentTr=''
			if len(iterable(pTrs))>0:
				parentTr=pTrs[0]

			t=self.trs[i]
			c=self.ctrls[i]
			r=mc.createNode('transform',n='Rivet#')

			wsMatrices.append(mc.xform(t,q=True,ws=True,m=True))

			if self.constraint: mc.setAttr(r+'.inheritsTransform',False)

			if not mc.objExists(c):
				c=t
				if not mc.objExists(t):
					c=r

			if not mc.objExists(c+'.zenRivet'):
				mc.addAttr(c,at='message',ln='zenRivet',sn='zriv')

			mc.connectAttr(r+'.message',c+'.zriv',f=True)

			if not mc.objExists(c+'.uPos'):
				mc.addAttr(c,k=True,at='double',ln='uPos',dv=50)
			if not mc.objExists(c+'.vPos'):
				mc.addAttr(c,k=True,at='double',ln='vPos',dv=50)

			if self.closestPoint=='geometry':
				up,vp=self.ClosestPoints[i].uvs[0]
			else:
				if mc.objExists(t):
					if self.hasGeometry:
						center=mc.objectCenter(t)
						mc.setAttr(cpos+'.ip',*center)
						posCenter,uCenter,vCenter=mc.getAttr(cpos+'.p')[0],mc.getAttr(cpos+'.u'),mc.getAttr(cpos+'.v')

					rp=mc.xform(t,ws=True,q=True,rp=True)
					mc.setAttr(cpos+'.ip',*rp)
					posRP,uRP,vRP=mc.getAttr(cpos+'.p')[0],mc.getAttr(cpos+'.u'),mc.getAttr(cpos+'.v')

					if self.hasGeometry:
						distCenter=distanceBetween(posCenter,center)
						distRP=distanceBetween(posRP,rp)

					if self.hasGeometry==False or abs(distCenter)>abs(distRP):
						up=uRP
						vp=vRP
					else:
						up=uCenter
						vp=vCenter

				elif len(distribute)>0:

					if self.distribute=='u':
						up=(i+1)/self.number
						vp=.5
					else:
						up=.5
						vp=(i+1)/self.number

			if up>float(self.uSpans)-.01: up=float(self.uSpans)-.01
			if vp>float(self.vSpans)-.01: vp=float(self.vSpans)-.01
			if up<.01: up=.01
			if vp<.01: vp=.01

			uvPos.append((up,vp))

			if up<.5 and self.distribute=='u' and Decimal(str(abs(.5-up)))<Decimal(str(closestDistancesToCenter[0])):
				closestDistancesToCenter[0]=abs(.5-up)
				centerMostRivetIDs[0]=i

			if up>.5 and self.distribute=='u' and Decimal(str(abs(.5-up)))<Decimal(str(closestDistancesToCenter[1])):
				closestDistancesToCenter[1]=abs(.5-up)
				centerMostRivetIDs[1]=i

			if up<.5 and self.distribute=='v' and Decimal(str(abs(.5-vp)))<Decimal(str(closestDistancesToCenter[0])):
				closestDistancesToCenter[0]=abs(.5-vp)
				centerMostRivetIDs[0]=i

			if up>.5 and self.distribute=='v' and Decimal(str(abs(.5-vp)))<Decimal(str(closestDistancesToCenter[1])):
				closestDistancesToCenter[1]=abs(.5-vp)
				centerMostRivetIDs[1]=i

			mc.setAttr(c+'.uPos',up*100)
			mc.setAttr(c+'.vPos',vp*100)

			posi=mc.createNode('pointOnSurfaceInfo')
			mc.setAttr((posi+".caching"),True)
			#mc.setAttr((posi+".top"),True)

			multiplyU=mc.createNode('multDoubleLinear')
			mc.connectAttr(c+".uPos",multiplyU+".i1")
			mc.setAttr(multiplyU+'.i2',.01)
			multiplyV=mc.createNode('multDoubleLinear')
			mc.connectAttr(c+".vPos",multiplyV+".i1")
			mc.setAttr(multiplyV+'.i2',.01)

			uvMultipliers.append([multiplyU,multiplyV])

			mc.connectAttr(self.surfaceAttr,posi+".inputSurface");
			mc.connectAttr(multiplyU+".o",posi+".parameterU")
			mc.connectAttr(multiplyV+".o",posi+".parameterV")

			dm=mc.createNode('decomposeMatrix')
			mc.setAttr(dm+'.caching',True)
			fbfm=mc.createNode('fourByFourMatrix')
			mc.setAttr(fbfm+'.caching',True)

			mc.connectAttr(posi+'.nnx',fbfm+'.in00')
			mc.connectAttr(posi+'.nny',fbfm+'.in01')
			mc.connectAttr(posi+'.nnz',fbfm+'.in02')
			mc.connectAttr(posi+'.nux',fbfm+'.in10')
			mc.connectAttr(posi+'.nuy',fbfm+'.in11')
			mc.connectAttr(posi+'.nuz',fbfm+'.in12')
			mc.connectAttr(posi+'.nvx',fbfm+'.in20')
			mc.connectAttr(posi+'.nvy',fbfm+'.in21')
			mc.connectAttr(posi+'.nvz',fbfm+'.in22')
			mc.connectAttr(posi+'.px',fbfm+'.in30')
			mc.connectAttr(posi+'.py',fbfm+'.in31')
			mc.connectAttr(posi+'.pz',fbfm+'.in32')

			if self.constraint:# and not self.parent:
				mc.connectAttr(fbfm+'.output',dm+'.inputMatrix')
			else:
				multMatrix=mc.createNode('multMatrix')
				mc.connectAttr(r+'.parentInverseMatrix',multMatrix+'.i[1]')
				mc.connectAttr(fbfm+'.output',multMatrix+'.i[0]')
				mc.connectAttr(multMatrix+'.o',dm+'.inputMatrix')

			mc.connectAttr(dm+'.outputTranslate',r+'.t')
			mc.connectAttr(dm+'.outputRotate',r+'.r')

			if t!=r:

				if self.createAimCurve:
					aimGroup=mc.createNode('transform',n='rivetAimGrp#')
					mc.parent(aimGroup,t,r=True)
					mc.parent(aimGroup,r)
					if self.keepPivot or self.closestPoint=='pivot':
						mc.xform(aimGroup,ws=True,piv=mc.xform(t,q=True,ws=True,rp=True))
					else:
						mc.xform(aimGroup,ws=True,piv=self.ClosestPoints[i][1])
					self.aimGroups.append(aimGroup)

				if self.constraint:

					if self.parent: # parent and constraint == ParentSpace

						self.parentSpaces.append(ParentSpace(t,r))
						pc=self.parentSpaces[i].parentConstraint

						sc=self.parentSpaces[i].scaleConstraint

						skip=['x']
						if\
						(
							(self.distribute=='v' and 'length' in self.scaleDirection) or
							(self.distribute=='u' and 'width' in self.scaleDirection) or
							t in self.skipScaleObjects
						):
							skip.append('y')
						if\
						(
							(self.distribute=='u' and 'length' in self.scaleDirection) or
							(self.distribute=='v' and 'width' in self.scaleDirection) or
							t in self.skipScaleObjects
						):
							skip.append('z')

						mc.scaleConstraint(sc,e=True,sk=skip)

						if t in self.skipRotateObjects:
							mc.parentConstraint(pc,e=True,sr=('x','y','z'))
						if t in self.skipTranslateObjects:
							mc.parentConstraint(pc,e=True,st=('x','y','z'))

					else: #just constraint

						if t in self.skipRotateObjects:
							pc=mc.parentConstraint(r,t,sr=('x','y','z'),mo=True)[0]#
						if t in self.skipTranslateObjects:
							pc=mc.parentConstraint(r,t,st=('x','y','z'),mo=self.mo)[0]
						if t not in self.skipRotateObjects and t not in self.skipTranslateObjects:
							pc=mc.parentConstraint(r,t,mo=self.mo)[0]



					pcTargets=mc.parentConstraint(pc,q=True,tl=True)

					pcIDs=[]

					nsc=listNodeConnections(r,pc,s=False,d=True)

					for n in range(0,len(nsc)):
						if len(nsc[n])==2 and mc.objExists(nsc[n][-1]):
							pcID=getIDs(nsc[n][-1])
							if isinstance(pcID,int):
								pcIDs.append(pcID)

					pcIDs=removeDuplicates(pcIDs)

					for pcID in pcIDs:
						mc.connectAttr(self.worldMatrix,pc+'.tg['+str(pcID)+'].tpm',f=True)
						mc.connectAttr(dm+'.outputTranslate',pc+'.tg['+str(pcID)+'].tt',f=True)
						mc.connectAttr(dm+'.outputRotate',pc+'.tg['+str(pcID)+'].tr',f=True)

					cleanup.append(r)

					if self.parent:

						scTargets=mc.scaleConstraint(sc,q=True,tl=True)

						scIDs=[]

						nsc=listNodeConnections(r,sc,s=False,d=True)

						for n in range(0,len(nsc)):
							if len(nsc[n])==2 and mc.objExists(nsc[n][-1]):
								scIDs.append(getIDs(nsc[n][-1]))

						scIDs=removeDuplicates(scIDs)

						scMD=mc.createNode('multiplyDivide')
						mc.setAttr(scMD+'.i1',1,1,1)
						mc.setAttr(scMD+'.i2',1,1,1)

						for scID in scIDs:

							mc.connectAttr(self.worldMatrix,sc+'.tg['+str(scID)+'].tpm',f=True)
							#mc.connectAttr(scMD+'.o',sc+'.tg['+str(scID)+'].ts',f=True)
							mc.connectAttr(scMD+'.ox',sc+'.tg['+str(scID)+'].tsx',f=True)
							mc.connectAttr(scMD+'.oy',sc+'.tg['+str(scID)+'].tsy',f=True)
							mc.connectAttr(scMD+'.oz',sc+'.tg['+str(scID)+'].tsz',f=True)

						r=self.parentSpaces[i][0]
						#xfm=mc.xform(r,q=True,ws=True,m=True)
						#mc.setAttr(r+'.inheritsTransform',False)
						#mc.xform(r,m=xfm)
						#mc.connectAttr(self.surfaceMatrix,multMatrix+'.i[1]',f=True)#self.parentSpaces[i][0]+'.parentInverseMatrix'

				elif self.createAimCurve:
					mc.parent(t,w=True)
					mc.setAttr(t+'.inheritsTransform',False)
					mc.parent(t,r,r=True)
				else:
					mc.parent(t,r)

				if mc.objExists(parentTr) and (self.parent or self.createAimCurve) and not self.constraint:

					if not (parentTr in iterable(mc.listRelatives(r,p=True))):

						if mc.getAttr(r+'.inheritsTransform')==True:
							mc.parent(r,parentTr,r=True)
						else:
							mc.parent(r,parentTr)

					if mc.getAttr(r+'.inheritsTransform')==False:

						dm=mc.createNode('decomposeMatrix')
						mc.connectAttr(parentTr+'.worldMatrix',dm+'.inputMatrix')
						mc.connectAttr(dm+'.os',t+'.s',f=True)

			if self.taper!='none' or self.scale!='none':

				cfsiU=mc.createNode('curveFromSurfaceIso')

				mc.setAttr(cfsiU+'.relative',True)
				mc.setAttr(cfsiU+'.relativeValue',True)
				mc.setAttr(cfsiU+'.isoparmDirection',0)
				mc.setAttr(cfsiU+'.minValue',0)
				mc.setAttr(cfsiU+'.maxValue',1)

				mc.connectAttr(multiplyV+".o",cfsiU+".isoparmValue")
				mc.connectAttr(self.surfaceAttr,cfsiU+'.inputSurface')

				cfsiV=mc.createNode('curveFromSurfaceIso')

				mc.setAttr(cfsiV+'.relative',True)
				mc.setAttr(cfsiV+'.relativeValue',True)
				mc.setAttr(cfsiV+'.isoparmDirection',1)
				mc.setAttr(cfsiV+'.minValue',0)
				mc.setAttr(cfsiV+'.maxValue',1)

				mc.connectAttr(multiplyV+".o",cfsiV+".isoparmValue")
				mc.connectAttr(self.surfaceAttr,cfsiV+'.inputSurface')

				subtractNode=mc.createNode('addDoubleLinear')
				mc.setAttr(subtractNode+'.i1',-(1/(self.number*2)))
				addNode=mc.createNode('addDoubleLinear')
				mc.setAttr(addNode+'.i1',1/(self.number*2))
				addSubClampNode=mc.createNode('clamp')
				mc.setAttr(addSubClampNode+'.min',0,0,0)
				mc.setAttr(addSubClampNode+'.max',1,1,1)
				mc.connectAttr(subtractNode+'.o',addSubClampNode+'.inputR')
				mc.connectAttr(addNode+'.o',addSubClampNode+'.inputG')

				if self.distribute=='u':
					mc.connectAttr(multiplyU+".o",subtractNode+".i2")
					mc.connectAttr(multiplyU+".o",addNode+".i2")
					mc.connectAttr(addSubClampNode+'.outputR',cfsiU+'.minValue')
					mc.connectAttr(addSubClampNode+'.outputG',cfsiU+'.maxValue')
				else:
					mc.connectAttr(multiplyV+".o",subtractNode+".i2")
					mc.connectAttr(multiplyV+".o",addNode+".i2")
					mc.connectAttr(addSubClampNode+'.outputR',cfsiV+'.minValue')
					mc.connectAttr(addSubClampNode+'.outputG',cfsiV+'.maxValue')

				ciU=mc.createNode('curveInfo')
				mc.connectAttr(cfsiU+'.outputCurve',ciU+'.inputCurve')

				ciV=mc.createNode('curveInfo')
				mc.connectAttr(cfsiV+'.outputCurve',ciV+'.inputCurve')

				mdlU=mc.createNode('multDoubleLinear')
				mc.connectAttr(ciU+'.al',mdlU+'.i1')
				mc.setAttr(mdlU+'.i2',1/float(mc.getAttr(ciU+'.al')))

				mdlV=mc.createNode('multDoubleLinear')
				mc.connectAttr(ciV+'.al',mdlV+'.i1')
				mc.setAttr(mdlV+'.i2',1/float(mc.getAttr(ciV+'.al')))

				if not mc.objExists(c+'.minScaleWidth'): mc.addAttr(c,ln='minScaleWidth',at='double',k=True,min=0,dv=self.minScaleWidth)
				if not mc.objExists(c+'.maxScaleWidth'): mc.addAttr(c,ln='maxScaleWidth',at='double',k=True,min=0,dv=self.maxScaleWidth)
				if not mc.objExists(c+'.minScaleLength'): mc.addAttr(c,ln='minScaleLength',at='double',k=True,min=0,dv=self.minScaleLength)
				if not mc.objExists(c+'.maxScaleLength'): mc.addAttr(c,ln='maxScaleLength',at='double',k=True,min=0,dv=self.maxScaleLength)

				clampNode=mc.createNode('clamp')

				minScaleLengthNode=mc.createNode('multDoubleLinear')
				maxScaleLengthNode=mc.createNode('multDoubleLinear')
				minScaleWidthNode=mc.createNode('multDoubleLinear')
				maxScaleWidthNode=mc.createNode('multDoubleLinear')

				mc.connectAttr(c+'.minScaleLength',minScaleLengthNode+'.i1')
				mc.connectAttr(lengthMultiplier,minScaleLengthNode+'.i2')

				mc.connectAttr(c+'.maxScaleLength',maxScaleLengthNode+'.i1')
				mc.connectAttr(lengthMultiplier,maxScaleLengthNode+'.i2')

				mc.connectAttr(c+'.minScaleWidth',minScaleWidthNode+'.i1')
				mc.connectAttr(lengthMultiplier,minScaleWidthNode+'.i2')

				mc.connectAttr(c+'.maxScaleWidth',maxScaleWidthNode+'.i1')
				mc.connectAttr(lengthMultiplier,maxScaleWidthNode+'.i2')

				if self.distribute=='u':
					mc.connectAttr(minScaleLengthNode+'.o',clampNode+'.minR')
					mc.connectAttr(maxScaleLengthNode+'.o',clampNode+'.maxR')
					mc.connectAttr(minScaleWidthNode+'.o',clampNode+'.minG')
					mc.connectAttr(maxScaleWidthNode+'.o',clampNode+'.maxG')
				else:
					mc.connectAttr(minScaleWidthNode+'.o',clampNode+'.minR')
					mc.connectAttr(maxScaleWidthNode+'.o',clampNode+'.maxR')
					mc.connectAttr(minScaleLengthNode+'.o',clampNode+'.minG')
					mc.connectAttr(maxScaleLengthNode+'.o',clampNode+'.maxG')

				mc.connectAttr(mdlU+'.o',clampNode+'.ipr')
				mc.connectAttr(mdlV+'.o',clampNode+'.ipg')

				if self.scale=='relative' and self.parent:#or len(self.scaleDirection)<2:#

					if\
					(
						(self.distribute=='u' and 'length' in self.scaleDirection) or
						(self.distribute=='v' and 'width' in self.scaleDirection)
					):
						if self.constraint:
							mc.connectAttr(clampNode+'.opr',scMD+'.i1y')
						else:
							mc.connectAttr(clampNode+'.opr',r+'.sy',f=True)
					if\
					(
						(self.distribute=='v' and 'length' in self.scaleDirection) or
						(self.distribute=='u' and 'width' in self.scaleDirection)
					):
						if self.constraint:
							mc.connectAttr(clampNode+'.opg',scMD+'.i1z')
						else:
							mc.connectAttr(clampNode+'.opg',r+'.sz',f=True)


				elif self.taper!='none' and self.parent:

					#self.autoFlexGroups

					mc.setAttr(t+'.sx',lock=True)
					mc.setAttr(t+'.sy',lock=True)
					mc.setAttr(t+'.sz',lock=True)
					mc.setAttr(t+'.tx',lock=True)
					mc.setAttr(t+'.ty',lock=True)
					mc.setAttr(t+'.tz',lock=True)
					mc.setAttr(t+'.rx',lock=True)
					mc.setAttr(t+'.ry',lock=True)
					mc.setAttr(t+'.rz',lock=True)

					aimTr=mc.createNode('transform',p=t)
					mc.xform(aimTr,ws=True,t=antipodes[i])

					#mc.setAttr(db+'.p1',*self.ClosestPoints[i][0])
					#mc.setAttr(db+'.p2',*antipodes[i])
					axisLength=distanceBetween(self.ClosestPoints[i][0],antipodes[i])#mc.getAttr(db+'.d')

					ffd,lattice,latticeBase=mc.lattice(t,divisions=(2,2,2),objectCentered=True,ol=1)
					latticeLowEndPoints=mc.ls(lattice+'.pt[0:1][0:0][0:1]',fl=True)
					latticeHighEndPoints=mc.ls(lattice+'.pt[0:1][1:1][0:1]',fl=True)

					mc.parent(latticeBase,lattice)

					mc.setAttr(lattice+'.sy',axisLength)

					lattices.append([ffd,lattice,latticeBase])

					mc.parent(lattice,t)
					mc.xform(lattice,ws=True,a=True,t=mc.xform(r,q=True,ws=True,a=True,rp=True))
					mc.xform(lattice,os=True,a=True,ro=(0,0,0))
					mc.move(0,axisLength/2,0,lattice,r=True,os=True,wd=True)

					xSum,ySum,zSum=0,0,0
					for p in latticeLowEndPoints:
						px,py,pz=mc.pointPosition(p,w=True)
						xSum+=px
						ySum+=py
						zSum+=pz

					mc.xform(lattice,ws=True,piv=(xSum/len(latticeLowEndPoints),ySum/len(latticeLowEndPoints),zSum/len(latticeLowEndPoints)))
					mc.xform(latticeBase,ws=True,piv=(xSum/len(latticeLowEndPoints),ySum/len(latticeLowEndPoints),zSum/len(latticeLowEndPoints)))

					ac=mc.aimConstraint(aimTr,lattice,aim=(0,1,0),wut='objectrotation',wuo=r,u=(0,0,1),mo=False)
					mc.delete(ac)

					ac=mc.aimConstraint(aimTr,aimGroup,aim=(0,1,0),wut='objectrotation',wuo=r,u=(0,0,1),mo=False)
					mc.delete(ac,aimTr)

					lowEndCluster,lowEndClusterHandle=mc.cluster(latticeLowEndPoints)[:2]
					highEndCluster,highEndClusterHandle=mc.cluster(latticeHighEndPoints)[:2]

					lowEndClusterHandleShape=mc.listRelatives(lowEndClusterHandle,c=True)[0]
					highEndClusterHandleShape=mc.listRelatives(highEndClusterHandle,c=True)[0]

					#mc.parent(highEndClusterHandle,t)

					if mc.isConnected(lowEndClusterHandleShape+'.clusterTransforms[0]',lowEndCluster+'.clusterXforms'):
						mc.disconnectAttr(lowEndClusterHandleShape+'.clusterTransforms[0]',lowEndCluster+'.clusterXforms')
					if mc.isConnected(highEndClusterHandleShape+'.clusterTransforms[0]',highEndCluster+'.clusterXforms'):
						mc.disconnectAttr(highEndClusterHandleShape+'.clusterTransforms[0]',highEndCluster+'.clusterXforms')

					self.autoFlexGroups.append\
					(
						(
							mc.createNode('transform',n='rivetBaseAutoFlex#',p=r),
							mc.createNode('transform',n='rivetEndAutoFlex#',p=aimGroup)
						)
					)

					self.handles.append\
					(
						(
							mc.createNode('transform',n='rivetBaseCtrl#',p=self.autoFlexGroups[i][0]),
							mc.createNode('transform',n='rivetEndCtrl#',p=self.autoFlexGroups[i][1])
						)
					)

					self.handleShapes.append\
					(
						(
							mc.createNode('locator',p=self.handles[i][0]),
							mc.createNode('locator',p=self.handles[i][1])
						)
					)

					mc.setAttr(self.handleShapes[i][0]+'.los',.5,.5,.5)
					mc.setAttr(self.handleShapes[i][1]+'.los',.5,.5,.5)

					mc.xform(self.autoFlexGroups[i][0],ws=True,a=True,t=mc.xform(t,q=True,ws=True,rp=True))
					mc.xform(self.autoFlexGroups[i][0],ws=True,a=True,piv=mc.xform(t,q=True,ws=True,rp=True))

					for bp in self.bindPoses: mc.dagPose((self.handles[i][0],self.handles[i][1]),a=True,n=bp)

					mc.xform(self.autoFlexGroups[i][1],ws=True,t=antipodes[i])

					mc.hide(lattice)

					mc.connectAttr(self.handles[i][0]+'.worldInverseMatrix[0]',lowEndCluster+'.bindPreMatrix',f=True)
					mc.disconnectAttr(self.handles[i][0]+'.worldInverseMatrix[0]',lowEndCluster+'.bindPreMatrix')

					mc.connectAttr(self.handles[i][0]+'.worldMatrix[0]',lowEndCluster+'.matrix',f=True)

					mc.connectAttr(self.handles[i][1]+'.worldInverseMatrix[0]',highEndCluster+'.bindPreMatrix',f=True)
					mc.disconnectAttr(self.handles[i][1]+'.worldInverseMatrix[0]',highEndCluster+'.bindPreMatrix')

					mc.connectAttr(self.handles[i][1]+'.worldMatrix[0]',highEndCluster+'.matrix',f=True)

					aimGroups.append(aimGroup)

					if self.distribute=='u':
						mc.connectAttr(clampNode+'.opr',self.autoFlexGroups[i][0]+'.sy')
					else:
						mc.connectAttr(clampNode+'.opg',self.autoFlexGroups[i][0]+'.sz')

					mc.delete([lowEndClusterHandle,highEndClusterHandle])

				self.rivets.append(r)

		if self.createAimCurve and self.parent:

			pmm=mc.createNode('pointMatrixMult')
			arcPoints=[]
			ids=[0,centerMostRivetIDs[0],centerMostRivetIDs[1],-1]

			for id in ids:

				measureTr=mc.createNode('transform')
				aimTr=mc.createNode('transform',p=self.trs[id])
				mc.parent(measureTr,self.trs[id])

				mc.xform(aimTr,ws=True,t=antipodes[id])
				mc.xform(measureTr,ws=True,t=mc.xform(self.rivets[id],q=True,ws=True,a=True,rp=True))
				#mc.xform(measureTr,os=True,a=True,ro=(0,0,0),s=(1,1,1))

				ac=mc.aimConstraint(aimTr,measureTr,aim=(0,1,0),wut='objectrotation',wuo=self.rivets[id],u=(0,0,1),mo=False)
				mc.delete(ac,aimTr)

				mc.connectAttr(measureTr+'.worldInverseMatrix',pmm+'.inMatrix',f=True)

				maxYID=-1
				maxY=0.0
				yVal=0.0

				for i in range(0,self.number):

					mc.setAttr(pmm+'.ip',*antipodes[i])
					yVal=mc.getAttr(pmm+'.oy')
					if yVal>maxY:
						maxY=yVal
						maxYID=i

				mc.setAttr(pmm+'.ip',*antipodes[maxYID])

				oy=mc.getAttr(pmm+'.oy')

				mc.setAttr(pmm+'.ip',*antipodes[id])

				ox=mc.getAttr(pmm+'.ox')
				oz=mc.getAttr(pmm+'.oz')

				mc.connectAttr(measureTr+'.worldMatrix',pmm+'.inMatrix',f=True)
				mc.setAttr(pmm+'.ip',ox,oy,oz)

				ap=mc.getAttr(pmm+'.o')[0]

				arcPoints.append(ap)

				mc.disconnectAttr(measureTr+'.worldMatrix',pmm+'.inMatrix')

				mc.delete(measureTr)

			mc.delete(pmm)

			arcCtrlArg=arcPoints
			arcCtrlKeys={'arcWeight':self.arcWeight,'p':self.parents,'sp':self.softParents}

			for k in arcCtrlKeys:
				if type(arcCtrlKeys[k]).__name__=='NoneType':
					del(arcCtrlKeys[k])

			self.ArcCtrl=ArcCtrl(*arcCtrlArg,**arcCtrlKeys)

			mc.addAttr(self.ArcCtrl[0],at='bool',ln='showHandles',k=True,dv=False)
			mc.setAttr(self.ArcCtrl[0]+'.showHandles',k=False,cb=True)
			mc.setAttr(self.ArcCtrl[0]+'.v',k=False,cb=True)
			mc.setAttr(self.ArcCtrl[1]+'.v',k=False,cb=True)

			for h in self.handles:
				mc.connectAttr(self.ArcCtrl[0]+'.showHandles',h[0]+'.v')
				mc.connectAttr(self.ArcCtrl[0]+'.showHandles',h[1]+'.v')

			for bp in self.bindPoses: mc.dagPose(self.ArcCtrl,a=True,n=bp)

			cpoc=mc.createNode('closestPointOnCurve')
			mc.connectAttr(self.ArcCtrl.outputCurve,cpoc+'.inCurve')

			for i in range(0,self.number):

				aimTr=mc.createNode('transform')
				poci=mc.createNode('pointOnCurveInfo')
				dm=mc.createNode('decomposeMatrix')
				fbfm=mc.createNode('fourByFourMatrix')

				mc.connectAttr(poci+'.nnx',fbfm+'.in00')
				mc.connectAttr(poci+'.nny',fbfm+'.in01')
				mc.connectAttr(poci+'.nnz',fbfm+'.in02')
				mc.connectAttr(poci+'.ntx',fbfm+'.in10')
				mc.connectAttr(poci+'.nty',fbfm+'.in11')
				mc.connectAttr(poci+'.ntz',fbfm+'.in12')

				mc.connectAttr(self.ArcCtrl.outputNormal+'X',fbfm+'.in20')
				mc.connectAttr(self.ArcCtrl.outputNormal+'Y',fbfm+'.in21')
				mc.connectAttr(self.ArcCtrl.outputNormal+'Z',fbfm+'.in22')

				mc.connectAttr(poci+'.px',fbfm+'.in30')
				mc.connectAttr(poci+'.py',fbfm+'.in31')
				mc.connectAttr(poci+'.pz',fbfm+'.in32')

				mc.connectAttr(fbfm+'.output',dm+'.inputMatrix')
				mc.connectAttr(dm+'.outputTranslate',aimTr+'.t')
				mc.connectAttr(dm+'.outputRotate',aimTr+'.r')

				mc.setAttr(cpoc+'.ip',*antipodes[i])
				cpu=mc.getAttr(cpoc+'.u')
				mc.setAttr(poci+'.parameter',cpu)

				mc.connectAttr(self.ArcCtrl.outputCurve,poci+'.inputCurve')

				ac=mc.aimConstraint(aimTr,self.aimGroups[i],aim=(0,1,0),wut='objectrotation',wuo=aimTr,u=(0,0,1),mo=not(self.realign))[0]

				disconnectNodes(aimTr,ac)

				mc.connectAttr(fbfm+'.output',ac+'.worldUpMatrix',f=True)
				mc.connectAttr(dm+'.ot',ac+'.target[0].targetTranslate',f=True)

				mc.delete(aimTr)

				sc=mc.createNode('subCurve')

				mc.setAttr(sc+'.relative',True)
				mc.setAttr(sc+'.minValue',0)
				mc.setAttr(sc+'.maxValue',1)

				mc.connectAttr(self.ArcCtrl.outputCurve,sc+'.ic')

				if self.distribute=='u':
					uMultAttr=uvMultipliers[i][0]+".o"
				else:
					uMultAttr=uvMultipliers[i][1]+".o"

				#adjust for offset

				multOffsetCalc=mc.createNode('multDoubleLinear')
				mc.setAttr(multOffsetCalc+'.i1',1/mc.getAttr(uMultAttr))
				mc.connectAttr(uMultAttr,multOffsetCalc+'.i2')

				multOffset=mc.createNode('multDoubleLinear')
				mc.setAttr(multOffset+'.i1',cpu)
				mc.connectAttr(multOffsetCalc+'.o',multOffset+'.i2')

				mc.connectAttr(multOffset+'.o',poci+'.parameter',f=True)

				subtractNode=mc.createNode('addDoubleLinear')
				mc.setAttr(subtractNode+'.i1',-(1.0/(self.number*2)))
				addNode=mc.createNode('addDoubleLinear')
				mc.setAttr(addNode+'.i1',1.0/(self.number*2))
				addSubClampNode=mc.createNode('clamp')
				mc.setAttr(addSubClampNode+'.min',0,0,0)
				mc.setAttr(addSubClampNode+'.max',1,1,1)
				mc.connectAttr(subtractNode+'.o',addSubClampNode+'.inputR')
				mc.connectAttr(addNode+'.o',addSubClampNode+'.inputG')

				mc.connectAttr(multOffset+".o",subtractNode+".i2")
				mc.connectAttr(multOffset+".o",addNode+".i2")
				mc.connectAttr(addSubClampNode+'.outputR',sc+'.minValue')
				mc.connectAttr(addSubClampNode+'.outputG',sc+'.maxValue')

				ciU=mc.createNode('curveInfo')
				mc.connectAttr(sc+'.outputCurve',ciU+'.inputCurve')

				mdlU=mc.createNode('multDoubleLinear')
				mc.connectAttr(ciU+'.al',mdlU+'.i1')
				mc.setAttr(mdlU+'.i2',1/float(mc.getAttr(ciU+'.al')))

				clampNode=mc.createNode('clamp')

				if not mc.objExists(c+'.minScaleEnd'): mc.addAttr(self.ctrls[i],ln='minScaleEnd',at='double',k=True,min=0,max=1,dv=0)
				if not mc.objExists(c+'.maxScaleEnd'): mc.addAttr(self.ctrls[i],ln='maxScaleEnd',at='double',k=True,min=0,dv=1)

				mc.connectAttr(self.ctrls[i]+'.minScaleEnd',clampNode+'.minR')
				mc.connectAttr(self.ctrls[i]+'.maxScaleEnd',clampNode+'.maxR')

				mc.connectAttr(mdlU+'.o',clampNode+'.ipr')

				if self.distribute=='u':
					mc.connectAttr(clampNode+'.opr',self.autoFlexGroups[i][1]+'.sz')
				else:
					mc.connectAttr(clampNode+'.opr',self.autoFlexGroups[i][1]+'.sy')

			mc.delete(cpoc)

		if self.parent:
			self[:]=self.rivets
		else:
			self[:]=self.trs
		#if self.mo:
		#	#for i in len(self.trs):
		#		#try: mc.xform(t,q=True,ws=True,m=wsMatrices[i]))
		#		#except: pass

		cleanup.append(cpos)

		for c in cleanup:
			if mc.objExists(c):
				disconnectNodes(c)
				mc.delete(c)

		if self.snapToSurface:
			if self.createAimCurve or self.taper:
				for i in range(0,self.number):
					mc.xform(self.handles[i][0],ws=True,t=mc.xform(self.rivets[i],q=True,ws=True,rp=True))
					mc.xform(self.trs[i],ws=True,rp=mc.xform(self.rivets[i],q=True,ws=True,rp=True))
			else:
				for i in range(0,self.number):
					mc.xform(self.trs[i],ws=True,t=mc.xform(self.rivets[i],q=True,ws=True,rp=True))
					mc.xform(self.trs[i],ws=True,ro=mc.xform(self.rivets[i],q=True,ws=True,ro=True))

def doRivet(*args,**keywords):
	return Rivet(*args,**keywords)
