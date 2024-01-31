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
from zen.zen.constraints import ParentSpace
from zen.controls.handle import Handle

class ArcCtrl(list):

	def __init__(self,*args,**keywords):

		#check to make sure unique names are used in scene
		uniqueNames(iterable(mc.ls(type='dagNode')),re=True)

		# default options
		self.createSurface=False # use for IK's etc. - creates a surface instead of a curve
		self.scaleLength=True # use for IK's etc. - compensates for scale

		self.stretch=-1 # maximum stretch %: 0 > Infinity
		self.squash=-1 # maximum squash %: 0 > 100
		self.arcWeight=.5 # controls the balance of rotational control weight alloted to the end Handle vs the base Handle
		self.width=1 # surface width
		self.length=10 # only used if no arguments are passed

		self.parents=['',''] # create under parent or parents
		self.softParents=['','']
		self.parentSpaces=['','']
		self.names=['ArcCtrl#','arcCtrl_handle#'] #
		self.handleType=['locator','locator'] # see 'Handle' class - 'locator','doubleEllipse',
		self.handleOptions=[{},{}] # dictionaries passed on to the Handle class for options concerning placement of handles

		self.aim=(0,1,0)
		self.poleVector=(0,0,1) # if only two arc points are given, it will try to point the arc in this direction if possible


		# option abbreviations
		shortNames=\
		{
			'p':'parents',
			'cs':'createSurface',
			'pv':'poleVector',
			'st':'stretch',
			'sq':'squash',
			'cs':'createSurface',
			'n':'names',
			'ho':'handleOptions',
			'w':'width',
			'pv':'poleVector',
			'aw':'arcWeight',
			'ht':'handleType',
			'sp':'softParents'
		}

		if 'shortNames' in self.__dict__: # this is done so that we don't wipe out added short names in inheriting classes
			for sn in shortNames:
				self.shortNames[sn]=shortNames[sn]
		else:
			self.shortNames=shortNames

		for k in keywords: #get user options
			if k in self.shortNames:
				exec('self.'+self.shortNames[k]+'=keywords[k]')
			elif k in self.__dict__:
				exec('self.'+k+'=keywords[k]')

		#check and format options

		if\
		(
			len(iterable(self.aim))<3 or
			not isinstance(self.aim[0],(float,int)) or
			not isinstance(self.aim[1],(float,int)) or
			not isinstance(self.aim[2],(float,int))
		):
			self.aim=(0,1,0)
		if\
		(
			len(iterable(self.poleVector))<3 or
			not isinstance(self.poleVector[0],(float,int)) or
			not isinstance(self.poleVector[1],(float,int)) or
			not isinstance(self.poleVector[2],(float,int))
		):
			self.poleVector=(0,0,1)

		self.aim=normalize(self.aim)
		self.poleVector=normalize(self.poleVector)

		if len(iterable(self.softParents))==1:
			self.softParents=[iterable(self.softParents)[0],iterable(self.softParents)[0]]
		elif len(iterable(self.softParents))==0:
			self.softParents=['','']

		if len(iterable(self.parents))==1:
			self.parents=[iterable(self.parents)[0],iterable(self.parents)[0]]
		elif len(iterable(self.parents))==0:
			self.parents=['','.']

		if len(iterable(self.names))==1:
			self.names=[iterable(self.names)[0],iterable(self.names)[0]]
		if len(iterable(self.names))==0:
			self.names=['','']

		if len(iterable(self.handleType))==1:
			self.handleType=[iterable(self.handleType)[0],iterable(self.handleType)[0]]
		if len(iterable(self.handleType))==0:
			self.handleType=['','']

		if isinstance(self.handleOptions,dict): self.handleOptions=[self.handleOptions,self.handleOptions]
		if isinstance(self.handleOptions,(list,tuple)) and\
			len(self.handleOptions)==1 and\
			isinstance(self.handleOptions[0],dict):
				self.handleOptions=[self.handleOptions[0],self.handleOptions[0]]

		if self.stretch>=0 and self.squash<0 or self.stretch<0 and self.squash>=0:# squash & stretch come as a pair, set one to 0 if only 1 is set
			if self.stretch<0: self.stretch=0
			if self.squash<0: self.squash=0

		if not isinstance(self.poleVector,tuple): self.poleVector=tuple(self.poleVector)

		# attributes
		self.outputCurve=''
		self.outputNormal=''
		self.surface=''
		self.outputSurface=''
		self.handleShapes=[]
		self.curveShapes=[]
		self.arcPoints=[]
		self.handles=[]

		# parse arguments
		if len(args)==0: args=iterable(mc.ls(sl=True,fl=True)) # if no arguments are input, use selection
		if len(args)==0: args=[[0.0,0.0,0.0]]

		sel=[]
		for a in args:
			if isIterable(a) and not isinstance(a[0],(float,int)):
				sel.extend(a)
			else:
				sel.append(a)
		for s in sel:
			if isIterable(s) and isinstance(s[0],(float,int)) and len(s)>=3:
				self.arcPoints.append(s)
			elif isinstance(s,str) and mc.objExists(s):
				err=True
				if len(s.split('.'))>1:
					try:
						self.arcPoints.append(mc.pointPosition(s))
						err=False
					except:
						err=True
				else:
					try:
						self.arcPoints.append(mc.pointPosition(s+'.rp'))
						err=False
					except:
						err=True

		if len(self.arcPoints)<2:
			if len(self.arcPoints)==0: self.arcPoints=[[0.0,0.0,0.0]]
			self.arcPoints=\
			[
				self.arcPoints[0],
				[
					float(self.arcPoints[0][0])+float(self.aim[0])*self.length,
					float(self.arcPoints[0][1])+float(self.aim[1])*self.length,
					float(self.arcPoints[0][2])+float(self.aim[2])*self.length
				]
			]

		self.create()

	def arcCheck(self):

		if len(self.arcPoints)>4: # if more than the maximum of 4 points have been given, determine which to use
			if float(int(float(len(self.arcPoints)-1)/3.0))==float(len(self.arcPoints)-1)/3.0: #divisible by 3
				self.arcPoints=\
				[
					self.arcPoints[0],
					self.arcPoints[int((len(self.arcPoints)-1)/3.0)], # 1/3
					self.arcPoints[int((2*len(self.arcPoints)-1)/3.0)], # 2/3
					self.arcPoints[-1]
				]
			elif float(int(float(len(self.arcPoints)-1)/2.0))==float(len(self.arcPoints)-1)/2.0: #even
				self.arcPoints=\
				[
					self.arcPoints[0],
					self.arcPoints[int(float(len(self.arcPoints)-1)/2.0)], # 1/2
					self.arcPoints[int(float(len(self.arcPoints)-1)/2.0)], # 1/2
					self.arcPoints[-1]
				]
			else:
				self.arcPoints=\
				[
					self.arcPoints[0],
					self.arcPoints[int(float(len(self.arcPoints)-1)/2.0)], # 1/2-
					self.arcPoints[int(float(len(self.arcPoints)-1)/2.0)+1], # 1/2+
					self.arcPoints[-1]
				]

		# check to see that all the points are not on the same vector ( co-linear )
		vA=vB=vC=cD=[]
		realArcPoints=self.arcPoints[:]
		mp=midPoint(self.arcPoints[0],self.arcPoints[-1])

		dist=distanceBetween(self.arcPoints[0],self.arcPoints[-1])
		zp=dist/1000
		offsets=[[self.poleVector[0]*zp,self.poleVector[1]*zp,self.poleVector[2]*zp],(0,zp,0),(0,0,zp),(zp,0,0)]
		for i in range(1,10):
			for offset in offsets:
				if len(self.arcPoints)>2:
					vA=normalize(self.arcPoints[1][0]-self.arcPoints[0][0],self.arcPoints[1][1]-self.arcPoints[0][1],self.arcPoints[1][2]-self.arcPoints[0][2])
					vB=normalize(self.arcPoints[-1][0]-self.arcPoints[1][0],self.arcPoints[-1][1]-self.arcPoints[1][1],self.arcPoints[-1][2]-self.arcPoints[1][2])
					vC=normalize(self.arcPoints[-2][0]-self.arcPoints[0][0],self.arcPoints[-2][1]-self.arcPoints[0][1],self.arcPoints[-2][2]-self.arcPoints[0][2])
					vD=normalize(self.arcPoints[-1][0]-self.arcPoints[-2][0],self.arcPoints[-1][1]-self.arcPoints[-2][1],self.arcPoints[-1][2]-self.arcPoints[-2][2])
				if distanceBetween(vA,vB)<zp/4 or distanceBetween(vC,vD)<zp/4 or len(self.arcPoints)==2:
					self.arcPoints=realArcPoints[:]
					if len(self.arcPoints)==2:
						 self.arcPoints=[self.arcPoints[0],[],self.arcPoints[-1]]
					self.arcPoints[1]=(mp[0]+offset[0]*i,mp[1]+offset[1]*i,mp[2]+offset[2]*i)
				else:
					break
			if distanceBetween(vA,vB)<zp/4 or distanceBetween(vC,vD)<zp/4 or len(self.arcPoints)==2: break


	def create(self):

		# arguments and list options are reversed before and after creation to conform context with IK Handle creation
		for lo in self.__dict__:
			if isinstance(self.__dict__[lo],list):
				exec('self.'+lo+'.reverse()')

		self.arcCheck()

		trSpaces=[]
		cleanup=[]
		curveShapes=[]
		keep=[]

		loft=''

		if self.createSurface:
			xs=[0,1]
		else:
			xs=[0]

		for i in [0,1]:
			self.handles.append(mc.createNode('transform',n=self.names[i]))
			trSpaces.append(self.handles[-1])

		mc.addAttr(self.handles[1],ln='arcNormal',at='float3')
		mc.addAttr(self.handles[1],ln='arcNormalX',at='float',p='arcNormal')
		mc.addAttr(self.handles[1],ln='arcNormalY',at='float',p='arcNormal')
		mc.addAttr(self.handles[1],ln='arcNormalZ',at='float',p='arcNormal')

		blendCurveShapes=[]
		arc=[]
		bs=[]
		bn=[]
		mdlWidth=[]
		origShape=[]
		ci=[]
		spans=0
		ext=[]
		measureCurves=[]

		if len(xs)>1:

			mdlWidth.append(mc.createNode('multDoubleLinear'))
			mc.setAttr(mdlWidth[0]+'.i2',-.5)

			mdlWidth.append(mc.createNode('multDoubleLinear'))
			mc.setAttr(mdlWidth[1]+'.i2',.5)

		for x in xs:

			#align handles

			arc.append([])
			arc[x].append(mc.createNode('makeThreePointCircularArc',n='arc#'))
			arc[x].append(mc.createNode('makeThreePointCircularArc',n='arc#'))
			#mc.setAttr(arc[x][0]+'.sections',16)
			#mc.setAttr(arc[x][1]+'.sections',16)

			n=0
			for i in list(range(0,2))+[-1]:
				mc.setAttr(arc[x][0]+'.point'+str(n+1),*self.arcPoints[i])
				n+=1
			n=0
			for i in [0]+list(range(-2,0)):
				mc.setAttr(arc[x][1]+'.point'+str(n+1),*self.arcPoints[i])
				n+=1

			bn.append(mc.createNode('blendColors'))
			mc.connectAttr(arc[x][0]+'.nr',bn[x]+'.c1')
			mc.connectAttr(arc[x][1]+'.nr',bn[x]+'.c2')

			if x==0:
				mc.connectAttr(bn[x]+'.op',self.handles[1]+'.arcNormal')

			self.outputNormal=self.handles[1]+'.arcNormal'

			if x==0:

				fbfm=mc.createNode('fourByFourMatrix')
				dm=mc.createNode('decomposeMatrix')

				cpoc=['','']

				bcN=mc.createNode('blendColors')
				bcT=mc.createNode('blendColors')
				bcP=mc.createNode('blendColors')

				mc.setAttr(bn[x]+'.b',self.arcWeight)
				mc.setAttr(bcN+'.b',self.arcWeight)
				mc.setAttr(bcT+'.b',self.arcWeight)
				mc.setAttr(bcP+'.b',self.arcWeight)

				mc.connectAttr(bcN+'.opr',fbfm+'.in00')
				mc.connectAttr(bcN+'.opg',fbfm+'.in01')
				mc.connectAttr(bcN+'.opb',fbfm+'.in02')

				mc.connectAttr(bcT+'.opr',fbfm+'.in10')
				mc.connectAttr(bcT+'.opg',fbfm+'.in11')
				mc.connectAttr(bcT+'.opb',fbfm+'.in12')

				mc.connectAttr(bcP+'.opr',fbfm+'.in30')
				mc.connectAttr(bcP+'.opg',fbfm+'.in31')
				mc.connectAttr(bcP+'.opb',fbfm+'.in32')

				mc.connectAttr(bn[x]+'.opr',fbfm+'.in20')
				mc.connectAttr(bn[x]+'.opg',fbfm+'.in21')
				mc.connectAttr(bn[x]+'.opb',fbfm+'.in22')

				mc.connectAttr(fbfm+'.output',dm+'.inputMatrix')

				for i in [0,1]:

					cpoc[i]=mc.createNode('closestPointOnCurve')
					mc.connectAttr(arc[x][i]+'.oc',cpoc[i]+'.ic')

					mc.connectAttr(cpoc[i]+'.nx',bcN+'.c'+str(i+1)+'r')
					mc.connectAttr(cpoc[i]+'.ny',bcN+'.c'+str(i+1)+'g')
					mc.connectAttr(cpoc[i]+'.nz',bcN+'.c'+str(i+1)+'b')

					mc.connectAttr(cpoc[i]+'.tx',bcT+'.c'+str(i+1)+'r')
					mc.connectAttr(cpoc[i]+'.ty',bcT+'.c'+str(i+1)+'g')
					mc.connectAttr(cpoc[i]+'.tz',bcT+'.c'+str(i+1)+'b')

					mc.connectAttr(cpoc[i]+'.px',bcP+'.c'+str(i+1)+'r')
					mc.connectAttr(cpoc[i]+'.py',bcP+'.c'+str(i+1)+'g')
					mc.connectAttr(cpoc[i]+'.pz',bcP+'.c'+str(i+1)+'b')

				for i in [0,-1]:

					mc.setAttr(cpoc[0]+'.ip',*self.arcPoints[i])
					mc.setAttr(cpoc[1]+'.ip',*self.arcPoints[i])
					mc.setAttr(trSpaces[i]+'.t',*mc.getAttr(dm+'.ot')[0])
					mc.setAttr(trSpaces[i]+'.r',*mc.getAttr(dm+'.or')[0])

				for i in [0,-1]:

					mc.disconnectAttr(arc[x][i]+'.oc',cpoc[i]+'.ic')

				mc.disconnectAttr(bn[x]+'.opr',fbfm+'.in20')
				mc.disconnectAttr(bn[x]+'.opg',fbfm+'.in21')
				mc.disconnectAttr(bn[x]+'.opb',fbfm+'.in22')

				mc.delete(fbfm,dm,cpoc,bcN,bcT,bcP)

				if len(xs)>1:
					loft=mc.createNode('loft')
					mc.setAttr(loft+'.autoReverse',False)
					mc.setAttr(loft+'.uniform',True)

			poci=mc.createNode('pointOnCurveInfo')

			i=0
			for f in [.01,.99]:

				pmm=mc.createNode('pointMatrixMult')

				if len(xs)>1:
					mc.connectAttr(mdlWidth[x]+'.o',pmm+'.ipz')

				mc.connectAttr(trSpaces[i]+'.wm[0]',pmm+'.im')
				mc.connectAttr(pmm+'.o',arc[x][0]+'.point'+str([1,3][i]))
				mc.connectAttr(pmm+'.o',arc[x][1]+'.point'+str([1,3][i]))

				mc.connectAttr(arc[x][i]+'.outputCurve',poci+'.inputCurve',f=True)
				mc.setAttr(poci+'.top',True)
				mc.setAttr(poci+'.parameter',f)

				pmm=mc.createNode('pointMatrixMult')

				mc.connectAttr(trSpaces[i]+'.worldInverseMatrix',pmm+'.inMatrix')
				mc.setAttr(pmm+'.ip',*mc.getAttr(poci+'.p')[0])
				ap=mc.getAttr(pmm+'.o')[0]
				mc.connectAttr(trSpaces[i]+'.worldMatrix',pmm+'.inMatrix',f=True)
				mc.setAttr(pmm+'.ip',*ap)

				if len(xs)>1: mc.connectAttr(mdlWidth[x]+'.o',pmm+'.ipz')

				mc.connectAttr(pmm+'.o',arc[x][i]+'.point2',f=True)

				i+=1

			self.curveShapes.append(mc.createNode('nurbsCurve',p=trSpaces[1],n=self.names[1]+'Shape#'))
			blendCurveShapes.append(mc.createNode('nurbsCurve',p=trSpaces[1],n=self.names[1]+'Shape#'))

			mc.connectAttr(arc[x][0]+'.outputCurve',self.curveShapes[x]+'.create')
			mc.connectAttr(arc[x][1]+'.outputCurve',blendCurveShapes[x]+'.create')

			spans=mc.getAttr(self.curveShapes[x]+'.spans')

			bs.append(mc.blendShape(blendCurveShapes[x],self.curveShapes[x],o='local',w=(0,1))[0])
			origShape.append(mc.listConnections(arc[x][0]+'.outputCurve',d=True,s=False,sh=True)[0])

			blendConnectAttrs=mc.listConnections(origShape[x]+'.worldSpace',p=True,sh=True)

			for b in blendConnectAttrs:
				mc.connectAttr(arc[x][0]+'.outputCurve',b,f=True)

			mc.connectAttr(arc[x][1]+'.outputCurve',bs[x]+'.it[0].itg[0].iti[6000].igt',f=True)

			rc=mc.createNode('rebuildCurve')
			mc.setAttr(rc+'.kcp',False)
			mc.connectAttr(arc[x][0]+'.sections',rc+'.spans',f=True)
			mc.setAttr(rc+'.kr',0)

			reverseCurve=mc.createNode('reverseCurve')
			mc.connectAttr(rc+'.oc',reverseCurve+'.ic')

			tg=mc.createNode('transformGeometry')
			mc.connectAttr(tg+'.og',self.curveShapes[x]+'.create',f=True)
			mc.connectAttr(reverseCurve+'.oc',tg+'.ig')
			mc.connectAttr(trSpaces[1]+'.worldInverseMatrix',tg+'.transform',f=True)

			if self.stretch<0 or self.squash<0:
				mc.connectAttr(bs[x]+'.og[0]',rc+'.ic')
			else:
				rc2=mc.createNode('rebuildCurve')
				mc.connectAttr(arc[x][0]+'.sections',rc2+'.spans',f=True)
				mc.setAttr(rc2+'.kr',0)

				mc.connectAttr(bs[x]+'.og[0]',rc2+'.ic',f=True)

				sub=mc.createNode('subCurve')
				mc.setAttr(sub+'.r',True)
				mc.setAttr(sub+'.min',0)
				mc.setAttr(sub+'.max',1)

				ext=''

				ext=mc.createNode('extendCurve')
				mc.setAttr(ext+'.rmk',True)
				mc.setAttr(ext+'.d',.00001)
				mc.connectAttr(sub+'.oc',ext+'.ic1',f=True)
				mc.connectAttr(ext+'.oc',rc+'.ic',f=True)

				mc.connectAttr(rc2+'.oc',sub+'.ic',f=True)

				if not mc.objExists(self.handles[0]+'.stretch'):
					mc.addAttr(self.handles[0],ln='stretch',at='float',min=0,dv=self.stretch,k=True)
				if not mc.objExists(self.handles[0]+'.squash'):
					mc.addAttr(self.handles[0],ln='squash',at='float',min=0,max=100,dv=self.squash,k=True)
				if not mc.objExists(self.handles[1]+'.length'):
					mc.addAttr(self.handles[1],ln='length',at='float',min=0,k=True)
				if not mc.objExists(self.handles[1]+'.overSquash'):
					mc.addAttr(self.handles[1],ln='overSquash',at='float',min=0,dv=100,k=False)
				if not mc.objExists(self.handles[1]+'.overStretch'):
					mc.addAttr(self.handles[1],ln='overStretch',at='float',min=0,dv=100,k=False)

				ci.append(mc.createNode('curveInfo'))
				mc.connectAttr(rc+'.oc',ci[x]+'.ic',f=True)

				mc.connectAttr(rc2+'.oc',ci[x]+'.ic',f=True)

				measureAttr=ci[x]+'.al'

				if x==0 and len(xs)>1:
					pma=mc.createNode('plusMinusAverage')
					mc.setAttr(pma+'.op',3)
					overStretchPMA=mc.createNode('plusMinusAverage')
					mc.setAttr(overStretchPMA+'.op',3)
					mc.connectAttr(overStretchPMA+'.o1',self.handles[1]+'.overStretch')
					overSquashPMA=mc.createNode('plusMinusAverage')
					mc.setAttr(overSquashPMA+'.op',3)
					mc.connectAttr(overSquashPMA+'.o1',self.handles[1]+'.overSquash')

				if len(xs)>1:
					mc.connectAttr(ci[x]+'.al',pma+'.i1['+str(x)+']')
					measureAttr=pma+'.o1'

				mc.setAttr(self.handles[1]+'.length',float(mc.getAttr(measureAttr)))

				if x==0:
					stretchADL=mc.createNode('plusMinusAverage')
					mc.setAttr(stretchADL+'.op',2)# subtract
					mc.connectAttr(measureAttr,stretchADL+'.i1[0]')
					mc.connectAttr(self.handles[1]+'.length',stretchADL+'.i1[1]')

					stretchMD=mc.createNode('multiplyDivide')
					mc.setAttr(stretchMD+'.op',2)# divide
					mc.connectAttr(stretchADL+'.o1',stretchMD+'.i1x')
					mc.connectAttr(self.handles[1]+'.length',stretchMD+'.i2x')
					stretch=stretchMD+'.ox'

					mc.connectAttr(self.handles[0]+'.stretch',stretchMD+'.i1y')
					mc.setAttr(stretchMD+'.i2y',100)
					stretchMax=stretchMD+'.oy'

					stretchMDClamp=mc.createNode('clamp')
					mc.connectAttr(stretchMax,stretchMDClamp+'.mxr')#stretchMD+'.oy'
					mc.setAttr(stretchMDClamp+'.mnr',0.0001)
					mc.connectAttr(stretchMax,stretchMDClamp+'.ipr')

					stretchMax=stretchMDClamp+'.opr'

					mc.connectAttr(stretchMax,stretchMDClamp+'.mxg')
					mc.setAttr(stretchMDClamp+'.mng',0.0001)
					mc.connectAttr(stretch,stretchMDClamp+'.ipg')
					stretchClamped=stretchMDClamp+'.opg'

					mc.connectAttr(stretch,stretchMDClamp+'.mxb')
					mc.setAttr(stretchMDClamp+'.mnb',0.0001)
					mc.connectAttr(stretch,stretchMDClamp+'.ipb')
					stretchClampedLo=stretchMDClamp+'.opb'

					stretchGapPMA=mc.createNode('plusMinusAverage')# difference between max stretch and current stretch
					mc.setAttr(stretchGapPMA+'.op',2)# subtract
					mc.connectAttr(stretchMax,stretchGapPMA+'.i1[0]')
					mc.connectAttr(stretchClampedLo,stretchGapPMA+'.i1[1]')
					stretchGAP=stretchGapPMA+'.o1'

					stretchGapPercMD=mc.createNode('multiplyDivide')# %difference between max stretch and current stretch
					mc.setAttr(stretchGapPercMD+'.op',2)# divide
					mc.connectAttr(stretchGAP,stretchGapPercMD+'.i1x')
					mc.connectAttr(stretchMax,stretchGapPercMD+'.i2x')
					stretchGapPerc=stretchGapPercMD+'.ox'

					stretchPlusOneNode=mc.createNode('addDoubleLinear')
					mc.connectAttr(stretchClampedLo,stretchPlusOneNode+'.i1')
					mc.setAttr(stretchPlusOneNode+'.i2',1)
					stretchPlusOne=stretchPlusOneNode+'.o'

					overStretchSubNode=mc.createNode('plusMinusAverage')
					mc.setAttr(overStretchSubNode+'.op',2)# subtract
					mc.connectAttr(stretchClampedLo,overStretchSubNode+'.i1[0]')#stretchMinusFallOff
					mc.connectAttr(stretchClamped,overStretchSubNode+'.i1[1]')#stretchClampedMinusFallOff
					overStretchDivNode=mc.createNode('multiplyDivide')
					mc.setAttr(overStretchDivNode+'.op',2)# divide
					mc.connectAttr(overStretchSubNode+'.o1',overStretchDivNode+'.i1x')
					mc.connectAttr(stretchPlusOne,overStretchDivNode+'.i2x')
					overStretch=overStretchDivNode+'.ox'

					if len(xs)>1:
						mc.connectAttr(overStretch,overStretchPMA+'.i1['+str(x)+']')

					#squash
					squashPMA=mc.createNode('plusMinusAverage')
					mc.setAttr(squashPMA+'.op',2)# subtract
					mc.connectAttr(self.handles[1]+'.length',squashPMA+'.i1[0]')
					mc.connectAttr(measureAttr,squashPMA+'.i1[1]')
					squashDist=squashPMA+'.o1'

					squashDistClamp=mc.createNode('clamp')
					mc.connectAttr(squashDist,squashDistClamp+'.mxr')#stretchMD+'.oy'
					mc.setAttr(squashDistClamp+'.mnr',0.00001)
					mc.connectAttr(squashDist,squashDistClamp+'.ipr')
					squashDistClamped=squashDistClamp+'.opr'

					squashMD=mc.createNode('multiplyDivide')
					mc.setAttr(squashMD+'.op',2)# divide
					mc.connectAttr(squashDistClamped,squashMD+'.i1x')
					mc.connectAttr(self.handles[1]+'.length',squashMD+'.i2x')
					squash=squashMD+'.ox'

					mc.connectAttr(self.handles[0]+'.squash',squashMD+'.i1y')
					mc.setAttr(squashMD+'.i2y',100)
					squashMax=squashMD+'.oy'

					squashMDClamp=mc.createNode('clamp')
					mc.connectAttr(squashMax,squashMDClamp+'.mxr')
					mc.setAttr(squashMDClamp+'.mnr',0.00001)
					mc.connectAttr(squashMax,squashMDClamp+'.ipr')
					squashMax=squashMDClamp+'.opr'

					mc.connectAttr(squashMax,squashMDClamp+'.mxg')
					mc.setAttr(squashMDClamp+'.mng',0.0001)
					mc.connectAttr(squash,squashMDClamp+'.ipg')
					squashClamped=squashMDClamp+'.opg'

					mc.connectAttr(squash,squashMDClamp+'.mxb')
					mc.setAttr(squashMDClamp+'.mnb',0.0001)
					mc.connectAttr(squash,squashMDClamp+'.ipb')
					squashClampedLo=squashMDClamp+'.opb'

					squashGapPMA=mc.createNode('plusMinusAverage')# difference between max squash and current squash
					mc.setAttr(squashGapPMA+'.op',2)# subtract
					mc.connectAttr(squashMax,squashGapPMA+'.i1[0]')
					mc.connectAttr(squashClampedLo,squashGapPMA+'.i1[1]')
					squashGAP=squashGapPMA+'.o1'

					squashGapPercMD=mc.createNode('multiplyDivide')# %difference between max squash and current squash
					mc.setAttr(squashGapPercMD+'.op',2)# divide
					mc.connectAttr(squashGAP,squashGapPercMD+'.i1x')
					mc.connectAttr(squashMax,squashGapPercMD+'.i2x')
					squashGapPerc=squashGapPercMD+'.ox'

					overSquashSubNode=mc.createNode('plusMinusAverage')
					mc.setAttr(overSquashSubNode+'.op',2)# subtract
					mc.connectAttr(squashClampedLo,overSquashSubNode+'.i1[0]')#squashMinusFallOff
					mc.connectAttr(squashClamped,overSquashSubNode+'.i1[1]')#squashClampedMinusFallOff
					overSquash=overSquashSubNode+'.o1'#overSquashDivNode+'.ox'

					overSquashDistanceMDL=mc.createNode('multDoubleLinear')
					mc.connectAttr(self.handles[1]+'.length',overSquashDistanceMDL+'.i1')
					mc.connectAttr(overSquash,overSquashDistanceMDL+'.i2')
					overSquashDistanceClamp=mc.createNode('clamp')
					mc.connectAttr(overSquashDistanceMDL+'.o',overSquashDistanceClamp+'.mxr')#stretchMD+'.oy'
					mc.setAttr(overSquashDistanceClamp+'.mnr',0.00001)
					mc.connectAttr(overSquashDistanceMDL+'.o',overSquashDistanceClamp+'.ipr')
					overSquashDistance=overSquashDistanceClamp+'.opr'

					if len(xs)>1:
						mc.connectAttr(overSquash,overSquashPMA+'.i1['+str(x)+']')

				if mc.objExists(ext+'.d'): mc.connectAttr(overSquashDistance,ext+'.d')
				mc.connectAttr(overStretch,sub+'.min')

			disconnectNodes(origShape[x])
			mc.delete(origShape[x])
			disconnectNodes(blendCurveShapes[x])
			mc.delete(blendCurveShapes[x])

			if x==len(xs)-1:
				if 'spans' not in mc.listAttr(self.handles[1]):
					mc.addAttr(self.handles[1],ln='spans',at='long',min=0,dv=spans,k=True)
					mc.connectAttr(self.handles[1]+'.spans',arc[0][0]+'.sections')
					mc.connectAttr(self.handles[1]+'.spans',arc[0][1]+'.sections')

			if len(xs)>1:
				mc.connectAttr(tg+'.og',loft+'.ic['+str(x)+']')
				disconnectNodes(self.curveShapes[x])
				if x==1:
					mc.delete(self.curveShapes[x])

					self.outputSurface=loft+'.os'

					if self.createSurface:
						self.surface=mc.createNode('nurbsSurface',p=trSpaces[1])
						mc.connectAttr(self.outputSurface,self.surface+'.create',f=True)

					if not self.createSurface or ( self.scaleLength and mc.objExists(self.handles[1]+'.length') ):

						self.curveShapes[0]=mc.createNode('nurbsCurve',p=trSpaces[1])
						cfsi=mc.createNode('curveFromSurfaceIso')
						mc.setAttr(cfsi+'.r',True)
						mc.setAttr(cfsi+'.rv',True)
						mc.setAttr(cfsi+'.min',0)
						mc.setAttr(cfsi+'.max',1)
						mc.setAttr(cfsi+'.idr',1)
						mc.setAttr(cfsi+'.idr',1)
						mc.setAttr(cfsi+'.iv',.5)
						mc.connectAttr(self.outputSurface,cfsi+'.is',f=True)
						mc.connectAttr(cfsi+'.oc',self.curveShapes[0]+'.create',f=True)
						self.outputCurve=cfsi+'.oc'

		for i in [0,-1]:
			if self.handleType[i]=='none':
				self.handleShapes.append([''])
			else:
				if 'type' not in self.handleOptions[i]: self.handleOptions[i]['type']=self.handleType[i-1]
				self.handleShapes.append(Handle(self.handles[i],**self.handleOptions[i]))

		keep=keep+[self.surface]+self.handleShapes[0]+self.handleShapes[-1]

		if not self.createSurface or self.scaleLength: keep.append(self.curveShapes[0])

		cleanup.extend\
		(
			removeAll\
			(
				keep,
				(
					removeDuplicates(mc.listRelatives(trSpaces[1],c=True,type='nurbsSurface'))+
					removeDuplicates(mc.listRelatives(trSpaces[1],c=True,type='nurbsCurve'))
				)
			)
		)

		if self.createSurface:
			self.outputSurface=self.surface+'.worldSpace'
		else:
			self.outputCurve=self.curveShapes[0]+'.worldSpace'

		mc.addAttr(self.handles[0],ln='arcWeight',at='double',k=True,min=0,max=1,dv=self.arcWeight)
		if self.createSurface:
			mc.addAttr(self.handles[1],ln='width',at='double',k=True,min=.001,dv=self.width)
			mc.connectAttr(self.handles[1]+'.width',mdlWidth[0]+'.i1')
			mc.connectAttr(self.handles[1]+'.width',mdlWidth[1]+'.i1')

		rev=mc.createNode('reverse')

		mc.connectAttr(self.handles[0]+'.arcWeight',rev+'.ix')

		mc.connectAttr(rev+'.ox',bn[0]+'.b')
		if self.createSurface: mc.connectAttr(rev+'.ox',bn[1]+'.b')

		mc.connectAttr(rev+'.ox',bs[0]+'.en')
		if self.createSurface: mc.connectAttr(rev+'.ox',bs[1]+'.en')

		for i in [0,-1]:

			if self.parents[i]=='.':
				mc.parent(self.handles[i],self.handles[[-1,0][i]])
			elif mc.objExists(self.parents[i]):
				mc.parent(self.handles[i],self.parents[i])

			if self.softParents[i]=='.':
				self.parentSpaces[i]=ParentSpace(self.handles[i],self.handles[[-1,0][i]])
			elif mc.objExists(self.softParents[i]):
				self.parentSpaces[i]=ParentSpace(self.handles[i],self.softParents[i])

		for c in cleanup:
			if mc.objExists(c):
				disconnectNodes(c)
				mc.delete(c)

		if self.scaleLength and mc.objExists(self.handles[1]+'.length'):

			measureCurve=mc.createNode('nurbsCurve',p=self.handles[1],n=self.names[1]+'Shape#')
			mc.connectAttr(self.curveShapes[0]+'.local',measureCurve+'.create')
			ciOrig=mc.createNode('curveInfo')
			mc.connectAttr(measureCurve+'.worldSpace[0]',ciOrig+'.ic',f=True)
			#mc.connectAttr(ciOrig+'.al',self.handles[1]+'.length',f=True)

			divLength=mc.createNode('multiplyDivide')
			mc.setAttr(divLength+'.op',2)
			mc.connectAttr(self.handles[1]+'.length',divLength+'.i1x')
			mc.setAttr(divLength+'.i2x',mc.getAttr(self.handles[1]+'.length'))
			multLength=mc.createNode('multiplyDivide')
			mc.setAttr(multLength+'.op',1)
			mc.connectAttr(ciOrig+'.al',multLength+'.i1x')
			mc.connectAttr(divLength+'.ox',multLength+'.i2x')
			for attr in [overSquashDistanceMDL+'.i1',stretchADL+'.i1[1]',stretchMD+'.i2x',squashPMA+'.i1[0]',squashMD+'.i2x']:
				mc.connectAttr(multLength+'.ox',attr,f=True)

			mc.addAttr(self.handles[1],ln='globalLength',at='double')
			mc.connectAttr(multLength+'.ox',self.handles[1]+'.globalLength',f=True)
			mc.addAttr(self.handles[1],ln='lengthScale',at='double')
			mc.connectAttr(divLength+'.ox',self.handles[1]+'.lengthScale',f=True)

			mc.disconnectAttr(self.curveShapes[0]+'.local',measureCurve+'.create')
			mc.setAttr(measureCurve+'.intermediateObject',True)
			#mc.setAttr(self.handles[1]+'.length',k=False,cb=False)

			if self.createSurface:
				mc.delete(self.curveShapes[0])

		# put lists back in input order
		for lo in self.__dict__:
			if isinstance(self.__dict__[lo],list):
				exec('self.'+lo+'.reverse()')

		self[:]=list(self.handles)

