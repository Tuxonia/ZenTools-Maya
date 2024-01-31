import maya.cmds as mc
import maya.mel as mel
from decimal import Decimal
from zen.melEncode import melEncode
from zen.isIterable import isIterable
from zen.removeDuplicates import removeDuplicates
from zen.getIDs import getIDs
from zen.distanceBetween import distanceBetween
from zen.uniqueNames import uniqueNames
from zen.iterable import iterable
from zen.geometry.polyFaceList import PolyFaceList

class ClosestPoints(list):

	def __init__(self,*args,**keywords):
		
		#check to make sure unique names are used in scene
		uniqueNames(iterable(mc.ls(type='dagNode')),re=True)
		
		self.tol=.001
		
		for k in keywords:
			if k in self.__dict__:
				if type(eval('self.'+k)).__name__==type(keywords[k]).__name__:
					exec('self.'+k+'=keywords[k]')
		
		sel=[]
		for a in args:
			if isIterable(a):
				sel.extend(a)
			else:
				sel.append(a)
				
		sel=removeDuplicates(mc.ls(sel)+mc.ls(sl=True,o=True))
		
		if len(sel)<2: raise Exception("Procedure requires two polygon meshes, nurbs surfaces, or nurbs curves.")
		else: sel=sel[:2]			
		
		oo=Decimal('Infinity')
		self[:]=[[oo,oo,oo],[oo,oo,oo]]
		
		noo=Decimal('-Infinity')
		self.antipodes=[[noo,noo,noo],[noo,noo,noo]]  
		
		self.uvs=[(-1,-1),(-1,-1)]
		self.closestFaces=['','']
		self.closestFaceIDs=[-1,-1]
		self.closestVertexIDs=[-1,-1]
		self.antipodeFaces=['','']
		self.antipodeFaceIDs=[-1,-1]
		self.antipodeUVs=[(-1,-1),(-1,-1)]
		self.antipodeVertexIDs=[-1,-1]

		self.trs,self.types,self.shapes,self.shAttr,self.knots,self.roughAPIDs,self.roughCPIDs,self.uv=[],[],[],[],[],[],[],[]
		density,maxDensity,cpID,searchID,i=0,0,0,0,0
		ci,si='',''
				
		for s in sel: # find shapes and node types and determine which is denser
			
			if len(s.split('.'))>1:
				sha=s
				nt=mc.getAttr(sha,type=True)
				if nt=='nurbsCurve' or nt=='nurbsSurface' or nt=='mesh':
					self.shapes.append('')
					self.trs.append('')
					self.shAttr.append(sha)
					self.types.append(nt)
				else:
					raise Exception("Arguments must be polygon meshes, nurbs surfaces, or nurbs curves.")
			
			elif  len(mc.ls(s,tr=True))>0:
				
				sh=[]
				for c in \
				(
					mc.listRelatives(s,c=True,s=True,ni=True,type='nurbsCurve'),
					mc.listRelatives(s,c=True,s=True,ni=True,type='nurbsSurface'),
					mc.listRelatives(s,c=True,s=True,ni=True,type='mesh')
				):
					if isIterable(c) and len(c)>0: sh=c[0]				
				
				if isinstance(sh,str) and mc.objExists(sh):
					nt=mc.nodeType(sh)
					self.shapes.append(sh)
					self.trs.append(s)
					self.types.append(nt)
					if nt=='mesh': sha=s+'.outMesh'
					if nt=='nurbsSurface' or nt=='nurbsCurve': sha=s+'.local'
					self.shAttr.append(sha)
					
			elif mc.objExists(s):
								
				nt=mc.nodeType(s)
				
				if nt=='nurbsCurve' or nt=='nurbsSurface' or nt=='mesh':
					self.shapes.append(s)
					self.trs.append(mc.listRelatives(s,p=True)[0])
					self.types.append(nt)
					if nt=='mesh': sha=s+'.worldMesh[0]'
					if nt=='nurbsSurface' or nt=='nurbsCurve': sha=s+'.local'
					self.shAttr.append(sha)
					
				else:
					raise Exception("Arguments must be polygon meshes, nurbs surfaces, or nurbs curves.")
					
			else:
				raise Exception("Arguments must be polygon meshes, nurbs surfaces, or nurbs curves.")
							
			if nt=='mesh':
				self.knots.append({})
				density=len(mc.ls(sh+'.vtx[*]',fl=True))
			elif nt=='nurbsCurve':
				if not mc.objExists(ci): ci=mc.createNode('curveInfo')
				mc.connectAttr(sha,ci+'.ic',f=True)
				ku=[]
				kuq=removeDuplicates(mc.getAttr(ci+'.knots')[0])
				for u in kuq:
					if u>=0: ku.append(float(u))
					else: kuq.pop()
				k={'u':tuple(ku)}
				self.knots.append(k)
				density=len(k['u'])
			elif nt=='nurbsSurface':
				if not mc.objExists(si): si=mc.createNode('surfaceInfo')
				mc.connectAttr(sha,si+'.is',f=True)
				ku=[]
				kuq=removeDuplicates(mc.getAttr(ci+'.knotsU')[0])
				for u in kuq:
					if u>=0: ku.append(float(u))
					else: kuq.pop()
				kv=[]
				kvq=removeDuplicates(mc.getAttr(ci+'.knotsV')[0])
				for v in kvq:
					if v>=0: kv.append(float(v))
					else: kvq.pop()
				k={'u':tuple(ku),'v':tuple(kv)}
				self.knots.append(k)
				density=len(k['u'])*len(k['v'])
				
			self.uv.append([-1.0,-1.0])
			self.roughAPIDs.append([-1.0,-1.0])
			self.roughCPIDs.append([-1.0,-1.0])
							
			if density>maxDensity:
				maxDensity=density
				cpID=i
			else:
				searchID=i
			i+=1
			
		if self.types[searchID]=='mesh' and self.types[cpID]!='mesh':
			temp=cpID
			cpID=searchID
			searchID=temp
			
		if mc.objExists(ci): mc.delete(ci)
		if mc.objExists(si): mc.delete(si)
					
		self.lookup(cpID)

		#for p in self:
		#	mc.spaceLocator(p=p)
			
		#mc.spaceLocator(p=self.getAntipodes(searchID))
		#mc.spaceLocator(p=self.getAntipodes(cpID))
			
		
	def lookup(self,id,cp=True,fp=False,ap=False):
		
		if (id==0 and cp) or (abs(id)==1 and (ap or fp)): 
			cpID=0
			searchID=1
		else:
			cpID=1
			searchID=0
		
		cpTr=self.trs[cpID]
		cpSh=self.shapes[cpID]
		cpType=self.types[cpID]
		cpShAttr=self.shAttr[cpID]
		cpKnots=self.knots[cpID]
		searchTr=self.trs[searchID]
		searchSh=self.shapes[searchID]
		searchType=self.types[searchID]
		searchShAttr=self.shAttr[searchID]
		searchKnots=self.knots[searchID]
		
		if not mc.objExists(searchSh):
			tempList=searchShAttr.split('.')
			if len(tempList)>1 and tempList[1]=='local':  searchShAttr=tempList[0]+'.worldSpace'
			if len(tempList)>1 and tempList[1]=='outMesh':  searchShAttr=tempList[0]+'.worldMesh'
			searchTr=mc.createNode('transform')
			searchSh=mc.createNode(searchType,p=searchTr)
			if searchType=='mesh':
				mc.connectAttr(searchShAttr,searchSh+'.inMesh')
			else:
				mc.connectAttr(searchShAttr,searchSh+'.create')
			if len(tempList)>1 and tempList[1]=='local':  searchShAttr=searchSh+'.worldSpace'
			if len(tempList)>1 and tempList[1]=='outMesh':  searchShAttr=searchSh+'.worldMesh'
			
		
		db=mc.createNode('distanceBetween')
				
		cpNode=''
		useCP=False
		
		if cp  or fp or self[cpID]==Decimal('Infinity'):
			
			useCP=True
			
			if cpType=='mesh':
				cpNode=mc.createNode('closestPointOnMesh')
				mc.connectAttr(cpShAttr,cpNode+'.inMesh')
			elif cpType=='nurbsSurface':
				cpNode=mc.createNode('closestPointOnSurface')
				mc.connectAttr(cpShAttr,cpNode+'.inputSurface')
			elif cpType=='nurbsCurve':
				cpNode=mc.createNode('closestPointOnCurve')
				mc.connectAttr(cpShAttr,cpNode+'.inputCurve')
				
			pmm=mc.createNode('pointMatrixMult')
			pmm2=mc.createNode('pointMatrixMult')
			
			mc.connectAttr(cpNode+'.p',pmm+'.ip')
			mc.connectAttr(pmm+'.o',db+'.p1')
			mc.connectAttr(pmm2+'.o',cpNode+'.ip')
			
			if mc.objExists(cpSh):
				mc.connectAttr(cpSh+'.worldInverseMatrix[0]',pmm2+'.inMatrix')
				mc.connectAttr(cpSh+'.worldMatrix[0]',pmm+'.inMatrix')	
				
			if fp: ap=True
		else:
			mc.setAttr(db+'.p1',*self[cpID])
			
		furthestDistance=-1
		closestDistance=Decimal('Infinity')
		
		closest=''
		furthest=''
		distance=0.0
		
		closestUV=(.5,.5)
		furthestUV=(.5,.5)
		
		pp=[]
		
		if searchType=='mesh' or (cp and self.roughCPIDs[searchID][0]<0) or (ap and self.roughAPIDs[searchID][0]<0):

			if searchType=='mesh':
				for point in mc.ls(searchSh+'.vtx[*]',fl=True):
					pp=mc.pointPosition(point,w=True)
					if useCP: mc.setAttr(pmm2+'.ip',*pp)
					mc.setAttr(db+'.p2',*pp)
					distance=mc.getAttr(db+'.d')
					if Decimal(str(distance))<Decimal(str(closestDistance)):
						closestDistance=distance
						closest=point
					if distance>furthestDistance:
						furthestDistance=distance
						furthest=point
						
			if searchType=='nurbsSurface':
				i=0
				for u in searchKnots['u']:
					n=0
					for v in searchKnots['v']:
						point=searchSh+'.uv['+str(u)+']['+str(v)+']'
						pp=mc.pointPosition(point,w=True)
						if useCP: mc.setAttr(pmm2+'.ip',*pp)
						mc.setAttr(db+'.p2',*pp)
						distance=mc.getAttr(db+'.d')
						if Decimal(str(distance))<Decimal(str(closestDistance)):
							closestDistance=distance
							closest=point
							self.roughCPIDs[searchID]=[i,n]
						if distance>furthestDistance:
							furthestDistance=distance
							furthest=point
							self.roughAPIDs[searchID]=[i,n]
						n+=1
					i+=1
				
			if searchType=='nurbsCurve':
				i=0
				for u in searchKnots['u']:
					point=searchSh+'.u['+str(u)+']'
					pp=mc.pointPosition(point,w=True)
					if useCP: mc.setAttr(pmm2+'.ip',*pp)
					mc.setAttr(db+'.p2',*pp)
					distance=mc.getAttr(db+'.d')
					
					if Decimal(str(distance))<Decimal(str(closestDistance)):
						closestDistance=distance
						closest=point
						self.roughCPIDs[searchID]=[i,-1]
						
					if distance>furthestDistance:
						furthestDistance=distance
						furthest=point
						self.roughAPIDs[searchID]=[i,-1]
					i+=1
					
		if searchType=='mesh':
			
			pomi=mc.createNode('pointOnMeshInfo')
			mc.connectAttr(searchSh+'.worldMesh[0]',pomi+'.inMesh')
			
			if cp:
				sampleFaceIDs=PolyFaceList(mc.polyListComponentConversion(closest,fv=True,tf=True),f=True).getIDs()
			if ap:
				sampleFaceIDs=PolyFaceList(mc.polyListComponentConversion(furthest,fv=True,tf=True),f=True).getIDs()
				
			mc.setAttr(pomi+'.r',True)
			mc.setAttr(pomi+'.u',.5)
			mc.setAttr(pomi+'.v',.5)
			
			qDistance=0.0
			qClosestDistance=Decimal('Infinity')
			qClosest=''
			qFurthestDistance=0.0
			qFurthest=''
			qID=-1
			
			for i in sampleFaceIDs:
				
				mc.setAttr(pomi+'.f',i)
				pp=mc.getAttr(pomi+'.p')[0]
				if useCP: mc.setAttr(pmm2+'.ip',*pp)
				mc.setAttr(db+'.p2',*pp)
				qDistance=mc.getAttr(db+'.d')
				
				if cp and Decimal(str(qDistance))<Decimal(str(qClosestDistance)):
					qClosestDistance=qDistance
					qID=i
					
				if ap and qDistance>qFurthestDistance:
					qFurthestDistance=qDistance
					qID=i
					
			mc.setAttr(pomi+'.f',qID)
			
			minU=0.0
			maxU=1.0
			minV=0.0
			maxV=1.0
			
			closestFaceID=-1
			closestFaceU=-1
			closestFaceV=-1
			
			furthestFaceID=-1
			furthestFaceU=-1
			furthestFaceV=-1
			
			closestPP=[]
			furthestPP=[]
			
			closestUV=(-1,-1)
			furthestUV=(-1,-1)
			
			closestFaceDistance=Decimal('Infinity')
			furthestFaceDistance=0.0
			
			x=0
			rangeU=maxU-minU
			rangeV=maxV-minV
				
			while rangeU>self.tol or rangeV>self.tol:
				
				rangeU=maxU-minU
				rangeV=maxV-minV
				
				newBoundsU=\
				[
					[minU,minU+rangeU/3.0],
					[minU+rangeU/3.0,minU+rangeU*2.0/3.0],
					[minU+rangeU*2.0/3.0,maxU]
				]
				newBoundsV=\
				[
					[minV,minV+rangeV/3.0],
					[minV+rangeV/3.0,minV+rangeV*2.0/3.0],
					[minV+rangeV*2.0/3.0,maxV]
				]
				
				qU=[minU+rangeU/6.0,minU+3.0*rangeU/6.0,maxU-rangeU/6.0]
				qV=[minV+rangeV/6.0,minV+3.0*rangeV/6.0,maxV-rangeV/6.0]
				
				qDistance=0.0
				qClosestDistance=Decimal('Infinity')
				qClosest=''
				qFurthestDistance=0.0
				qFurthest=''
				qcpU=-1
				qcpV=-1
				qfpU=-1
				qfpV=-1
				
				for i in range(0,3):
					
					u=qU[i]
					mc.setAttr(pomi+'.u',u)
						
					for n in range(0,3):
						
						v=qV[n]
						mc.setAttr(pomi+'.v',v)
						
						pp=mc.getAttr(pomi+'.p')[0]
						if useCP: mc.setAttr(pmm2+'.ip',*pp)
						mc.setAttr(db+'.p2',*pp)
						qDistance=mc.getAttr(db+'.d')
						
						if pp!=(0.0,0.0,0.0):							
						
							if cp and Decimal(str(qDistance))<Decimal(str(qClosestDistance)):
								qClosestDistance=qDistance
								qClosest=point
								qcpU=u
								qcpV=v
								qUID=i
								qVID=n
								closestPP=pp
								
							if ap and qDistance>qFurthestDistance:
								qFurthestDistance=qDistance
								qFurthest=point
								qfpU=u
								qfpV=v
								qUID=i
								qVID=n
								furthestPP=pp
					
				if cp:
					if Decimal(str(qClosestDistance))<Decimal(str(closestFaceDistance)):	
						closestFaceDistance=qClosestDistance
						closestFaceID=qID
					closestFaceU=qcpU			
					closestFaceV=qcpV
					
				if ap:
					if qFurthestDistance>furthestFaceDistance:
						furthestFaceDistance=qFurthestDistance
						furthestFaceID=qID
					furthestFaceU=qfpU
					furthestFaceV=qfpV
					
				minU,maxU=newBoundsU[qUID]
				minV,maxV=newBoundsV[qVID]
				
			if cp:
				mc.setAttr(pomi+'.f',closestFaceID)
				mc.setAttr(pomi+'.u',closestFaceU)
				mc.setAttr(pomi+'.v',closestFaceV)
				self[searchID]=closestPP
			if ap:
				mc.setAttr(pomi+'.f',furthestFaceID)
				mc.setAttr(pomi+'.u',furthestFaceU)
				mc.setAttr(pomi+'.v',furthestFaceV)
				self.antipodes[searchID]=furthestPP
				
			if cp and Decimal(str(closestFaceDistance))>=Decimal(str(closestDistance)):
				self[searchID]=mc.pointPosition(closest)
				
			if ap and furthestFaceDistance<=furthestDistance:
				self.antipodes[searchID]=mc.pointPosition(furthest)
				
			closestUV=(closestFaceU,closestFaceV)
			furthestUV=(furthestFaceU,furthestFaceV)
				
			mc.delete(pomi)

					
		elif searchType=='nurbsSurface':
			
			if cp: 
				roughUID=self.roughCPIDs[searchID][0]
				roughU=searchKnots['u'][roughUID]
				roughVID=self.roughCPIDs[searchID][1]
				roughV=searchKnots['v'][roughVID]
			elif ap: 
				roughUID=self.roughAPIDs[searchID][0]
				roughU=searchKnots['u'][roughUID]
				roughVID=self.roughAPIDs[searchID][1]
				roughV=searchKnots['v'][roughVID]
				
			if roughUID==0: 
				minU=-(searchKnots['u'][-1]-searchKnots['u'][-2])
			else:
				minU=searchKnots['u'][roughUID-1]
								
			if roughUID==len(searchKnots['u'])-1: 
				maxU=searchKnots['u'][roughUID]+searchKnots['u'][1]
			else:
				maxU=searchKnots['u'][roughUID+1]

			if roughVID==0: 
				minV=-(searchKnots['v'][-1]-searchKnots['v'][-2])
			else:
				minV=searchKnots['v'][roughVID-1]
								
			if roughVID==len(searchKnots['v'])-1: 
				maxV=searchKnots['v'][roughVID]+searchKnots['v'][1]
			else:
				maxV=searchKnots['v'][roughVID+1]
			
			rangeU=float(maxU)-float(minU)
			rangeV=float(maxV)-float(minV)
			
			while rangeU>self.tol or rangeV>self.tol:
				
				rangeU=float(maxU)-float(minU)
				rangeV=float(maxV)-float(minV)
				
				newBoundsU=\
				[
					[minU,minU+rangeU/3.0],
					[minU+rangeU/3.0,minU+rangeU*2.0/3.0],
					[minU+rangeU*2.0/3.0,maxU]
				]
				newBoundsV=\
				[
					[minV,minV+rangeV/3.0],
					[minV+rangeV/3.0,minV+rangeV*2.0/3.0],
					[minV+rangeV*2.0/3.0,maxV]
				]
				
				qU=[minU+rangeU/6.0,minU+3.0*rangeU/6.0,maxU-rangeU/6.0]
				qV=[minV+rangeV/6.0,minV+3.0*rangeV/6.0,maxV-rangeV/6.0]
				
				qClosestUV=(.5,.5)
				qFurthestUV=(.5,.5)
				qDistance=0.0
				qClosestDistance=Decimal('Infinity')
				qClosest=''
				qFurthestDistance=0.0
				qFurthest=''
				qUID=-1
				qVID=-1
				
				for i in range(0,3):
					
					#make sure the point is within range
					if qU[i]<0:
						u=searchKnots['u'][-1]+qU[i]
					elif qU[i]>searchKnots['u'][-1]:
						u=searchKnots['u'][0]+(qU[i]-searchKnots['u'][-1])
					else:
						u=qU[i]
												
					for n in range(0,3):
						#make sure the point is within range
						if qV[n]<0:
							v=searchKnots['v'][-1]+qV[n]
						elif qV[n]>searchKnots['v'][-1]:
							v=searchKnots['v'][0]+(qV[n]-searchKnots['v'][-1])
						else:
							v=qV[n]
													
						point=searchSh+'.uv['+str(u)+']['+str(v)+']'
						pp=mc.pointPosition(point,w=True)
						if useCP: mc.setAttr(pmm2+'.ip',*pp)
						mc.setAttr(db+'.p2',*pp)
						qDistance=mc.getAttr(db+'.d')
						
						if cp and Decimal(str(qDistance))<Decimal(str(qClosestDistance)):
							qClosestDistance=qDistance
							qClosest=point
							qClosestUV=(u,v)
							qUID=i
							qVID=n
							
						if ap and qDistance>qFurthestDistance:
							qFurthestDistance=qDistance
							qFurthest=point
							qFurthestUV=(u,v)
							qUID=i
							qVID=n
					
				if cp: 
					closestDistance=qClosestDistance
					closest=qClosest
					closestUV=qClosestUV
					
				if ap:
					furthestDistance=qFurthestDistance
					furthest=qFurthest
					furthestUV=qFurthestUV
					
				minU,maxU=newBoundsU[qUID]
				minV,maxV=newBoundsV[qVID]
				
		elif searchType=='nurbsCurve':
			
			if cp: roughID=self.roughCPIDs[searchID][0]
			elif ap: roughID=self.roughAPIDs[searchID][0]

			if roughID==0: 
				min=-(searchKnots['u'][-1]-searchKnots['u'][-2])
			else:
				min=searchKnots['u'][roughID-1]
								
			if roughID==len(searchKnots)-1: 
				max=searchKnots['u'][roughID]+searchKnots['u'][1]
			else:
				max=searchKnots['u'][roughID+1]
				
			rangeU=max-min
			
			while rangeU>self.tol:
				
				rangeU=max-min
				
				newBounds=\
				[
					[min,min+rangeU/3],
					[min+rangeU/3.0,min+rangeU*2/3],
					[min+rangeU*2/3,max]
				]
				
				qU=[min+rangeU/6,min+3*rangeU/6,max-rangeU/6]
				
				qDistance=0
				qClosestDistance=Decimal('Infinity')
				qClosest=''
				qFurthestDistance=0
				qFurthest=''
				qID=-1
				qClosestUV=(.5,-1)
				qFurthestUV=(.5,-1)
				
				for i in range(0,3):
					
					#make sure the point is within range
					if qU[i]<0:
						u=searchKnots['u'][-1]+qU[i]
					elif qU[i]>searchKnots['u'][-1]:
						u=searchKnots['u'][0]+(qU[i]-searchKnots['u'][-1])
					else:
						u=qU[i]
						
					point=searchSh+'.u['+str(u)+']'
					pp=mc.pointPosition(point,w=True)
					if useCP: mc.setAttr(pmm2+'.ip',*pp)
					mc.setAttr(db+'.p2',*pp)
					qDistance=mc.getAttr(db+'.d')
					
					if cp and Decimal(str(qDistance))<Decimal(str(qClosestDistance)):
						qClosestDistance=qDistance
						qClosestUV=(u,-1)
						qClosest=point
						qID=i
						
					if ap and qDistance>qFurthestDistance:
						qFurthestDistance=qDistance
						qFurthestUV=(u,-1)
						qFurthest=point
						qID=i
					
				if cp and Decimal(str(qClosestDistance))<Decimal(str(closestDistance)):
					closestDistance=qClosestDistance
					closest=qClosest
					closestUV=qClosestUV
					
				if ap and qFurthestDistance>furthestDistance:
					furthestDistance=qFurthestDistance
					furthest=qFurthest
					furthestUV=qFurthestUV
					
				min,max=newBounds[qID]
			
		if cp: 
			if searchType!='mesh' and self[searchID][0]==Decimal('Infinity'):
				self[searchID]=tuple(mc.pointPosition(closest,w=True))
				
			if self.uvs[searchID][0]<0:
				self.uvs[searchID]=closestUV
				
			if searchType=='mesh':
				if self.closestFaceIDs[searchID]<0:
					self.closestFaceIDs[searchID]=closestFaceID
				if self.closestVertexIDs[searchID]<0:
					self.closestVertexIDs[searchID]=getIDs(furthest)

			if useCP:
				mc.setAttr(pmm2+'.ip',*self[searchID])
				self[cpID]=mc.getAttr(pmm+'.o')[0]
				self.uvs[cpID]=(mc.getAttr(cpNode+'.u'),mc.getAttr(cpNode+'.v'))
				if cpType=='mesh': 
					self.closestFaceIDs[cpID]=mc.getAttr(cpNode+'.f')
					if mc.objExists(cpNode+'.vt'): self.closestVertexIDs[cpID]=mc.getAttr(cpNode+'.vt')
		else:
			if searchType=='mesh':
				if self.antipodeFaceIDs[searchID]<0:
					self.antipodeFaceIDs[searchID]=furthestFaceID
				if self.antipodeVertexIDs[searchID]<0:
					self.antipodeVertexIDs[searchID]=getIDs(furthest)
			elif searchType!='mesh':
				self.antipodes[searchID]=tuple(mc.pointPosition(furthest,w=True))
				
			if self.antipodeUVs[searchID][0]<0:
				self.antipodeUVs[searchID]=furthestUV
					
		if useCP: 
			mc.delete(cpNode)			
			
		if searchTr!=self.trs[searchID]:
			mc.delete(searchTr)
		
		if mc.objExists(db):
			mc.delete(db)
		
		return self

		
	def getAntipodes(self,*arg):
		
		returnVal=[]
		
		if len(arg)==0: 
			arg=[0,1]
		if len(arg)==1:
			if self.antipodes[arg[0]][0]==Decimal('-Infinity'):
				self.lookup(arg[0],cp=False,ap=True)
			return self.antipodes[arg[0]]		
		elif  len(arg)>1:
			for a in arg:
				returnVal.append(self.getAntipodes(a))
				
		return returnVal
		
	def getFurthestPoints(self,*arg):
		
		returnVal=[]
		
		if len(arg)==0: 
			arg=[0,1]
		if len(arg)==1:
			if self.antipodes[arg[0]][0]==Decimal('-Infinity'):
				self.lookup(arg[0],cp=False,ap=False,fp=True)
			return self.antipodes[arg[0]]	
		elif  len(arg)>1:
			for a in arg:
				returnVal.append(self.getFurthestPoints(a))
				
		return returnVal
