import maya.cmds as mc
import maya.mel as mel
import maya.utils as mu
from zen.controls.handle import Handle
from zen.iterable import iterable
from zen.isIterable import isIterable
from zen.hierarchyBetween import hierarchyBetween
from zen.deferExec import deferExec
from zen.hierarchyOrder import hierarchyOrder
from zen.removeAll import removeAll
from zen.getBindPoses import getBindPoses
from zen.firstOpenPlug import firstOpenPlug
from zen.distanceBetween import distanceBetween
from zen.listNodeConnections import listNodeConnections
from zen.midPoint import midPoint
from zen.disconnectNodes import disconnectNodes
from zen.uniqueNames import uniqueNames
from zen.firstOpenPlug import firstOpenPlug
from zen.normalize import normalize
from zen.freeze import freeze
from zen.uniqueNames import uniqueNames
from zen.constraints import ParentSpace
from exceptions import Warning

class IKLimb(list):

	"""Creates a 3-bone ik/fk limb with pole vector aim and ik controls as well as fk controls, ik/fk switch, and twist joints ( by default & only if present )."""
	"""Input arguments/selections should be the start and end joints, a shoulder/hip twist joint ( if used ), and any control objects to be used ( assignment detected by proximity )."""
	"""Any control objects not specified will be created automatically."""

	def __init__(self,*args,**keywords):

		# default options

		self.name='limb'
		self.stretch=20
		self.squash=0
		self.twist=True # performs auto detect
		self.sway=True
		self.switch='ik' # initial ik/fk switch state
		self.handleOptions=[{'type':'doubleEllipse','spin':-180},{'type':'doubleEllipse','spin':-90},{'type':'doubleEllipse'},{'type':'locator'}]
		self.tol=1.0 # angle tolerance for preferred angles
		self.parent=''

		self.shortNames=\
		{
			'n':'name',
			'p':'parent',
			'sp':'softParent',
			'co':'controlObjects',
			'ho':'handleOptions'
		}

		# attributes

		self.controlObjects=['','','','']
		self.bindPoses=[]
		self.joints=[]
		self.group=''
		self.orientAxis=''
		self.bendAxis=''
		self.poleAxis=''
		self.ctrlJoints=[]
		self.handles=[]
		self.endEffector=''
		self.ikHandle=''
		self.jointParent=''
		self.jointParent=''
		self.originalRotations={}
		self.bendDirection=0
		self.poleVector=[]
		self.poleVectorWorld=[]
		self.upVector=[]
		self.aimVector=[]
		self.parentSpaces=[]

		for k in keywords:

			if k in self.__dict__:
				exec('self.'+k+'=keywords[k]')
			elif k in self.shortNames:
				exec('self.'+self.shortNames[k]+'=keywords[k]')

		uniqueNames(re=True)

		if len(args)==0:
			args=mc.ls(sl=True)

		sel=[]
		for a in args:
			sel.extend(iterable(a))
		sel=hierarchyOrder(sel)

		# parse options

		defualtHandleOptions=[{'type':'doubleEllipse','spin':-180},{'type':'doubleEllipse','spin':-90},{'type':'doubleEllipse'},{'type':'locator'}]

		i=len(self.handleOptions)
		while len(self.handleOptions)<4:
			self.handleOption.append(defualtHandleOptions[i])
			i+=1

		if isinstance(self.handleOptions,dict):
			self.handleOptions=[self.handleOptions,self.handleOptions,self.handleOptions]
		elif isIterable(self.handleOptions):
			if len(self.handleOptions)==0:
				self.handleOptions.append({})
			while len(self.handleOptions)<3:
				self.handleOptions.append(self.handleOptions[-1])
		else:
			self.handleOptions=[{},{},{}]

		self.controlObjects=iterable(self.controlObjects)
		self.orientAxis=self.orientAxis.lower()

		self.baseTwist=''
		self.hierarchy=[]
		if len(sel)>2:
			for j in sel[:-1]:
				if len(hierarchyBetween(j,sel[-1]))>len(self.hierarchy):
					self.hierarchy=hierarchyBetween(j,sel[-1])
			closest=9e999
			for s in removeAll([self.hierarchy[0],self.hierarchy[-1]],sel):
				if\
				(
					len(iterable(mc.listRelatives(self.hierarchy[0],p=True)))==0 or
					s in mc.listRelatives(mc.listRelatives(self.hierarchy[0],p=True)[0],c=True,type='joint')
				):
					dist=distanceBetween(s,self.hierarchy[0])
					if dist<closest:
						closest=dist
						self.baseTwist=s
		else:
			self.hierarchy=hierarchyBetween(sel[0],sel[-1])

		self.bindPoses=iterable(getBindPoses(self.hierarchy))

		self.joints=['','','']

		if len(self.hierarchy)<3:
			raise Exception('There are no joints between your start and end joint. No IK created.')

		self.joints[0]=self.hierarchy[0]
		self.joints[-1]=self.hierarchy[-1]

		# find the orientation axis

		self.orientAxis='x'
		axisLen={'x':0,'y':0,'z':0}
		for j in self.hierarchy[1:]:
			for a in ['x','y','z']:
				axisLen[a]+=abs(mc.getAttr(j+'.t'+a))
				if axisLen[a]>axisLen[self.orientAxis]:
					self.orientAxis=a

		# find bend joint and pole vector

		self.originalRotations={}

		for j in self.hierarchy[1:-1]: # check to see if any have a non-zero preferred angle
			for a in removeAll(self.orientAxis,['x','y','z']):
				if abs(mc.getAttr(j+'.pa'+a))>=self.tol:
					self.originalRotations[j+'.r'+a]=mc.getAttr(j+'.r'+a)
					mc.setAttr(j+'.r'+a,mc.getAttr(j+'.pa'+a))
		greatestAngle=0
		for j in self.hierarchy[1:-1]:
			jPos=mc.xform(j,q=True,ws=True,rp=True)
			prevJPos=mc.xform(self.hierarchy[self.hierarchy.index(j)-1],q=True,ws=True,rp=True)
			nextJPos=mc.xform(self.hierarchy[self.hierarchy.index(j)+1],q=True,ws=True,rp=True)
			vAngle=mc.angleBetween(v1=normalize(jPos[0]-prevJPos[0],jPos[1]-prevJPos[1],jPos[2]-prevJPos[2]),v2=normalize(nextJPos[0]-jPos[0],nextJPos[1]-jPos[1],jPos[2]-jPos[2]))[-1]
			if abs(vAngle)>greatestAngle:
				greatestAngle=abs(vAngle)
				self.joints[1]=j

		mp=midPoint\
		(
			self.hierarchy[0],self.hierarchy[-1],
			bias=\
			(
				distanceBetween(self.hierarchy[0],self.joints[1])/
				(distanceBetween(self.hierarchy[0],self.joints[1])+distanceBetween(self.joints[1],self.hierarchy[-1]))
			)
		)

		bendPoint=mc.xform(self.joints[1],q=True,ws=True,rp=True)

		self.poleVectorWorld=normalize\
		(
			bendPoint[0]-mp[0],
			bendPoint[1]-mp[1],
			bendPoint[2]-mp[2]
		)

		pmm=mc.createNode('pointMatrixMult')
		mc.setAttr(pmm+'.vm',True)
		mc.connectAttr(self.joints[1]+'.worldInverseMatrix',pmm+'.im')
		mc.setAttr(pmm+'.ip',*self.poleVectorWorld)

		self.poleVector=mc.getAttr(pmm+'.o')[0]

		disconnectNodes(pmm)
		mc.delete(pmm)

		greatestLength=0.0
		for i in [0,1,2]:
			if abs(self.poleVector[i])>greatestLength and ['x','y','z'][i]!=self.orientAxis:
				self.poleAxis=['x','y','z'][i]
				greatestLength=abs(self.poleVector[i])
				self.bendDirection=-abs(self.poleVector[i])/self.poleVector[i]

		for r in self.originalRotations:
			mc.setAttr(r,self.originalRotations[r])

		preferredAngleWarning=False
		if not mc.objExists(self.joints[1]):
			preferredAngleWarning=True
			mp=midPoint(self.hierarchy[0],self.hierarchy[-1])
			cd=9e999
			dist=0
			for j in self.hierarchy[1:-1]:
				dist=distanceBetween(j,mp)
				if dist<cd:
					cd=dist
					self.joints[1]=j
					self.bendAxis=removeAll(self.orientAxis,['z','y','x'])[0]

		if self.poleAxis=='': self.poleAxis=removeAll([self.orientAxis,self.bendAxis],['x','y','z'])[0]
		if self.bendAxis=='': self.bendAxis=removeAll([self.orientAxis,self.poleAxis],['x','y','z'])[0]
		if self.orientAxis=='': self.orientAxis=removeAll([self.bendAxis,self.poleAxis],['x','y','z'])[0]

		if self.poleAxis=='x': self.poleVector=[-self.bendDirection,0.0,0.0]
		if self.poleAxis=='y': self.poleVector=[0.0,-self.bendDirection,0.0]
		if self.poleAxis=='z': self.poleVector=[0.0,0.0,-self.bendDirection]

		if self.bendAxis=='x': self.upVector=[-self.bendDirection,0.0,0.0]
		if self.bendAxis=='y': self.upVector=[0.0,-self.bendDirection,0.0]
		if self.bendAxis=='z': self.upVector=[0.0,0.0,-self.bendDirection]

		if self.orientAxis=='x': self.aimVector=[self.bendDirection,0.0,0.0]
		if self.orientAxis=='y': self.aimVector=[0.0,self.bendDirection,0.0]
		if self.orientAxis=='z': self.aimVector=[0.0,0.0,self.bendDirection]

		if mc.objExists(self.baseTwist):

			conn=False
			for a in ['.r','.rx','.ry','.rz']:
				if mc.connectionInfo(self.baseTwist+a,id=True):
					conn=True
			if not conn:
				mc.orientConstraint(self.joints[0],self.baseTwist,sk=self.orientAxis)

		# load ik2Bsolver - ikRPSolver does not work well with this setup

		mel.eval('ik2Bsolver')

		self.create()

		if preferredAngleWarning:
			raise Warning('Warning: Joints are co-linear and no preferred angles were set. Results may be unpredictable.')

	def create(self):

		mc.cycleCheck(e=False)

		if mc.objExists(self.parent):
			self.group=mc.createNode('transform',n=uniqueNames(self.name),p=self.parent)
		else:
			self.group=mc.createNode('transform',n=uniqueNames(self.name))

		self.jointParent=''
		if len(iterable(mc.listRelatives(self.joints[0],p=True)))>0:
			self.jointParent=mc.listRelatives(self.joints[0],p=True)[0]
		else:
			self.jointParent=mc.createNode('transform',n=uniqueNames(self.name+'CtrlJointGroup'))
			mc.parent(self.joints[0],self.jointParent)

		cMuscleObjects=[]

		# create control joints

		self.ctrlJoints=[]
		for j in self.joints:

			cj=mc.createNode('joint',p=j,n=uniqueNames(self.name+'CtrlJoint'))

			if len(self.ctrlJoints)==0:
				mc.parent(cj,self.group)
				if mc.objExists(self.jointParent):
					self.jointParent=mc.rename(ParentSpace(cj,self.jointParent)[0],self.name+'CtrlJoints')
				else:
					self.jointParent=mc.rename(ParentSpace(cj)[0],self.name+'CtrlJoints')
			else:
				mc.parent(cj,self.ctrlJoints[-1])

			mc.setAttr(cj+'.r',*mc.getAttr(j+'.r')[0])
			mc.setAttr(cj+'.jo',*mc.getAttr(j+'.jo')[0])
			self.originalRotations[cj+'.r']=list(mc.getAttr(cj+'.r')[0])

			mc.setAttr(j+'.r',0,0,0)
			mc.setAttr(cj+'.r',0,0,0)

			mc.setAttr(cj+'.s',1,1,1)
			mc.setAttr(cj+'.radius',mc.getAttr(j+'.radius')*1.5)#0)
			mc.setAttr(cj+'.ovc',10)
			mc.connectAttr(j+'.pa',cj+'.pa')

			if self.joints.index(j)<len(self.joints)-1:
				childList=removeAll\
				(
					iterable(mc.listRelatives(self.joints[self.joints.index(j)+1],c=True,ad=True))+[self.joints[self.joints.index(j)+1]],
					iterable(mc.listRelatives(j,c=True,ad=True))+[j]
				)

				chList=childList
				for c in chList:
					if mc.nodeType(c) not in ['transform','joint','cMuscleObject']:
						childList.remove(c)
					if mc.nodeType(c) in ['transform','joint']:
						for a in ['.t','.tx','.ty','.tz','.r','.rx','.ry','.rz']:
							if mc.connectionInfo(c+a,id=True) or mc.getAttr(c+a,l=True) or mc.getAttr(c+'.io'):
								childList.remove(c)
								break

				if j==self.joints[-2]:
					childList.append(self.joints[-1])

				for jc in childList:
					if mc.nodeType(jc)=='transform' or mc.nodeType(jc)=='joint':
						if jc in self.joints[:-1]:
							mc.parentConstraint(cj,jc,mo=True)
						else:
							mc.parentConstraint(cj,jc,sr=('x','y','z'),mo=True)
					elif 'cMuscle' in mc.nodeType(jc):
						cMuscleObjects.append(jc)

			else:
				mc.parentConstraint(cj,j,st=('x','y','z'),mo=True)

			self.ctrlJoints.append(cj)

		mc.hide(self.jointParent)
		mc.setAttr(self.ctrlJoints[1]+'.ssc',False)

		# create ik

		self.ikHandle,self.endEffector=mc.ikHandle(sol='ik2Bsolver',sj=self.ctrlJoints[0],ee=self.ctrlJoints[-1],n=uniqueNames(self.name+'Handle'))
		self.endEffector=mc.rename(self.endEffector,self.name+'Effector')
		mc.setAttr(self.ikHandle+'.snapEnable',False)
		mc.hide(self.ikHandle)
		mc.setAttr(self.ikHandle+'.ikBlend',0)

		for j in self.originalRotations:
			if isIterable(self.originalRotations[j]):
				mc.setAttr(j,*self.originalRotations[j])
			else:
				mc.setAttr(j,self.originalRotations[j])

		# look for twist joints

		if self.twist:
			skipAxis=removeAll(self.orientAxis,['x','y','z'])
			twistJoints=removeAll([self.joints[-2],self.joints[-1]],hierarchyBetween(self.joints[-2],self.joints[-1],type='joint'))
			for i in range(0,len(twistJoints)):
				tj=twistJoints[i]
				oc=mc.orientConstraint(self.ctrlJoints[-1],tj,sk=skipAxis,mo=True)
				if i>0:
					oc=mc.orientConstraint(self.ctrlJoints[-2],tj,sk=skipAxis,mo=True)
					wal=mc.orientConstraint(oc,q=True,wal=True)
					distToBend=distanceBetween(self.ctrlJoints[-2],tj)
					distToEnd=distanceBetween(self.ctrlJoints[-1],tj)
					mc.setAttr(oc+'.'+wal[-1],distToEnd/(distToBend+distToEnd))
					mc.setAttr(oc+'.'+wal[-2],distToBend/(distToBend+distToEnd))

		# make stretchy

		db=mc.createNode('distanceBetween')
		mc.connectAttr(self.ctrlJoints[0]+'.t',db+'.p1')

		pmm1=mc.createNode('pointMatrixMult')
		pmm2=mc.createNode('pointMatrixMult')

		mc.connectAttr(self.ikHandle+'.t',pmm1+'.ip')
		mc.connectAttr(self.ikHandle+'.pm[0]',pmm1+'.im')

		mc.connectAttr(pmm1+'.o',pmm2+'.ip')
		mc.connectAttr(self.ctrlJoints[0]+'.pim[0]',pmm2+'.im')

		mc.connectAttr(pmm2+'.o',db+'.p2')

		mdl=mc.createNode('multDoubleLinear')
		mc.connectAttr(db+'.d',mdl+'.i1')
		mc.setAttr(mdl+'.i2',1.0/mc.getAttr(db+'.d'))
		cn=mc.createNode('clamp')
		for i in range(0,3):
			c=['r','g','b'][i]
			a=['x','y','z'][i]
			mc.connectAttr(mdl+'.o',cn+'.ip'+c)
			mc.setAttr(cn+'.mn'+c,1)
			mc.connectAttr(mdl+'.o',cn+'.mx'+c)
			mc.connectAttr(cn+'.op'+c,self.ctrlJoints[0]+'.s'+a)

		for cmo in cMuscleObjects:
			mdlcm=mc.createNode('multDoubleLinear')
			mc.setAttr(mdlcm+'.i1',mc.getAttr(cmo+'.length'))
			mc.connectAttr(cn+'.op'+['r','g','b'][['x','y','z'].index(self.orientAxis)],mdlcm+'.i2')
			mc.connectAttr(mdlcm+'.o',cmo+'.length')


		# create control objects or set control object pivots

		poleOffset=distanceBetween(self.ctrlJoints[1],self.ctrlJoints[0])*2

		for i in range(0,len(self.controlObjects)-1):
			if mc.objExists(self.controlObjects[i]):
				mc.xform(self.controlObjects[i],ws=True,piv=mc.xform(self.ctrlJoints[-1],q=True,ws=True,rp=True))
			else:
				if 'r' not in self.handleOptions[i] and 'radius' not in self.handleOptions[i]:
					self.handleOptions[i]['r']=distanceBetween(self.ctrlJoints[-1],self.ctrlJoints[0])/4
				if 'name' not in self.handleOptions[i] and 'n' not in self.handleOptions[i]:
					self.handleOptions[i]['n']=self.joints[i]+'_ctrl'
				if 'x' not in self.handleOptions[i] and 'xform' not in self.handleOptions[i]:
					self.handleOptions[i]['xform']=self.joints[i]
				if 'aim' not in self.handleOptions[i] and 'a' not in self.handleOptions[i]:
					self.handleOptions[i]['aim']=self.aimVector
				self.handleOptions[i]['parent']=self.group
				self.handleOptions[-i]['pointTo']=self.joints[i]
				self.handleOptions[i]['aimAt']=self.joints[i]
				self.handles.append(Handle(**self.handleOptions[i]))
				self.controlObjects[i]=(self.handles[-1].transforms[-1])

		if not mc.objExists(self.controlObjects[-1]):
			if 'name' not in self.handleOptions[-1] and 'n' not in self.handleOptions[-1]:
				self.handleOptions[-1]['n']=self.joints[1]+'_aimCtrl'
			if 'x' not in self.handleOptions[-1] and 'xform' not in self.handleOptions[-1]:
				self.handleOptions[-1]['x']=self.ctrlJoints[1]
			if 'aim' not in self.handleOptions[i] and 'a' not in self.handleOptions[i]:
				self.handleOptions[i]['aim']=self.poleVector
			self.handleOptions[-1]['parent']=self.group
			self.handleOptions[-1]['pointTo']=self.joints[1]
			self.handleOptions[-1]['aimAt']=self.joints[1]
			self.handles.append(Handle(**self.handleOptions[-1]))
			self.controlObjects[-1]=(self.handles[-1].transforms[-1])
			mc.move\
			(
				poleOffset*(self.poleVector[0]),
				poleOffset*(self.poleVector[1]),
				poleOffset*(self.poleVector[2]),
				self.controlObjects[-1],
				r=True,os=True,wd=True
			)

		# add and set control attributes

		mc.setAttr(self.controlObjects[-1]+'.v',k=False)
		for attr in ['.sx','.sy','.sz']:
			mc.setAttr(self.controlObjects[-1]+attr,l=True,k=False,cb=False)
			mc.setAttr(self.ikHandle+attr,l=True,k=False,cb=False)
		for attr in ['.rx','.ry','.rz']:
			mc.setAttr(self.controlObjects[-1]+attr,k=False,cb=False)
		for attr in ['.tx','.ty','.tz']:
			mc.setAttr(self.group+attr,l=True,k=False,cb=False)
			mc.setAttr(self.controlObjects[0]+attr,l=True,k=False,cb=False)

		mc.setAttr(self.ikHandle+'.v',k=False,cb=False)

		for attr in ['.tx','.ty','.tz']:
			mc.setAttr(self.controlObjects[1]+attr,l=True,k=False,cb=False)

		if not mc.objExists(self.controlObjects[-2]+'.twist'):
			mc.addAttr(self.controlObjects[-2],at='doubleAngle',ln='twist',k=True)
		if not mc.objExists(self.controlObjects[-2]+'.sway') and self.sway:
			mc.addAttr(self.controlObjects[-2],at='doubleAngle',ln='sway',k=1)
		if not mc.objExists(self.controlObjects[-2]+'.stretch'):
			mc.addAttr(self.controlObjects[-2],at='double',ln='stretch',k=1,dv=self.stretch,min=0)
		if not mc.objExists(self.controlObjects[-2]+'.squash'):
			mc.addAttr(self.controlObjects[-2],at='double',ln='squash',k=1,dv=self.squash,min=0,max=99)
		if not mc.objExists(self.controlObjects[-2]+'.ikSwitch'):
			mc.addAttr(self.controlObjects[-2],at='enum',ln='ikSwitch',en='ik:fk',k=True,dv=1)# if self.switch=='fk' else 0

		#sway control

		if self.sway:

			adl=mc.createNode('addDoubleLinear')
			mc.connectAttr(self.ctrlJoints[1]+'.r'+self.poleAxis,adl+'.i1')
			mc.connectAttr(self.controlObjects[-2]+'.sway',adl+'.i2')
			childList=removeAll\
			(
				iterable(mc.listRelatives(self.joints[2],c=True,ad=True)),
				iterable(mc.listRelatives(self.joints[1],c=True,ad=True))
			)+[self.joints[2],self.joints[1]]
			for c in childList:
				if mc.nodeType(c)=='transform' or mc.nodeType(c)=='joint':
					pc=mc.parentConstraint(c,q=True)
					nc=listNodeConnections(self.ctrlJoints[1],pc,s=True,d=True)
					for conn in nc:
						if conn[0]==self.ctrlJoints[1]+'.rotate':
							mc.disconnectAttr(conn[0],conn[1])
							for a in removeAll(self.poleAxis,['x','y','z']):
								mc.connectAttr(conn[0]+a.upper(),conn[1]+a.upper(),f=True)
							mc.connectAttr(adl+'.o',conn[1]+self.poleAxis.upper(),f=True)

		# ik/fk switch

		for i in range(0,3):

			c=['r','g','b'][i]
			a=['x','y','z'][i]
			adl=mc.createNode('addDoubleLinear')
			mdl1=mc.createNode('multDoubleLinear')
			mc.setAttr(mdl1+'.i2',.01)
			mdl2=mc.createNode('multDoubleLinear')
			mc.setAttr(mdl2+'.i2',.01)
			revNode=mc.createNode('reverse')
			mc.setAttr(adl+'.i1',1)

			mc.connectAttr(	mdl1+'.o',adl+'.i2')
			mc.connectAttr(self.controlObjects[-2]+'.stretch',mdl1+'.i1')

			mc.connectAttr(	mdl2+'.o',revNode+'.ix')
			mc.connectAttr(self.controlObjects[-2]+'.squash',mdl2+'.i1')

			mc.connectAttr(adl+'.o',cn+'.mx'+c,f=True)
			mc.connectAttr(revNode+'.ox',cn+'.mn'+c,f=True)

		if not mc.objExists(self.controlObjects[-2]+'.zenPreviousIKState'):
			if self.switch=='fk':
				mc.addAttr(self.controlObjects[-2],at='long',ln='zenPreviousIKState',k=0,dv=1)
			else:
				mc.addAttr(self.controlObjects[-2],at='long',ln='zenPreviousIKState',k=0,dv=0)
		if not mc.objExists(self.controlObjects[-2]+'.zenPreviousIKParent'):
			if self.switch=='fk':
				mc.addAttr(self.controlObjects[-2],at='long',ln='zenPreviousIKParent',k=0,dv=1)
			else:
				mc.addAttr(self.controlObjects[-2],at='long',ln='zenPreviousIKParent',k=0,dv=0)

		for i in range(0,2):
			for c in mc.listRelatives(self.controlObjects[i],s=True):
				mc.connectAttr(self.controlObjects[-2]+'.ikSwitch',c+'.v')

		mc.connectAttr(self.controlObjects[-2]+'.twist',self.ikHandle+'.twist')

		rev=mc.createNode('reverse')
		mc.connectAttr(self.controlObjects[-2]+'.ikSwitch',rev+'.ix')
		mc.connectAttr(rev+'.ox',self.ikHandle+'.ikBlend')

		for c in mc.listRelatives(self.controlObjects[-1],s=True):
			mc.connectAttr(rev+'.ox',c+'.v')

		# parent spaces

		for i in [0,1,2]:
			if(mc.objExists(self.jointParent)and i in [0,2]):
				ParentSpace(self.controlObjects[i],self.jointParent)
			else:
				ParentSpace(self.controlObjects[i],self.controlObjects[i-1])

		ParentSpace(self.controlObjects[-1],self.controlObjects[-2])
		if mc.objExists(self.jointParent):
			ParentSpace(self.controlObjects[-1],self.jointParent).setParent(self.jointParent)
			ParentSpace(self.controlObjects[-2],self.jointParent).setParent(self.jointParent)
		else:
			ParentSpace(self.controlObjects[-1],self.controlObjects[0])

		if self.switch=='fk':
			ParentSpace(self.controlObjects[2],self.controlObjects[1])

		for co in self.controlObjects[2:]:
			freeze(co,t=True)

		mc.aimConstraint\
		(
			self.ctrlJoints[1],self.controlObjects[-1],
			aim=(self.aimVector[0],self.aimVector[1],self.aimVector[2]),
			wuo=self.ctrlJoints[1],
			wut='objectrotation',
			mo=True
		)

		if mc.objExists(self.jointParent):
			mc.setAttr(self.controlObjects[0]+'.parentTo',l=True,k=False,cb=False)
		mc.setAttr(self.controlObjects[1]+'.parentTo',l=True,k=False,cb=False)

		#constraints

		orientConstraints=['','','']
		for i in [2,1,0]:
			orientConstraints[i]=mc.orientConstraint(self.controlObjects[i],self.ctrlJoints[i],mo=True)[0]
			mc.setAttr(self.controlObjects[i]+'.v',k=False)
			for attr in ['.sx','.sy','.sz']:
				mc.setAttr(self.controlObjects[i]+attr,l=True,k=False,cb=False)
			if i==1:
				if not self.sway:
					mc.setAttr(self.controlObjects[i]+'.r'+self.poleAxis,l=True,k=False,cb=False)
				mc.setAttr(self.controlObjects[i]+'.r'+self.orientAxis,l=True,k=False,cb=False)

		self.poleVectorConstraint=mc.poleVectorConstraint(self.controlObjects[-1],self.ikHandle)[0]

		for oc in orientConstraints[:-1]:
			octl=mc.orientConstraint(oc,q=True,tl=True)
			ocwal=mc.orientConstraint(oc,q=True,wal=True)
			weightAlias=ocwal[octl.index(self.controlObjects[orientConstraints.index(oc)])]
			mc.connectAttr(self.controlObjects[-2]+'.ikSwitch',oc+'.'+weightAlias)

		mc.parent(self.ikHandle,self.controlObjects[2],r=False)

		if self.switch=='ik':
			mc.setAttr(self.controlObjects[-2]+'.ikSwitch',0)

		# link for asset detection

		if 'zenIkFkLimbCtrls' not in mc.listAttr(self.group):
			mc.addAttr(self.group,ln='zenIkFkLimbCtrls',at='message',m=True)
		if 'zenIkFkLimbCtrlJoints' not in mc.listAttr(self.group):
			mc.addAttr(self.group,ln='zenIkFkLimbCtrlJoints',at='message',m=True)
		for co in self.controlObjects:
			if 'zenCtrl' not in mc.listAttr(co):
				mc.addAttr(co,ln='zenCtrl',at='message')
			mc.connectAttr(co+'.zenCtrl',self.group+'.zenIkFkLimbCtrls['+str(firstOpenPlug(self.group+'.zenIkFkLimbCtrls'))+']')
		for cj in self.ctrlJoints:
			if 'zenCtrl' not in mc.listAttr(cj):
				mc.addAttr(cj,ln='zenCtrl',at='message')
			mc.connectAttr(cj+'.zenCtrl',self.group+'.zenIkFkLimbCtrlJoints['+str(firstOpenPlug(self.group+'.zenIkFkLimbCtrlJoints'))+']')

		for bp in self.bindPoses:
			for co in self.controlObjects:
				mc.dagPose(co,a=True,n=bp)

		self[:]=[self.group]+self.controlObjects

		mc.cycleCheck(e=True)

		mc.select(self[-2])
