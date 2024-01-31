import maya.cmds as mc
import maya.mel as mel
from platform import python_version
from  zen.isIterable import isIterable
from zen.removeDuplicates import removeDuplicates
from zen.disconnectNodes import disconnectNodes
from zen.removeAll import removeAll
from zen.deferExec import deferExec
from zen.iterable import iterable
import re

class ParentSpace(list):

	def __init__(self,*args,**keywords):

		# default options
		self.world=''
		self.parents=[]
		name=''
		self.scale=True
		self.enumNames=[]

		self.enumNames=\
		{
			's':'scale',
			'w':'world',
			'p':'parents',
			'n':'name',
			'ps':'ParentSpace',
			'en':'enumNames'
		}

		# attributes
		self[:]=[]
		self.child=''
		self.currentParent=''
		self.parentConstraint=''
		self.scaleConstraint=''

		for k in keywords:
			if k in self.__dict__:
				exec('self.'+k+'=keywords[k]')
			elif k in self.enumNames:
				exec('self.'+enumNames[k]+'=keywords[k]')

		self.enumNames=iterable(self.enumNames)

		sel=[]
		if len(args)==0:
			sel=mc.ls(sl=True)

		for a in args:
			if isIterable(a):
				for aa in a:
					if mc.objExists(a): sel.append(mc.ls(a))[0]
			elif mc.objExists(a):
				sel.append(mc.ls(a)[0])

		if (len(sel)>0 or self.child!='') and len(self)==0:

			if self.child=='':
				self.child=sel[0]

			if mc.objExists(self.child+'.zenParentSpace') and mc.connectionInfo(self.child+'.zenParentSpace',id=True):
				self.append(mc.listConnections(sel[0]+'.zenParentSpace',s=True,d=False)[0])
			else:
				self.create(n=name)

			if len(sel)>1:
				self.addParents(en=self.enumNames,*sel[1:])
				self.setParent(sel[-1])

	def create(self,n=''):

		if n=='': n=self.child+'_parentSpace'

		currentParent=iterable(mc.listRelatives(self.child,p=True))
		if len(currentParent)>0: currentParent=currentParent[0]
		else: currentParent=''

		ps=mc.createNode('transform',n=n,p=self.child)
		self.append(ps)

		if mc.objExists(currentParent):
			mc.parent(ps,currentParent)
		else:
			currentParent='world'
			mc.parent(ps,w=True)

		if not mc.objExists(self.child+'.zenParentSpace'):
			mc.addAttr(self.child,at='message',ln='zenParentSpace')

		if not mc.objExists(self.child+'.zenPrevParentNum'):
			mc.addAttr(self.child,at='long',ln='zenPrevParentNum',k=0,dv=0)

		mc.connectAttr(ps+'.message',self.child+'.zenParentSpace')

		if self.world=='':
			worldTr=mc.createNode('transform',n='world')
		else:
			worldTr=self.world

		self.addParents([worldTr],en=['world'])

		mc.parent(self.child,ps)

		if self.world=='':
			md=mc.createNode('multiplyDivide')
			mc.setAttr(md+'.i1',*mc.getAttr(self.parentConstraint+'.tg[0].tt')[0])
			mc.connectAttr(md+'.o',self.parentConstraint+'.tg[0].tt',f=True)

			worldMatrix=mc.createNode('fourByFourMatrix')
			wm=\
			[
				[1,0,0,0],
				[0,1,0,0],
				[0,0,1,0],
				[0,0,0,1]
			]
			for a in range(0,4):
				for b in range(0,4):
					mc.setAttr( worldMatrix+'.in'+str(a)+str(b), wm[a][b] )

			mc.connectAttr(worldMatrix+'.o',self.parentConstraint+'.tg[0].tpm',f=True)
			disconnectNodes(worldTr)
			mc.delete(worldTr)

	def addParents(self,*args,**keywords):

		enumNames=[]

		shortNames=\
		{
			'en':'enumNames'
		}

		for k in keywords:
			if k in locals():
				exec(k+'=keywords[k]')
			if k in shortNames:
				exec(shortNames[k]+'=keywords[k]')

		enumNames=iterable(enumNames)

		parents=[]
		for a in args:
			parents.extend(iterable(a))

		enumNames=parents

		baseNameRE=re.compile('(^[^0-9].*[^0-9])')

		i=len(enumNames)
		while len(enumNames)<len(parents):
			enumNames.append(baseNameRE.search(parents[i]).group())
			i+=1

		for i in range(0,len(parents)):

			p=parents[i]
			en=enumNames[i]

			if\
			(
				mc.objExists(str(mc.parentConstraint(self[0],q=True))) and
				p in iterable(mc.parentConstraint(mc.parentConstraint(self[0],q=True),q=True,tl=True))
			):
				return

			self.parentConstraint=pc=mc.parentConstraint(p,self[0],mo=False)[0]
			self.scaleConstraint=sc=mc.scaleConstraint(p,self[0],mo=False)[0]



			if not mc.objExists(self.child+'.parentTo'):
				mc.addAttr(self.child,at='enum',ln='parentTo',en=en,k=True)
			else:
				mc.addAttr(self.child+'.parentTo',e=True,enumName=mc.addAttr(self.child+'.parentTo',q=True,enumName=True)+':'+en)

			enumNum=len(removeAll('',mc.addAttr(self.child+'.parentTo',q=True,enumName=True).split(':')))-1
			if enumNum==0:
				enumNum=len(removeAll('',mc.addAttr(self.child+'.parentTo',q=True,enumName=True).split(';')))-1

			parentWeightAttr=pc+'.'+mc.parentConstraint(pc,q=True,wal=True)[-1]
			scaleWeightAttr=sc+'.'+mc.scaleConstraint(sc,q=True,wal=True)[-1]

			cond=mc.createNode('condition',n='parentSpaceCond#')

			mc.connectAttr(self.child+'.parentTo',cond+'.ft')
			mc.setAttr(cond+'.st',enumNum)
			mc.setAttr(cond+'.op',0)
			mc.setAttr(cond+'.ctr',1)
			mc.setAttr(cond+'.cfr',0)
			mc.connectAttr(cond+'.ocr',parentWeightAttr)
			mc.connectAttr(cond+'.ocr',scaleWeightAttr)

	def setParent(self,parent,**keywords):

		rel=False

		for k in keywords:
			if k=='r' or k=='relative':
				rel=keywords[k]

		wsm=mc.xform(self.child,q=True,ws=True,m=True)
		piv=mc.xform(self.child,q=True,ws=True,rp=True)

		self.parentConstraint=pc=mc.parentConstraint(self[0],q=True)
		pcTargets=mc.parentConstraint(pc,q=True,tl=True)
		pcAliasList=mc.parentConstraint(pc,q=True,wal=True)

		self.scaleConstraint=sc=mc.scaleConstraint(self[0],q=True)

		for i in range(0,len(pcTargets)):
			if mc.ls(parent)[0]==mc.ls(pcTargets[i])[0]:
				cond=mc.listConnections(pc+'.'+pcAliasList[i],s=True,d=False)[0]
				mc.setAttr(self.child+'.parentTo',mc.getAttr(cond+'.st'))
				mc.setAttr(self.child+'.zenPrevParentNum',mc.getAttr(cond+'.st'))
				break

		mc.xform(self.child,a=True,ws=True,m=wsm)
		mc.xform(self.child,ws=True,piv=piv)

