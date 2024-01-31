import maya.cmds as mc
import maya.mel as mel
import maya.utils as mu
from zen.isIterable import isIterable
from zen.removeDuplicates import removeDuplicates
from zen.removeDuplicates import removeDuplicates
from zen.removeAll import removeAll
from zen.listNodeConnections import listNodeConnections
from zen.getIDs import getIDs
from zen.shape import shape
from zen.firstOpenPlug import firstOpenPlug
from zen.iterable import iterable
from zen.duplicateShape import duplicateShape

class BlendShape(list):

	"""Aims to facilitate and simplify scripting blendShapes and blendShape in-betweens with fewer lines of code.
The last argument should be either the base shape or a blendShape node to which you wish to append the input targets.
Targets may be passed in either as string arguments if there are no in-betweens, as list arguments in order of progression,
as keywords wherein the key is the name of the desired control attribute name."""

	def __init__(self,*args,**keywords):

		#default options
		self.targets=[]
		self.origin='local'
		self.frontOfChain=True
		self.deleteTargets=False
		self.base=[]
		self.baseIndex=0
		self.useExisting=True
		self.controlObjects=[]
		self.controlAttributes=[]
		self.before=False
		self.after=False
		self.name='blendShape#'
		self.goals=[] # use to specify exact goal weights for each target in each target list
		self.range=[[0,10]] # use to specify range of goals for each target
		self.weights=[0]
		self.prune=False
		self.baseIndex=0
		self.createControlObject=False
		self.control=True

		# any of the following abbreviations can be substituted
		self.shortNames=\
		{
			'o':'origin',
			'foc':'frontOfChain',
			'dt':'deleteTargets',
			'b':'base',
			'ue':'useExisting',
			'co':'controlObjects',
			'control':'controlObjects',
			'ca':'controlAttributes',
			'n':'name',
			'g':'goals',
			'goal':'goals',
			'gm':'goalMax',
			'p':'prune',
			'r':'range',
			't':'targets',
			'w':'weights',
			'c':'control'
		}

		unusedKeys={}
		for k in keywords:
			if k in self.shortNames:
				exec('self.'+self.shortNames[k]+'=keywords[k]')
			elif k in self.__dict__:
				exec('self.'+k+'=keywords[k]')
			else:
				unusedKeys[k]=keywords[k]

		self.controlObjects=iterable(self.controlObjects)

		if not isIterable(self.range[0]): self.range=[self.range]

		if len(args)==0: args=mc.ls(sl=True)

		sel=[]
		for a in args:
			if isinstance(a,str) and mc.objExists(a) and mc.nodeType(a)=='blendShape':
				self.append(a)
				self.base=mc.blendShape(a,q=True,g=True)
				for i in range(0,len(self.base)): self.base[i]=shape(self.base[i])
				break
			else:
				sel.append(a)

		if len(self.base)>self.baseIndex and mc.objExists(self.base[self.baseIndex]):
			self.targets.extend(removeAll([self[0],self.base[self.baseIndex]],sel))
		else:
			self.targets.extend(sel[:-1])
			self.base=[shape(args[-1])]

		if self.useExisting and len(self[:])==0: self.find()

		if len(self)==0: self.create()

		self.addTargets(**self.__dict__)

	def find(self):

		setBlendShapes=[]
		for d in iterable(mc.listSets(o=self.base[self.baseIndex],ets=True,t=2)):
			setBlendShapes.extend(iterable(mc.listConnections(d+'.usedBy',type='blendShape')))

		histBlendShapes=iterable(mc.ls(iterable(mc.listHistory(self.base)),type='blendShape'))

		for bs in setBlendShapes:
			if bs in histBlendShapes:
				self.append(bs)
				break

	def create(self):

		blendShapeKeys={}
		for k in ['frontOfChain','before','after','name','origin']:
			if isinstance(eval('self.'+k),bool) and eval('self.'+k)==True:
				blendShapeKeys[k]=eval('self.'+k)
			if isinstance(eval('self.'+k),str) and eval('self.'+k)!='':
				blendShapeKeys[k]=eval('self.'+k)

		if len(iterable(mc.listHistory(self.base[self.baseIndex])))==0:
			duplicateShape(self.base[self.baseIndex],ah=True)

		self[:]=mc.blendShape\
		(
			self.base[self.baseIndex],
			**blendShapeKeys
		)

	def addTargets(self,*args,**keywords):

		targets=[]
		goals=[]
		goalRange=[[0,10]]
		deleteTargets=False
		base=self.base
		baseIndex=0
		controlObjects=[]
		controlAttributes=[]
		prune=self.prune
		baseIndex=0
		weights=[0]
		control=True

		shortNames=\
		{
			't':'targets',
			'g':'goals',
			'r':'goalRange',
			'range':'goalRange',
			'dt':'deleteTargets',
			'b':'base',
			'co':'controlObjects',
			'ca':'controlAttributes',
			'goal':'goals',
			'p':'prune',
			'w':'weights',
			'c':'control'
		}

		for k in keywords:
			if k in shortNames:
				exec(shortNames[k]+'=keywords[k]')
			elif k in locals() and k!='shortNames':
				exec(k+'=keywords[k]')

		targets.extend(args)
		controlObjects=iterable(controlObjects)
		controlAttributes=iterable(controlAttributes)
		weights=iterable(weights)

		targetTrs=[]
		for i in range(0,len(targets)):
			targets[i]=iterable(targets[i])
			targetTrs.append([])
			for n in range(0,len(targets[i])):
				targets[i][n]=shape(targets[i][n])
				targetTrs[-1].append(mc.listRelatives(targets[i][n],p=True)[0])

		if len(targets)==0:
			raise Exception('BlendShape.addTargets() requires target(s).')
			return

		#double-check base index in case of changes to indexing
		geometry=iterable(mc.blendShape(self[0],q=True,g=True))
		if shape(base[baseIndex]) in geometry:
			baseIndex=geometry.index(shape(base[baseIndex]))
		elif base[baseIndex] in geometry:
			baseIndex=geometry.index(base[baseIndex])
		else:
			raise Exception('Shape '+shape(base[baseIndex])+' is not used by '+self[0]+'.')
			return

		while len(goals)<len(targets):
			goals.append([])

		while len(weights)<len(targets):
			weights.append(weights[-1])

		while len(goalRange)<len(targets):
			goalRange.append(goalRange[-1])

		for i in range(0,len(targets)):

			t=iterable(targets[i])
			g=iterable(goals[i])
			r=iterable(goalRange[i])

			if len(base)>1:
				matchingBases=[]
				tvs=len(mc.ls(t[-1]+'.vtx[*]',fl=True))
				tfs=len(mc.ls(t[-1]+'.f[*]',fl=True))
				tes=len(mc.ls(t[-1]+'.e[*]',fl=True))
				for b in base:
					if\
					(
						tvs==len(mc.ls(b+'.vtx[*]',fl=True)) and
						tfs==len(mc.ls(b+'.f[*]',fl=True)) and
						tes==len(mc.ls(b+'.e[*]',fl=True))
					):
						matchingBases.append(b)

				if base[baseIndex] not in matchingBases and len(matchingBases)>0:
					baseIndex=base.index(matchingBases[-1])

			index=firstOpenPlug(self[0]+'.it['+str(baseIndex)+'].itg')

			if len(g)>0 and g[-1]<g[0]:
				g.reverse()
				t.reverse()

			if len(g)>=len(t): r=[g[0],g[-1]]

			if len(r)==1 and isinstance(r[0],(float,int)): r=[r[0],r[0]+10]
			elif len(r)>2 and isinstance(r[0],(float,int)) and isinstance(r[-1],(float,int)): r=[r[0],r[-1]]
			elif len(r)==0 or not isinstance(r[0],(float,int)) or not isinstance(r[-1],(float,int)): r=[0,10]

			if r[-1]<r[0]:
				r.reverse()
				t.reverse()

			if t[-1] not in mc.blendShape(self[0],q=True,t=True):

				n=0
				if len(g)==0: g.append(r[0]+(r[-1]-r[0])/len(t))
				while len(g)<len(t):
					g.append(g[-1]+(r[-1]-g[-1])/(len(t)-len(g)))
					n+=1

				for n in range(0,len(t)):

					mc.blendShape\
					(
						self[0],
						e=True,
						t=(base[baseIndex],index,t[n],g[n]),
						w=(index,weights[i])
					)

			goals[i]=g
			targets[i]=t
			goalRange[i]=r

		# if we don't have all the control attributes or we don't have a control object, make some up

		if len(controlObjects)==0 and len(targets)>0:
			controlObjects.append(mc.listRelatives(base[baseIndex],p=True)[0])

		if len(controlObjects)>0:
			while len(controlObjects)<len(targets):
				controlObjects.append(controlObjects[-1])
			n=0
			while len(controlAttributes)<len(targetTrs):
				controlAttributes.append(targetTrs[n][-1].replace(base[baseIndex],''))
				if controlAttributes[-1][0] in ['_','|']: controlAttributes[-1]=controlAttributes[-1][1:]
				controlAttributes[-1]=controlAttributes[-1][0].lower()+controlAttributes[-1][1:]
				n=+1
			if control:
				for i in range(0,len(targets)):
					if mc.objExists(controlObjects[i]) and controlAttributes[i] not in removeDuplicates(mc.listAttr(controlObjects[i])):
						mc.addAttr\
						(
							controlObjects[i],
							ln=controlAttributes[i],
							at='double',
							dv=weights[i],
							k=True,
							smx=goalRange[i][-1],
							smn=goalRange[i][0]
						)
					if not mc.isConnected(controlObjects[i]+'.'+controlAttributes[i],self[0]+'.'+targets[i][-1]):
						mc.connectAttr(controlObjects[i]+'.'+controlAttributes[i],self[0]+'.'+targets[i][-1],f=True)

		self.controlObjects.extend(controlObjects)
		self.targets.extend(targets)
		self.range.extend(goalRange)
		self.goals.extend(goals)
		self.base.extend(base)
		self.controlObjects.extend(controlObjects)
		self.controlAttributes.extend(controlAttributes)

def new(*args,**keywords):
	return BlendShape(*args,**keywords)