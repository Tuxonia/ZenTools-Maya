import maya.cmds as mc
import maya.mel as mel
import maya.utils as mu
from zen.isIterable import isIterable
from zen.removeDuplicates import removeDuplicates
from zen.removeAll import removeAll
from zen.listNodeConnections import listNodeConnections
from zen.getIDs import getIDs
from zen.shape import shape
from zen.firstOpenPlug import firstOpenPlug
from zen.iterable import iterable
from zen.firstOpenPlug import firstOpenPlug
from zen.getReversed import getReversed
from zen.deferExec import deferExec
from zen.midPoint import midpoint
from zen.distanceBetween import distanceBetween
from zen.geometry import polyComponentList

class Wrap(list):
	
	def __init__(self,*args,**keywords):
		
		# default options
		
		self.controlObjects=['']
		self.baseShapes=['']
		self.influences=[]
		self.deformed=[]
		self.nurbsSamples=[10.0]
		self.smoothness=[0.0]
		self.nurbsSamples=[10]
		self.wrapSmoothness=[1]
		self.exclusiveBind=True
		self.maxDistance=0
		self.calculateMaxDistance=False
		self.smooth=-1
		self.smoothType=0
		
		self.wrapOptions=\
		{
			'name':'',
			'before':False,
			'after':False,
			'split':False,
			'frontOfChain':False,
			'parallel':False,
			'prune':False,
		}
		
		self.shortNames=\
		{
			'co':'controlObject',
			'bsa':'baseShapeAttr',
			'dsa':'deformShapeAttr',
			'd':'deformed',
			'n':'name',
			'bf':'before',
			'af':'after',
			'sp':'split',
			'foc':'frontOfChain',
			'par':'parallel',
			'pr':'prune',
			'eb':'exclusiveBind',
			'md':'maxDistance',
			'cmd':'calculateMaxDistance'   
		}
		
		# attributes
		
		self.inputType=[]
		
		for k in keywords:
			if k in self.__dict__:
				exec('self.'+k+'=keywords[k]')
			elif k in self.wrapOptions:
				exec('self.wrapOptions["'+k+'"]=keywords[k]')
			elif k in self.shortNames:
				if shortNames[k] in self.__dict__:
					exec('self.'+shortNames[k]+'=keywords[k]')
				elif shortNames[k] in self.wrapOptions:
					exec('self.wrapOptions["'+shortNames[k]+'"]=keywords[k]')
					
		if isinstance(self.smoothType,str) and self.smoothType in ['exponential','linear']: 
			self.smoothType=['exponential','linear'].index(self.smoothType)
				
		self.influences=iterable(self.influences)
		self.baseShapes=iterable(self.baseShapes)
		self.deformed=iterable(self.deformed)
		
		# parse arguments
		
		if len(args)==0 and (len(self.influences)==0 or len(self.deformed)==0):
			args=mc.ls(sl=True)
			
		sel=[]
		for a in args:
			if\
			(
				(isinstance(a,str) and len(a.split('.'))>1 and str(mc.getAttr(a,type=True)) in ['mesh','nurbsCurve','nurbsSurface']) or
				(isIterable(a) and len(mc.ls(a,o=True))>0 and mc.nodeType(mc.ls(a,o=True)[0]) in ['mesh','nurbsCurve','nurbsSurface'])
			):
				sel.append(a)
			elif isinstance(a,str) and mc.nodeType(shape(a)) in ['mesh','nurbsCurve','nurbsSurface']:
				sel.append(shape(a))
				
		if len(self.influences)==0 and len(self.deformed)==0:
			self.influences=sel[:-1]
			self.deformed=sel[-1:]
		elif len(self.influences)==0 and len(self.deformed)>0:
			self.influences=sel
		elif len(self.influences)>0 and len(self.deformed)==0:
			self.deformed=sel

		self.create()

		self.addInfluences\
		(
			nurbsSamples=self.nurbsSamples,
			wrapSmoothness=self.wrapSmoothness,
			controlObjects=self.controlObjects,
			smooth=self.smooth,
			smoothType=self.smoothType,
			*self.influences
		)

	def create(self):
		
		woHold=dict(self.wrapOptions)
		for wo in woHold:
			if\
			(
				(isinstance(self.wrapOptions[wo],str) and self.wrapOptions[wo]=='') or
				(isinstance(self.wrapOptions[wo],bool) and self.wrapOptions[wo]==False)
			):
				del(self.wrapOptions[wo])
		self.wrapOptions['type']='wrap'
		
		if len(self.deformed)>0:
			
			self.deformed[0]=shape(self.deformed[0])
			
			if len(iterable(mc.listHistory(self.deformed[0])))==0:
				duplicateShape(self.deformed[0],ah=True)
				
			self[:]=mc.deformer(self.deformed[0],**self.wrapOptions)
			
		if len(self.deformed)>1:
			
			i=1
			for d in self.deformed[1:]:
				
				d=self.deformed[i]=shape(d)
				
				mc.deformer(self[0],e=True,g=d)
				
				new=mc.listConnections(self[0]+'.og['+str(i)+']',sh=True)[0]
				
				if d!=new and mc.objExists(new): # new node has been created - rename
					
					mc.rename(d,d+'Orig#')
					mc.rename(new,d)
					
				i+=1
				
		mc.setAttr(self[0]+'.maxDistance',self.maxDistance)
				
		if self.exclusiveBind:
			mc.setAttr(self[0]+'.exclusiveBind',True)
		
	def addInfluences(self,*influences,**keywords):
				
		controlObjects=['']
		baseShapes=['']
		wrapSmoothness=[1]
		nurbsSamples=[10]
		smooth=-1
		smoothType=0
		influences=list(influences)
		
		shortNames=\
		{
			'co':'controlObjects'
		}
				
		for k in keywords:
			if k in locals():
				exec(k+'=keywords[k]')
			elif k in shortNames:
				exec(shortNames[k]+'=keywords[k]')
				
		controlObjects=iterable(controlObjects)
		baseShapes=iterable(baseShapes)
		wrapSmoothness=iterable(wrapSmoothness)
		nurbsSamples=iterable(nurbsSamples)
		
		if self.influences==influences:
			self.influences=[]
		else:
			influencesHold=influences
			for inf in influencesHold:
				if inf in self.influences:
					influences.remove(inf)
				else:
					self.influences.append(inf)
				
		while len(controlObjects)<len(influences):
			  controlObjects.append(controlObjects[-1])
		while len(baseShapes)<len(influences):
			  baseShapes.append(baseShapes[-1])
		while len(wrapSmoothness)<len(influences):
			  wrapSmoothness.append(wrapSmoothness[-1])
		while len(nurbsSamples)<len(influences):
			  nurbsSamples.append(nurbsSamples[-1])
			  
		for i in range(0,len(influences)):
			
			bsh=baseShapes[i]
			inf=influences[i]
			ctrlObj=controlObjects[i]
			nurbsSample=self.nurbsSamples[i]
			wrapSmooth=self.wrapSmoothness[i]
			infFaces=[]
			infSourceShape=''
			infShape=''
			infTr=''
			shapeType=''
			
			if isinstance(inf,str):
				
				if len(inf.split('.'))>1:
					
					shapeType=str(mc.getAttr(inf,type=True))
					
					if len(iterable(mc.ls(inf,o=True,type='dagNode')))>0 and len(iterable(mc.listRelatives(mc.ls(inf,o=True),p=True)))>0:
						infTr=mc.listRelatives(mc.ls(inf,o=True),p=True)[0]
						infShape=shape(infTr)
					else:
						infShapeHist=iterable(mc.ls(iterable(mc.listHistory(inf,f=True,af=True)),type='shape'))
						if len(infShapeHist)>0:
							infShape=infShapeHist[0]
							infTr=mc.listRelatives(infShape,p=True)
						
				else:
					
					shapeType=mc.nodeType(inf)
					infShape=infSourceShape=inf
					infTr=mc.listRelatives(inf,p=True)
					
			elif isIterable(inf):
				
				infShape=mc.ls(inf,o=True)[0]
				infTr=mc.listRelatives(infShape,p=True)[0]
				shapeType=mc.nodeType(infShape)
								
				if mc.nodeType(infShape)=='mesh':
					
					inf=mc.polyListComponentConversion(inf,tf=True)

					inputComponents=[]
					for fStr in inf: 
						inputComponents.append(fStr.split('.')[-1])
					
					pco=mc.createNode('polyChipOff')
					mc.setAttr(pco+'.dup',True)
					mc.setAttr(pco+'.inputComponents',len(inputComponents),type='componentList',*inputComponents)
					mc.connectAttr(infShape+'.outMesh',pco+'.ip')
					
					psep=mc.createNode('polySeparate')
					mc.setAttr(psep+'.ic',2)
					mc.connectAttr(pco+'.out',psep+'.ip')
					
					inf=psep+'.out[1]'
					
					if not(isinstance(bsh,str) and mc.objExists(bsh)):
												
						bshSource=''
						
						for m in removeAll(infShape,mc.ls(iterable(mc.listHistory(infShape)),type='mesh')):
							
							if\
							(
								len(mc.ls(m+'.vtx[*]',fl=True))==len(mc.ls(infShape+'.vtx[*]',fl=True)) and
								len(mc.ls(m+'.f[*]',fl=True))==len(mc.ls(infShape+'.f[*]',fl=True)) and
								len(mc.ls(m+'.e[*]',fl=True))==len(mc.ls(infShape+'.e[*]',fl=True)) and 
								len(removeAll(m,mc.listHistory(m)))==0
							):
								isBSTarget=False
								for bsConn in iterable(mc.listConnections(m,type='blendShape',p=True)):
									if 'inputTarget' in '.'.join(bsConn.split('.')[1:]):
										isBSTarget=True
										break
								if isBSTarget:
									continue
								else:
									bshSource=m
									break
								
						if bshSource=='':
														
							bshSource=mc.createNode('mesh',p=infTr)
							mc.connectAttr(infShape+'.outMesh',bshSource+'.inMesh')
							mc.blendShape(infShape,bshSource,w=[1,1])
							mc.delete(bshSource,ch=True)
							mc.setAttr(bshSource+'.io',True)

						pco=mc.createNode('polyChipOff')
						mc.setAttr(pco+'.dup',True)
						mc.setAttr(pco+'.inputComponents',len(inputComponents),type='componentList',*inputComponents)
						mc.connectAttr(bshSource+'.outMesh',pco+'.ip')
						
						psep=mc.createNode('polySeparate')
						mc.setAttr(psep+'.ic',2)
						mc.connectAttr(pco+'.out',psep+'.ip')
						
						bsh=psep+'.out[1]'
								
				else:
					
					inf=infShape

			plug=firstOpenPlug(self[0]+'.basePoints')
					
			if isinstance(inf,str) and mc.objExists(inf):
				
				if len(inf.split('.'))<=1:
					
					if mc.nodeType(shape(inf))=='mesh':
						inf=shape(inf)+'.outMesh'
					else:
						inf=shape(inf)+'.local'
					
			
			if isinstance(bsh,str) and mc.objExists(bsh):
				
				if len(bsh.split('.'))<=1:

					if mc.nodeType(shape(bsh))=='mesh':
						bsh=shape(bsh)+'.outMesh'
					else:
						bsh=shape(bsh)+'.local'
					
			else:
				
				bshShape=mc.createNode(shapeType)
				
				if shapeType=='mesh':
					mc.connectAttr(inf,bshShape+'.inMesh')
					mc.blendShape(infShape,bshShape,w=(1,1))
					mc.delete(bshShape,ch=True)
					bsh=bsh+'.outMesh'
				else:
					mc.connectAttr(inf,bshShape+'.create')
					mc.blendShape(infShape,bshShape,w=(1,1))
					mc.delete(bshShape,ch=True)
					bsh=bsh+'.local'
					
				mc.setAttr(bshShape+'.io',True)
				
			#mc.connectAttr(inf,self[0]+'.driverPoints['+str(plug)+']',f=True)
			#mc.connectAttr(bsh,self[0]+'.basePoints['+str(plug)+']',f=True
				
			# poly smooth
			if shapeType=='mesh':
				
				pspInf=mc.createNode('polySmoothProxy')
				mc.setAttr(pspInf+'.kb',False)
				mc.connectAttr(inf,pspInf+'.ip')
				inf=pspInf+'.out'
				
				pspBase=mc.createNode('polySmoothProxy')
				mc.setAttr(pspBase+'.kb',False)
				mc.connectAttr(bsh,pspBase+'.ip')
				bsh=pspBase+'.out'
				
			mc.connectAttr(inf,self[0]+'.driverPoints['+str(plug)+']',f=True)
			mc.connectAttr(bsh,self[0]+'.basePoints['+str(plug)+']',f=True)

			# add wrap control attributes
			
			if not mc.objExists(ctrlObj):
				ctrlObj=infTr
							
			if shapeType=='mesh':
				
				if not 'wrapSmoothLevels' in mc.listAttr(ctrlObj):
					mc.addAttr(ctrlObj,ln='wrapSmoothLevels',at='short',dv=0)
					
				mc.setAttr(ctrlObj+'.wrapSmoothLevels',k=False,cb=True)
				mc.connectAttr(ctrlObj+'.wrapSmoothLevels',pspInf+'.el')
				mc.connectAttr(ctrlObj+'.wrapSmoothLevels',pspBase+'.el')
				mc.connectAttr(ctrlObj+'.wrapSmoothLevels',pspInf+'.ll')
				mc.connectAttr(ctrlObj+'.wrapSmoothLevels',pspBase+'.ll')
				
				if not 'wrapSmoothType' in mc.listAttr(ctrlObj):
					mc.addAttr(ctrlObj,ln='wrapSmoothType',at='enum',en='exponential:linear',min=0,max=1,dv=smoothType)
					
				mc.setAttr(ctrlObj+'.wrapSmoothType',k=False,cb=True)
				mc.connectAttr(ctrlObj+'.wrapSmoothType',pspInf+'.mth')
				mc.connectAttr(ctrlObj+'.wrapSmoothType',pspBase+'.mth')
				
				if not 'inflType' in mc.listAttr(ctrlObj):
					mc.addAttr(ctrlObj,ln='inflType',at='enum',en='none:point:face',min=1,max=2,dv=2)
					
				mc.setAttr(ctrlObj+'.inflType',k=False,cb=True)
				mc.connectAttr(ctrlObj+'.inflType',self[0]+'.inflType['+str(plug)+']')
				
			else:
				if not 'nurbsSamples' in mc.listAttr(ctrlObj):
					mc.addAttr(ctrlObj,ln='nurbsSamples',at='short',dv=nurbsSample)
					
				mc.setAttr(ctrlObj+'.nurbsSamples',k=False,cb=True)
				mc.connectAttr(ctrlObj+'.nurbsSamples',self[0]+'.nurbsSamples['+str(plug)+']')

			if self.calculateMaxDistance:
				
				greatestDistance=0.0
				
				if shapeType=='mesh':
	
					distCheckMesh=mc.createNode('mesh',p=infTr)
					mc.connectAttr(inf,distCheckMesh+'.inMesh')
					
					deformedCP=''
					if mc.nodeType(shape(self.deformed[0]))=='mesh':
						deformedCP=mc.createNode('closestPointOnMesh')
						mc.connectAttr(self.deformed[0]+'.worldMesh[0]',deformedCP+'.im')
					elif mc.nodeType(shape(self.deformed[0]))=='nurbsCurve':
						deformedCP=mc.createNode('closestPointOnCurve')
						mc.connectAttr(self.deformed[0]+'.worldSpace',deformedCP+'.ic')
					elif mc.nodeType(shape(self.deformed[0]))=='nurbsSurface':
						deformedCP=mc.createNode('closestPointOnSurface')
						mc.connectAttr(self.deformed[0]+'.worldSpace',deformedCP+'.is')

					for f in mc.ls(distCheckMesh+'.f[*]',fl=True):
						
						center=midPoint(f)
						mc.setAttr(deformedCP+'.ip',*center)
						closestPoint=mc.getAttr(deformedCP+'.p')[0]
						distance=distanceBetween(closestPoint,center)
						
						if distance>greatestDistance:
							greatestDistance=distance
						
					mc.disconnectAttr(inf,distCheckMesh+'.inMesh')
					mc.delete(distCheckMesh)
						
				if greatestDistance*2>mc.getAttr(self[0]+'.maxDistance'):
					mc.setAttr(self[0]+'.maxDistance',greatestDistance*2)
					
			if shapeType=='mesh':
				
				if smooth>=0:
					
					mc.setAttr(ctrlObj+'.wrapSmoothLevels',smooth)
					
				elif mc.nodeType(shape(self.deformed[0]))=='mesh':
					
					faceCount=0
					for d in self.deformed:
						if mc.nodeType(shape(d))=='mesh':
							faceCount+=len(mc.ls(shape(d)+'.f[*]',fl=True))
							
					smoothSampleMesh=mc.createNode('mesh',p=infTr)
					mc.connectAttr(inf,smoothSampleMesh+'.inMesh')
					
					smoothFaceCount=0
					n=0
					
					while len(mc.ls(smoothSampleMesh+'.f[*]',fl=True))<faceCount:
						mc.setAttr(ctrlObj+'.wrapSmoothLevels',n)
						n+=1
						
					if len(mc.ls(smoothSampleMesh+'.f[*]',fl=True))>faceCount*1.5:
						mc.setAttr(ctrlObj+'.wrapSmoothLevels',mc.getAttr(ctrlObj+'.wrapSmoothLevels')-1)
						
					mc.disconnectAttr(inf,smoothSampleMesh+'.inMesh')
					mc.delete(smoothSampleMesh)
				