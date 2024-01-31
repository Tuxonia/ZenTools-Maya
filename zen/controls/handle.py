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
from zen.freeze import freeze
from zen.constraints.rivet import Rivet
from zen.constraints.parentSpace import ParentSpace

class Handle(list):

	def __init__(self,*args,**keywords):

		#defaults
		self.parent=''
		self.transforms=[]
		self.name=''
		self.pointTo=''
		self.aimAt=''
		self.aim=[0,1,0]
		self.up=[0,0,1]
		self.pivot=[]
		self.type='locator'
		self.shape=''
		self.shapes=[]
		self.radius=1
		self.sweep=90
		self.position=[0,0,0]
		self.scale=[1,1,1]
		self.xform=''
		self.spin=0
		self.xformMatrix=[]
		self.freeze=False
		self.softParent=''

		# attributes

		self.parentSpaces=[]


		self.shortNames=\
		{
			'p':'parent',
			'f':'freeze',
			'n':'name',
			'tan':'tangent',
			'pv':'pivot',
			'piv':'pivot',
			'tr':'transform',
			'pct':'parentCtrl',
			'pctrl':'parentCtrl',
			'ctrl':'control',
			'rad':'radius',
			'r':'radius',
			'sw':'sweep',
			'pos':'position',
			't':'type',
			'x':'xform',
			'aa':'aimAt',
			'sp':'softParent'
		}

		self.attributeTypes=\
		{
			'normal':'float3',
			'up':'double3',
			'aim':'double3',
			'sweep':'double',
			'spin':'double'
		}

		self.attributeLimits=\
		{
			'normal':[[-1,-1,-1],[1,1,1]],
			'up':[[-1,-1,-1],[1,1,1]],
			'aim':[[-1,-1,-1],[1,1,1]],
			'sweep':[0,180],
			'spin':[-225,135],
			'radius':[0,10000000]
		}

		self.attributeShortNames=\
		{
			'position':'pos',
			'radius':'rad',
			'spin':'sp',
			'sweep':'sw',
			'normal':'nr'
		}

		for k in keywords:
			if k in self.shortNames:
				exec('self.'+self.shortNames[k]+'=keywords[k]')
			elif k in self.__dict__:
				exec('self.'+k+'=keywords[k]')

		if len(args)==0 and not mc.objExists(self.xform): args=mc.ls(sl=True)

		sel=[]

		for a in args:
			if isIterable(a):
				sel.extend(a)
			else:
				sel.append(a)

		for s in sel:
			if mc.ls(s)==mc.ls(s,type='transform'):
				self.transforms.append(mc.ls(s)[0])
			elif mc.ls(s)==mc.ls(s,type='shape'):
				self.transforms.append(mc.ls(s)[0])

		# parse options

		if self.name=='': self.name='Handle#'

		if not isIterable(self.position):
			if isinstance(self.position,str) and mc.objExists(self.position):
				if len(iterable(self.position.split('.')))>1:
					try:
						self.position=mc.pointPosition(self.position)
					except:
						self.position=mc.pointPosition(self.position+'.rp')
				else:
					self.position=mc.pointPosition(self.position+'.rp')
		elif len(self.position)<3:
			self.position=[0.0,0.0,0.0]

		if self.transforms==[]:
			if 'freeze' not in keywords and 'f' not in keywords:
				self.freeze=True
			if mc.objExists(self.xform):
				self.transforms.append(mc.createNode('transform',n=self.name,p=self.xform))
				mc.setAttr(self.transforms[-1]+'.r',0,0,0)
			else:
				self.transforms.append(mc.createNode('transform',n=self.name))

			if mc.objExists(self.parent):
				mc.parent(self.transforms[-1],self.parent)
			else:
				mc.parent(self.transforms[-1],w=True)

			"""if mc.objExists(self.xform):

				xfm=mc.xform(self.xform,q=True,ws=True,a=True,m=True)
				wsro=mc.xform(self.xform,q=True,ws=True,ro=True)
				wst=mc.xform(self.xform,q=True,ws=True,t=True)
				wsrp=mc.xform(self.xform,q=True,ws=True,rp=True)
				wsra=mc.xform(self.xform,q=True,ws=True,ra=True)
				wssp=mc.xform(self.xform,q=True,ws=True,sp=True)
				print self.transforms[-1]
				print xfm
				mc.xform(self.transforms[-1],ws=True,a=True,m=xfm)
				mc.xform(self.transforms[-1],ws=True,ro=wsro)
				mc.xform(self.transforms[-1],ws=True,t=wst)
				mc.xform(self.transforms[-1],ws=True,rp=wsrp)
				mc.xform(self.transforms[-1],ws=True,ra=wsra)
				mc.xform(self.transforms[-1],ws=True,sp=wssp)

				print mc.xform(self.transforms[-1],q=True,a=True,ws=True,m=True)"""

		elif mc.objExists(self.parent):
			for t in self.transforms:
				mc.parent(t,self.parent)

		if mc.objExists(self.softParent):
			for t in self.transforms:
				self.parentSpaces.append(ParentSpace(t,self.softParent))

		if self.freeze:
			freeze(self.transforms[-1],t=True)

		if mc.objExists(self.pointTo):
			self.aimCurve=mc.createNode('nurbsCurve',p=self.transforms[0])

		if len(self.shapes)==0:
			exec('self.mk'+self.type[0].upper()+self.type[1:]+'()')

		if mc.objExists(self.pointTo):
			self.mkAim()

		for t in self.transforms:
			if not 'zenHandleShape' in mc.listAttr(t):
				mc.addAttr(t,ln='zenHandleShape',m=True,at='message')

		for s in self.shapes:
			if not 'zenHandle' in mc.listAttr(s):
				mc.addAttr(s,ln='zenHandle',at='message')

		for t in self.transforms:
			for s in self.shapes:
				mc.connectAttr\
				(
					s+'.zenHandle',
					t+'.zenHandleShape['+str(firstOpenPlug(t+'.zenHandleShape'))+']'
				)

		if len(self.transforms)>1:
			for t in self.transforms[1:]:
				pass

		self[:]=self.shapes

	def mkAim(self):

		nurbSq=mc.createNode('makeNurbsSquare')
		mc.setAttr(nurbSq+'.sl1',.001)
		mc.setAttr(nurbSq+'.sl2',.001)
		mc.setAttr(nurbSq+'.d',1)
		extend=mc.createNode('extendCurve')
		mc.setAttr(extend+'.em',2)
		mm=mc.createNode('multMatrix')
		mc.connectAttr(nurbSq+'.oc1',extend+'.ic1')
		mc.connectAttr(self.pointTo+'.wm[0]',mm+'.i[0]')
		mc.connectAttr(self.transforms[0]+'.wim[0]',mm+'.i[1]')

		pmm=mc.createNode('pointMatrixMult')
		mc.connectAttr(mm+'.o',pmm+'.im')
		mc.connectAttr(self.pointTo+'.rp',pmm+'.ip')
		mc.connectAttr(pmm+'.o',extend+'.ip')

		mc.connectAttr(extend+'.oc',self.aimCurve+'.create',lock=True)

		pma=mc.createNode('plusMinusAverage')
		mc.connectAttr(self.transforms[0]+'.rp',pma+'.i3[0]')
		mc.connectAttr(self.shapes[-1]+'.position',pma+'.i3[1]')
		mc.connectAttr(pma+'.o3',nurbSq+'.center')

		poci=mc.createNode('pointOnCurveInfo')
		mc.connectAttr(extend+'.oc',poci+'.ic')
		mc.setAttr(poci+'.top',True)
		mc.setAttr(poci+'.pr',.5)

		mc.setAttr(self.shapes[-1]+'.position',*self.position)

	def mkLocator(self):

		self.shapes.append(mc.createNode('locator',p=self.transforms[0],n=self.transforms[0]+'Shape#'))

		mc.setAttr(self.shapes[-1]+'.localPositionX',cb=False,k=False)
		mc.setAttr(self.shapes[-1]+'.localPositionY',cb=False,k=False)
		mc.setAttr(self.shapes[-1]+'.localPositionZ',cb=False,k=False)
		mc.setAttr(self.shapes[-1]+'.localScaleX',cb=False,k=False)
		mc.setAttr(self.shapes[-1]+'.localScaleY',cb=False,k=False)
		mc.setAttr(self.shapes[-1]+'.localScaleZ',cb=False,k=False)

		pma=mc.createNode('plusMinusAverage')
		mc.connectAttr(self.transforms[-1]+'.rp',pma+'.i3[0]')
		mc.connectAttr(pma+'.o3',self.shapes[-1]+'.localPosition')

		self.addAttributes\
		(
			position=pma+'.i3[1]',
			scale=self.shapes[-1]+'.localScale'
		)

	def mkDoubleEllipse(self):

		self.mkEllipse(num=2)

	def mkEllipse(self,num=1):

		h=self.transforms[0]

		spans=10.0
		circNav=2.0

		offNum=.75
		offsets=[offNum*spans,(circNav-offNum)*spans]

		mnc=mc.createNode('makeNurbCircle')
		mc.setAttr(mnc+'.sweep',360*circNav)
		mc.setAttr(mnc+'.sections',spans)

		dc=mc.createNode('detachCurve')
		mc.connectAttr(mnc+'.oc',dc+'.ic')

		negHalfSweepMDL=mc.createNode('multDoubleLinear')
		mc.setAttr(negHalfSweepMDL+'.i2',-0.0013888888888888889*spans)

		posHalfSweepMDL=mc.createNode('multDoubleLinear')
		mc.setAttr(posHalfSweepMDL+'.i2',0.0013888888888888889*spans)

		negSweepMDL=mc.createNode('multDoubleLinear')
		mc.setAttr(negSweepMDL+'.i2',-0.00277777777778*spans)

		posSweepMDL=mc.createNode('multDoubleLinear')
		mc.setAttr(posSweepMDL+'.i2',0.00277777777778*spans)

		sweepAngleMDL=mc.createNode('multDoubleLinear')
		mc.setAttr(sweepAngleMDL+'.i2',0.00277777777778*spans)

		clamp=mc.createNode('clamp') # important: maya will crash if not used

		mc.connectAttr(sweepAngleMDL+'.o',clamp+'.ipr')

		minADL=mc.createNode('addDoubleLinear')
		mc.setAttr(minADL+'.i1',-offsets[0]+.00001)
		mc.connectAttr(posHalfSweepMDL+'.o',minADL+'.i2')

		maxADL=mc.createNode('addDoubleLinear')
		mc.setAttr(maxADL+'.i1',offsets[-1]-offsets[0]-.01)
		mc.connectAttr(negHalfSweepMDL+'.o',maxADL+'.i2')

		mc.connectAttr(minADL+'.o',clamp+'.minR')
		mc.connectAttr(maxADL+'.o',clamp+'.maxR')


		for i in range(0,num):

			offset=offsets[i]
			adl0=mc.createNode('addDoubleLinear')
			mc.connectAttr(negHalfSweepMDL+'.o',adl0+'.i1')
			mc.connectAttr(clamp+'.opr',adl0+'.i2')

			adl1=mc.createNode('addDoubleLinear')
			mc.connectAttr(posHalfSweepMDL+'.o',adl1+'.i1')
			mc.connectAttr(clamp+'.opr',adl1+'.i2')

			adl2=mc.createNode('addDoubleLinear')
			mc.setAttr(adl2+'.i1',offset)
			mc.connectAttr(clamp+'.opr',adl2+'.i2')
			mc.connectAttr(adl2+'.o',adl0+'.i2',f=True)
			mc.connectAttr(adl2+'.o',adl1+'.i2',f=True)

			mc.connectAttr(adl0+'.o',dc+'.parameter['+str(i*2)+']')
			mc.connectAttr(adl1+'.o',dc+'.parameter['+str(i*2+1)+']')

			pma=mc.createNode('plusMinusAverage')
			mc.connectAttr(self.transforms[0]+'.rp',pma+'.i3[0]')
			#mc.connectAttr(self.shapes[-1]+'.position',pma+'.i3[1]')
			mc.connectAttr(pma+'.o3',mnc+'.center',f=True)

			nc=mc.createNode('nurbsCurve',p=h,n=h+'Shape#')
			mc.connectAttr(dc+'.oc['+str(i*2)+']',nc+'.create',lock=True)
			self.shapes.append(nc)

		self.addAttributes\
		(
			radius=mnc+'.radius',
			sweep=[negSweepMDL+'.i1',posSweepMDL+'.i1',posHalfSweepMDL+'.i1',negHalfSweepMDL+'.i1'],
			spin=sweepAngleMDL+'.i1',
			position=pma+'.i3[1]',#mnc+'.center',
			aim=mnc+'.normal'
		)

	def addAttributes(self,**keywords):

		#organize:
		sortedKeywords=sortBy\
		(
			keywords,
			[
				'position',
				'scale',
				'sweep',
				'spin',
				'radius',
				'normal'
			]
		)

		for k in sortedKeywords:

			attrVal=eval('self.'+k)

			if isIterable(attrVal):
				attrType='double3'
			else:
				attrType='double'

			if k in self.attributeTypes:
				attrType=self.attributeTypes[k]
			else:
				self.attributeTypes[k]=attrType

			if not k in mc.listAttr(self.shapes[-1]):

				if k in self.attributeShortNames:
					mc.addAttr(self.shapes[-1],ln=k,sn=self.attributeShortNames[k],at=attrType)
				else:
					mc.addAttr(self.shapes[-1],ln=k,at=attrType)

				if isIterable(attrVal):

					subAttrType=attrType[:-1]
					if k in self.attributeShortNames:
						mc.addAttr(self.shapes[-1],ln=k+'X',sn=self.attributeShortNames[k]+'x',at=subAttrType,p=k)
						mc.addAttr(self.shapes[-1],ln=k+'Y',sn=self.attributeShortNames[k]+'y',at=subAttrType,p=k)
						mc.addAttr(self.shapes[-1],ln=k+'Z',sn=self.attributeShortNames[k]+'z',at=subAttrType,p=k)
					else:
						mc.addAttr(self.shapes[-1],ln=k+'X',at=subAttrType,p=k)
						mc.addAttr(self.shapes[-1],ln=k+'Y',at=subAttrType,p=k)
						mc.addAttr(self.shapes[-1],ln=k+'Z',at=subAttrType,p=k)

					mc.setAttr(self.shapes[-1]+'.'+k+'X',k=False,cb=True)
					mc.setAttr(self.shapes[-1]+'.'+k+'Y',k=False,cb=True)
					mc.setAttr(self.shapes[-1]+'.'+k+'Z',k=False,cb=True)

					if k in self.attributeLimits:
						mc.addAttr(self.shapes[-1]+'.'+k+'X',e=True,min=self.attributeLimits[k][0][0],max=self.attributeLimits[k][-1][0])
						mc.addAttr(self.shapes[-1]+'.'+k+'Y',e=True,min=self.attributeLimits[k][0][1],max=self.attributeLimits[k][-1][1])
						mc.addAttr(self.shapes[-1]+'.'+k+'Z',e=True,min=self.attributeLimits[k][0][2],max=self.attributeLimits[k][-1][2])
				else:
					if k in self.attributeLimits:
						mc.addAttr(self.shapes[-1]+'.'+k,e=True,min=self.attributeLimits[k][0],max=self.attributeLimits[k][-1])

			if isIterable(attrVal):
				mc.setAttr(self.shapes[-1]+'.'+k,*attrVal,**{'cb':True,'k':False})
			else:
				mc.setAttr(self.shapes[-1]+'.'+k,attrVal,k=False,cb=True)

			if isIterable(keywords[k]):
				connectTo=keywords[k]
			else:
				connectTo=[keywords[k]]

			for c in connectTo:
				if isinstance(connectTo,dict):
					for cc in connectTo:
						if not mc.isConnected(self.shapes[-1]+'.'+k+cc,connectTo[cc]):
							mc.connectAttr(self.shapes[-1]+'.'+k+cc,connectTo[cc],f=True)
				else:
					if not mc.isConnected(self.shapes[-1]+'.'+k,c):
						mc.connectAttr(self.shapes[-1]+'.'+k,c,f=True)
