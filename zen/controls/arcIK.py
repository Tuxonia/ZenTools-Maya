import maya.cmds as mc
import maya.mel as mel
import maya.utils as mu
from zen.melEncode import melEncode
from zen.isIterable import isIterable
from zen.removeDuplicates import removeDuplicates
from zen.removeAll import removeAll
from zen.deferExec import deferExec
from zen.sortBy import sortBy
from zen.midPoint import midPoint
from zen.normalize import normalize
from zen.disconnectNodes import disconnectNodes
from zen.firstOpenPlug import firstOpenPlug
from zen.distanceBetween import distanceBetween
from zen.hierarchyBetween import hierarchyBetween
from zen.getBindPose import getBindPoses
from zen.iterable import iterable
from zen.uniqueNames import uniqueNames
from zen.listNodeConnections import listNodeConnections
from zen.getIDs import getIDs
from zen.constraints import ParentSpace
from zen.controls.arcCtrl import ArcCtrl
from zen.controls.handle import Handle
from zen.constraints.rivet import Rivet
# ?!!
try:
	from zen.constraints.rivet import Rivet
except:
	from zen.constraints.rivet import *
	if not mc.about(batch=True): deferExec('reload(zen)')

class ArcIK(list):

	def __init__(self,*args,**keywords):

		#check to make sure unique names are used in scene
		uniqueNames(iterable(mc.ls(type='dagNode')),re=True)

		# default options
		self.radius=1
		self.arcWeight=.75
		self.handles=['ArcIKCtrl#']
		self.parent=['|']
		self.handleType=['doubleEllipse']
		self.handleOptions=[{}]
		self.softParent=['']
		self.name=''
		self.squash=20
		self.stretch=20
		self.width=1
		self.allowScale=False # not functional
		self.minWidth=0
		self.maxWidth=5
		self.spread=False #requires ribs
		self.curl=False #requires ribs
		self.wrap=False

		self.shortNames=\
		{
			'n':'name',
			'ht':'handleType',
			'ho':'handleOptions',
			'sp':'softParent',
			'p':'parent',
			'spr':'spread',
			'c':'curl'
		}

		# attributes
		self.handleShape=['']
		self.parentSpace=['']

		for k in keywords:
			if k in self.__dict__:
				exec('self.'+k+'=keywords[k]')
			elif k in self.shortNames:
				exec('self.'+self.shortNames[k]+'=keywords[k]')

		self.handles=iterable(self.handles)
		self.parent=iterable(self.parent)
		self.handleType=iterable(self.handleType)
		self.softParent=iterable(self.softParent)
		self.name=iterable(self.name)
		if isinstance(self.handleOptions,dict):
			self.handleOptions=[self.handleOptions]

		# parse arguments
		if len(args)==0: args=mc.ls(sl=True,fl=True)

		sel=[]
		for a in args:
			sel.extend(iterable(a))

		self.jointHierarchy=hierarchyBetween([sel[0],sel[-1]],type='joint')

		if ('radius' not in keywords) and ('r' not in keywords):
			hDist=distanceBetween(self.jointHierarchy[0],self.jointHierarchy[-1])
			self.radius=hDist/3

		self.ArcCtrl=ArcCtrl\
		(
			self.jointHierarchy,
			p=[self.jointHierarchy[0],'.'],
			stretch=self.stretch,
			squash=self.squash,
			arcWeight=self.arcWeight,
			createSurface=True,
			scaleLength=True
		)

		self.constrainJoints()
		self.mkControlObjects()

		self[:]=self.handles

	def constrainJoints(self): # Rivet & constrain joints to the ArcCtrl surface

		rivetArgs=[]
		cjLen=1
		for j in self.jointHierarchy[1:]:
			if self.spread:
				cj=removeAll\
				(
					self.jointHierarchy[1:],
					iterable(mc.listRelatives(j,c=True,type='transform'))
				)
				rivetArgs.extend(cj)
				cjLen=len(cj)+1

			rivetArgs.append(j)

		skipRotate=[]
		for sr in range(1,cjLen+1):
			skipRotate.append(-sr)

		rivetArgs.append(self.ArcCtrl.outputSurface)

		self.rivet=Rivet(rivetArgs,constraint=True,skipRotate=skipRotate)

		if not\
		(
			mc.connectionInfo(self.jointHierarchy[-1]+'.r',id=True) or
			mc.connectionInfo(self.jointHierarchy[-1]+'.rx',id=True) or
			mc.connectionInfo(self.jointHierarchy[-1]+'.ry',id=True) or
			mc.connectionInfo(self.jointHierarchy[-1]+'.rz',id=True)
		):
			mc.parentConstraint(self.ArcCtrl.handles[-1],self.jointHierarchy[-1],st=('x','y','z'),mo=True)
			if self.spread or self.curl:
				for j in cj:
					mc.parentConstraint(self.ArcCtrl.handles[-1],j,st=('x','y','z'),mo=True)

	def mkControlObjects(self):

		if not mc.objExists(self.handles[-1]):

			self.handles[-1]=mc.createNode('transform',n=uniqueNames(self.name[-1]))
			mc.xform(self.handles[-1],ws=True,a=True,m=mc.xform(self.ArcCtrl.handles[-1],q=True,ws=True,m=True))
			mc.xform(self.handles[-1],ws=True,a=True,piv=mc.xform(self.ArcCtrl.handles[-1],q=True,a=True,ws=True,piv=True)[:3])
			if 'type' not in self.handleOptions[-1]:
				self.handleOptions[-1]['type']=self.handleType[-1]
			if 'radius' not in self.handleOptions[-1]:
				self.handleOptions[-1]['radius']=self.radius
			self.handleShape[-1]=Handle(self.handles[-1],**self.handleOptions[-1])

		if mc.objExists(self.parent[-1]):
			mc.parent(self.handles[-1],self.parent[-1])

		if mc.objExists(self.softParent[-1]):
			self.parentSpace[-1]=ParentSpace(self.handles[-1],self.softParent[-1])
			for bp in getBindPoses(self.jointHierarchy): mc.dagPose(self.parentSpace[-1],a=True,n=bp)

		mc.makeIdentity(self.handles[-1],apply=True,t=True)#,r=True)

		mc.addAttr(self.handles[-1],ln='stretch',at='float',min=0,k=1,dv=self.stretch)
		mc.addAttr(self.handles[-1],ln='squash',at='float',min=0,max=1,k=1,dv=self.squash)
		mc.addAttr(self.handles[-1],ln='arcWeight',at='float',min=0,max=1,k=1,dv=self.arcWeight)
		mc.addAttr(self.handles[-1],ln='width',at='float',min=0.0001,k=1,dv=self.width)
		mc.connectAttr(self.handles[-1]+'.stretch',self.ArcCtrl.handles[-1]+'.stretch',f=True)
		mc.connectAttr(self.handles[-1]+'.squash',self.ArcCtrl.handles[-1]+'.squash',f=True)
		mc.connectAttr(self.handles[-1]+'.arcWeight',self.ArcCtrl.handles[-1]+'.arcWeight',f=True)
		mc.connectAttr(self.handles[-1]+'.width',self.ArcCtrl.handles[0]+'.width',f=True)

		if self.curl:
			mc.addAttr(self.handles[-1],ln='curl',at='doubleAngle',k=1,dv=0)

			for r in removeAll(self.jointHierarchy,self.rivet):

				axis='x'
				longestAxisLen=0

				for a in ['x','y','z']:

					axisLen=abs(mc.getAttr(r+'.t'+a))

					if axisLen>longestAxisLen:
						longestAxisLen=axisLen
						axis=a

				behaviorMirrored=False

				try:
					parentJoint=mc.listRelatives(r,p=True)[0]

					oppositeJoint=removeAll(r,mc.listRelatives(parentJoint,c=True,type='joint'))[0]
					for a in ['x','y','z']:

						if\
						(
							abs(180-abs(abs(mc.getAttr(r+'.jo'+a))-abs(mc.getAttr(oppositeJoint+'.jo'+a))))<5
						):
							behaviorMirrored=True
							break
				except:
					pass

				pcr=mc.listConnections(r+'.rx',type='parentConstraint')[0]

				pcTargets=mc.parentConstraint(pcr,q=True,tl=True)
				pcIDs=[]
				nsc=listNodeConnections(pcr,s=False,d=True)

				for n in range(0,len(nsc)):
					if len(nsc[n])==2 and mc.objExists(nsc[n][-1]):
						pcID=getIDs(nsc[n][-1])
						if isinstance(pcID,int):
							pcIDs.append(pcID)

				pcIDs=removeDuplicates(pcIDs)
				pcIDs.sort()
				pcID=pcIDs[-1]

				pma=mc.createNode('plusMinusAverage')

				if mc.getAttr(r+'.uPos')>50:
					mc.setAttr(pma+'.op',2)
					if\
					(
						(behaviorMirrored and parentJoint!=self.jointHierarchy[-1])
					):
						mc.setAttr(pma+'.op',1)
				if mc.getAttr(r+'.uPos')<50:
					mc.setAttr(pma+'.op',1)
					if\
					(
						behaviorMirrored
					):
						mc.setAttr(pma+'.op',2)

				mc.setAttr(pma+'.i1[0]',mc.getAttr(pcr+'.tg['+str(pcID)+'].tor'+axis))
				mc.setAttr(pcr+'.tg['+str(pcID)+'].tor'+axis,lock=False)
				mc.connectAttr(self.handles[-1]+'.curl',pma+'.i1[1]')
				mc.connectAttr(pma+'.o1',pcr+'.tg['+str(pcID)+'].tor'+axis)





		mc.parentConstraint(self.handles[-1],self.ArcCtrl.handles[-1],mo=True)
		mc.scaleConstraint(self.handles[-1],self.ArcCtrl.handles[-1],sk=('x','y'),mo=True)

		for bp in getBindPoses(self.jointHierarchy): mc.dagPose(self.handles[-1],a=True,n=bp)

		mc.setAttr(self.handles[-1]+'.sy',k=False,lock=True)
		mc.setAttr(self.handles[-1]+'.sx',k=False,lock=True)
		if not self.spread:
			mc.setAttr(self.handles[-1]+'.sz',k=False,lock=True)


		mc.setAttr(self.handles[-1]+'.v',k=False,cb=True)

		for bp in getBindPoses(self.jointHierarchy): mc.dagPose(self.handles[-1],a=True,n=bp)
