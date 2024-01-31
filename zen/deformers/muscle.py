import maya.cmds as mc
import maya.mel as mel
from types import *
from platform import python_version
from zen.melEncode import melEncode
from zen.melGlobalVar import MelGlobalVar
from zen.isIterable import isIterable

class Muscle:
	
	""""Create and modify muscles."""

	def __init__(self,*args,**keywords):
		
		#set defaults
		name=''
		self.spanGroups={}
		attributes={}
		self.axis=0
		self.jiggle=0
		self.script=0
		self.cMuscleShape=''
		self.Muscle=''
		self.muscleShape=''
		self.Handle=''
		self.allCurves=[]
		self.selectionGroups=[]
		pcw={}
		self.resMult=1.5
		self.spans=12
		
		for k in keywords:
			
			if(isinstance(keywords[k],list) and (k=='pcw' or k=='parentConstraintWeights')):#interpret parent constraint weights
				pcw=keywords[k]
			if(isinstance(keywords[k],bool)):#convert booleans to integers
				exec('self.'+k+'='+str(int(keywords[k])))
			elif(k=='axis'):#convert axis input to integer
				if(isinstance(keywords[k],str)):
					if(keywords[k].lower()=='x'):
						self.axis=1
					if(keywords[k].lower()=='y'):
						self.axis=2
					if(keywords[k].lower()=='z'):
						self.axis=3
				elif(isinstance(keywords[k],int)):
					self.axis=keywords[k]
			elif(k=='name'):
				name=keywords[k]
			elif(k in self.__dict__):
				exec('self.'+k+'=keywords[k]')
			else:
				attributes[k]=keywords[k]
		
		if len(args)==0 and len(self.Handle)==0 and len(self.Muscle)==0 and len(self.muscleShape)==0: args=mc.ls(sl=True)
		
		for arg in args:
			if(isinstance(arg,list)):
				aList=arg
			else:
				aList=[arg]
			sList=aList
			for a in aList:	
				if(mc.objExists(a) and mc.ls(a,o=True)[0]==mc.ls(a)[0]):
					if(mc.objExists(a+'.zmi')):
						self.Handle=a
						sList.remove(a)
					else:
						if(mc.nodeType(a)=='nurbsSurface'):
							aShape=a
						else:
							try: aShape=mc.listRelatives(c=True,s=True,ni=True,type='nurbsSurface')[0]
							except: aShape=''

						if(mc.objExists(aShape)):
							messageConnections=mc.listConnections(aShape+'.message',p=True,d=True,s=False)	
							if(isinstance(messageConnections,list) and len(messageConnections)>0):
								for c in mc.listConnections(a+'.message',p=True,d=True):
									if(c.split('.')[1]=='zenMuscle'):
										self.Handle=c.split('.')[0]
										sList.remove(a)
			if isIterable(sList) and len(sList)>0: self.selectionGroups.append(sList)
			
		if(len(self.Muscle)>0 and len(self.muscleShape)==0):
			try: 
				self.muscleShape=mc.listRelatives(self.Muscle,s=True,ni=True,type='nurbsSurface')[0]
			except:
				pass
			
		if(len(self.muscleShape)>0 and len(self.Handle)==0):
			for c in listConnections(self.muscleShape+'.message',p=True,d=True,s=False):
				if(c.split('.')[1]=='zenMuscle'):
					self.Handle=c.split('.')[0]
					break
					
		if(len(self.Handle)>0 and len(self.Muscle)==0 and mc.objExists(self.Handle+'.zenMuscle')): #if we know the Handle already, get the Muscle
			try:	self.Muscle=mc.listConnections(self.Handle+'.zenMuscle')[0]
			except:	pass
			
		if(len(self.Handle)>0 and len(self.muscleShape)==0 and mc.objExists(self.Handle+'.zenMuscle')):#get the Muscle shape
			try:	self.muscleShape=mc.listConnections(self.Handle+'.zenMuscle',sh=True)[0]
			except:	pass
			try:	self.handleGroup=mc.listConnections(self.Handle+'.zenMuscleCtrlGroup')[0]
			except: pass
			
		if(len(self.Handle)>0 and self.axis>=0):#see if there is an opposite
			if(isinstance(mc.listConnections(self.Handle+'.zenOpposite'),list)):
				opp=mc.listConnections(self.Handle+'.zenOpposite')[0]
				if(mc.objExists(opp)):
					self.opposite=Muscle(Handle=opp,axis=-1)
					
		if len(self.muscleShape):
			self.spans=mc.getAttr(self.muscleShape+'.spansU')
			
		if( len(self.selectionGroups)>0 ):
				
			if(len(self.Muscle)==0 and len(self.Handle)==0):
				self.create()
				
		self.getInfluences()
		
		if( len(self.selectionGroups)>0 ):
			
			if(len(name)>0):                                     
				if(isinstance(name,str)):
					self.rename(name)
				elif(isinstance(name,list)):
					self.rename(name[0])
					if "opposite" in self.__dict__:
						self.opposite.rename(name[1])
						
			self.setAttributes(**attributes)
			self.setParentConstraintWeights(*pcw)
			
	def setParentConstraintWeights(self,*args):
		if(len(args)>0):
			self.getInfluences()
			length=len(self.allCurves)
			if(len(args)<length): 
				length=len(args)
			for i in range(0,length):
				pc=mc.parentConstraint(self.allCurves[i],q=True)
				if(isinstance(args[i],dict) and isinstance(pc,str)):
					parents=mc.parentConstraint(pc,tl=True,q=True)
					pcs=args[i]
					pcSet=[]
					for n in range(0,len(parents)):
						if(parents[n] in pcs):
							pcSet.append(pcs[parents[n]])
						else:
							pcSet.append(0)#default to 0
					for n in range(0,len(pcSet)):
						mc.parentConstraint(parents[n],pc,w=pcSet[n])
		
	def getInfluences(self):
		#get influence objects
		self.influences=list()
		self.allCurves=list()
		
		if(not mc.objExists(self.Handle+'.zmi[0].zmim')): return
			
		for i in range(0,len(mc.ls(self.Handle+'.zmi[*]'))):
			self.influences.append(dict())
			self.influences[i]['mesh']=str(mc.listConnections(self.Handle+'.zmi['+str(i)+'].zmim',sh=True)[0])
			self.influences[i]['curves']=list()
			self.influences[i]['edges']=list()
			self.influences[i]['parents']=list()
			for c in mc.ls(self.Handle+'.zmi['+str(i)+'].zmics[*]'):
				if( isinstance(mc.listConnections(c+'.zmic'),list) and len(mc.listConnections(c+'.zmic'))>0):
					curve=mc.listConnections(c+'.zmic')[0]
					self.influences[i]['curves'].append(curve)
					self.allCurves.append(curve)
					edgeList=[]
					index=c.split('[')[(len(c.split('['))-1)].split(']')[0]
					edgeIndices=mc.getAttr(c+'.zmie')[0]
					if( len(self.influences[i]['mesh'])>0 ):
						for e in edgeIndices:
							edgeList.append(self.influences[i]['mesh']+'.e['+str(int(e))+']')
					self.influences[i]['edges'].append(edgeList)
					parentDictionary={}
					pc=mc.parentConstraint(curve,q=True)
					if(isinstance(pc,str)):
						parents=mc.parentConstraint(pc,q=True,tl=True)
						parentWeights=mc.parentConstraint(parents,pc,w=True,q=True)
						if not isIterable(parents): parents=[parents]
						if not isIterable(parentWeights): parentWeights=[parentWeights]
						for ppc in range(0,len(parents)):
							pcName=parents[ppc]
							pcWeight=parentWeights[ppc]
							if isinstance(pcName,str) and len(pcName) and isinstance(pcWeight,(float,int)):
								parentDictionary[pcName]=pcWeight
					else:
						parents=mc.listRelatives(curve,p=True)
						if(isinstance(parents,list) and len(parents)>0):
							parentDictionary[parents[0]]=1
							
					self.influences[i]['parents'].append(parentDictionary)
					    
	def create(self,): # creates the Muscle, executed on class instantiation if all necessary arguments are supplied
		
		command='rigZenMuscle\n(\n'
		command+='	'+melEncode(self.selectionGroups)+',\n'
		command+='	'+str(self.axis)+','+str(self.jiggle)+','+str(self.spans)+'\n)'

		results=mel.eval(command)
		
		if(self.axis>0):
			self.Handle=results[0]
			self.Muscle=results[2]
			curveCount=(( len(results)-4)/2)-1
			self.curves=results[4:len(results)-curveCount]
			self.opposite=Muscle\
			(
				axis=0,
				jiggle=self.jiggle,
				script=self.script,
				Handle=results[1],
				Muscle=results[3],
				curves=results[len(results)-curveCount:]
			)
			try:	self.opposite.handleGroup=mc.listConnections(self.opposite.Handle+'.zenMuscleCtrlGroup')[0]
			except: pass
		else:
			self.Handle=results[0]
			self.Muscle=results[1]
			self.curves=results[2:]

		try:	self.handleGroup=mc.listConnections(self.Handle+'.zenMuscleCtrlGroup')[0]
		except: pass
		
		self.cMuscleShape=mc.listRelatives(self.Muscle,c=True,type='cMuscleObject')[0]
		self.muscleShape=mc.listRelatives(self.Muscle,s=True,ni=True,type='nurbsSurface')[0]
		
		if(self.axis>0):
			self.opposite.cMuscleShape=mc.listRelatives(self.opposite.Muscle,c=True,type='cMuscleObject')[0]
			self.opposite.muscleShape=mc.listRelatives(self.opposite.Muscle,s=True,ni=True,type='nurbsSurface')[0]
			
	def rename(self,newName): # renames the Muscle and it's components
	
		self.Handle=mc.rename(self.Handle,newName+"_handle")
		self.Muscle=mc.rename(self.Muscle,newName)
		self.handleGroup=mc.rename(self.handleGroup,newName+"_handleGroup")
		
		for i in range(0,len(self.allCurves)):
			self.allCurves[i]=mc.rename(self.allCurves[i],(newName+"_curve"+str(i)))
			
	def setAttributes(self,*args,**keywords):
		
		if(len(keywords)>0):
			
			for k in keywords:
				if( mc.objExists(self.Handle+"."+k) == True ):
					try:
						mc.setAttr(self.Handle+"."+k,keywords[k])
					except:
						pass
					
		if(len(args)>0):
			
			for a in args:
				if(isinstance(args,dict) and mc.objExists(self.Handle+"."+a)):
					mc.setAttr(self.Handle+"."+a,args[a])
				elif(isinstance(a,list) and mc.objExists(self.Handle+"."+a[0]) and len(a)>1):
					mc.setAttr(self.Handle+"."+a[0],a[1])
					
	def goToPose(self,*args,**keywords):
		
		if not 'bp' in keywords:
			bp=False
		
		success=False
		err=False
		
		mel.eval("DisableAll")
				
		if(len(args)>0):
			for pose in args:
				if(mc.nodeType(pose)=='dagPose'):
					for i in range(0,10): #( glitch workaround )
						err=False
						try:
							mc.dagPose(pose,r=True)
							err=False
						except:
							err=True
		else:
			if(bp==True or len(keywords)>0):
				for i in range(0,10): #( glitch workaround )
					err=False
					try:
						mc.dagPose(self.root,r=True,bp=True)
						err=False
					except:
						err=True
			if(len(keywords)>0):
				for j in keywords:
					if(mc.objExists(j)):
						for i in range(0,10):
							try:
								mc.setAttr(j,keywords[j])
								err=False
							except:
								err=True
					else:
						err=True
				
		mel.eval("EnableAll")
		
		if(err==False): success=True
		
		return success
			
	def addAutoFlex(self,mirror=True,pose={},**keywords):
		"Adds an auto-flex pose from the current pose or a dictionary of attribute/value pairs."
				
		self.bindPose= mc.dagPose(self.Muscle,q=True,bp=True)[0]
		self.root=mc.dagPose(self.bindPose, q=True, m=True )[0]
		startPose=mc.dagPose(self.root,s=True)#store current pose
		
		plug=mel.eval('zenFirstOpenPlug("'+self.Handle+'.zenAutoFlex")')
		verified=False
		attributes={}
		poses=[]
		success=True
				
		offBindPoseJointCount=0
		dp=mc.dagPose(self.bindPose,q=True,ap=True)
		if isIterable(dp):
			offBindPoseJointCount=len(dp)
		
		if(offBindPoseJointCount>0 and len(pose)==0): #create an auto-flex pose from the current position
			command='rigZenMuscleAddAutoFlex("'+self.Handle+'",'+str(int(mirror))+')'
			plug=mel.eval(command)
		elif(len(pose)>0):
			success=self.goToPose(**pose)
			if(success):
				try:
					plug=mel.eval('rigZenMuscleAddAutoFlex("'+self.Handle+'",'+str(int(mirror)*self.getAxis())+')')
				except:
					success=False#raise Warning('Could not add auto flex pose for '+self.Muscle)
			
		if success:
			for k in keywords:
				attr='zenAutoFlex['+str(plug)+'].'+str(k)
				conn=mc.listConnections((self.Handle+'.'+attr),s=True,d=False,p=True)
				if isIterable(conn) and len(conn)>0 and mc.ls(conn[0],o=True)[0]==mc.ls((self.Handle+'.'+attr),o=True)[0]:
					attr=conn[0].split('.')[-1]
				attributes[str(attr)]=keywords[k]
			self.setAttributes(**attributes)
			success=self.goToPose(startPose)		
		else:
			self.goToPose(startPose)

		mc.delete(startPose)
		
		return success
	
	def getAxis(self):
		if self.axis!=0:
			return self.axis
		if "opposite" in self.__dict__:
		
			if 'bindPose' not in self.__dict__:
				self.bindPose= mc.dagPose(self.Muscle,q=True,bp=True)[0]
			if 'root' not in self.__dict__:
				self.root=mc.dagPose( self.bindPose, q=True, m=True )[0]
			
			offset=mc.xform(self.root,q=True,rp=True,ws=True)
			
			center=mc.objectCenter(self.muscleShape)
			opposite=mc.objectCenter(self.opposite.muscleShape)
			
			greatestDistance=-1
			axisID=-1
			
			for i in range(0,3):
				distance=abs((center[i]-offset[i])-(opposite[i]-offset[i]))
				if(distance>greatestDistance):
					   greatestDistance=distance
					   axisID=i
					   
			self.axis=axisID+1
			
			return self.axis
		else:
			return 0
		
	def generateScript(self):
		
		returnVal=self.Muscle+'=zen.Muscle\\\n'
		returnVal+='(\n'
			
		connections=mc.listConnections(self.Handle+'.zmi',type='transform')
		
		if isIterable(connections) and len(connections)>0:#if this is a mirrored Handle use the original
			if(len(connections)==1):
				if(mc.objExists(connections[0]+'.zmi')):
					opposite=Muscle(Handle=connections[0])
					return(opposite.generateScript())
					
		self.getInfluences()
		
		selectionGroups=[]
		parentConstraintWeights=[]
		
		n=0
		
		for i in range(0,len(self.influences)):#get the span components
			
			selectionGroups.append([])
			#parentConstraintWeights.append({})
			
			mesh=str(self.influences[i]['mesh'])
			curves=self.influences[i]['curves']
			edges=self.influences[i]['edges']
			parents=self.influences[i]['parents']
			
			if(len(parents)):
				for p in parents:
					for pc in p:
						if pc not in selectionGroups[i]: selectionGroups[i].append(pc)
						#parentConstraintWeights[i][pc]=p[pc]
					parentConstraintWeights.append(p)
			if(len(edges)):
				for e in edges:
					for ee in e:
						selectionGroups[i].append(ee)
			else:
				for c in curves:
					selectionGroups[i].append(c)
	
		for i in range(0,len(selectionGroups)):#span selection groups
			returnVal+='	['
			for n in range(0,len(selectionGroups[i])):
				returnVal+='"'+selectionGroups[i][n]+'"'
				if(n==len(selectionGroups[i])-1):
					returnVal+='],\n'
				else:
					returnVal+=','
		
		#set the parent constraint weights
		returnVal+='	pcw=['
		
		dStrings=[]
		for i in range(0,len(parentConstraintWeights)):
			returnVal+='{'
			
			diStrings=[]
			for x in parentConstraintWeights[i]:
				diStrings.append('"'+x+'":'+str(parentConstraintWeights[i][x]))
			
			returnVal+=','.join(diStrings)
			if(i<len(parentConstraintWeights)-1):
				returnVal+='},'
			else:
				returnVal+='}]'
		
		attrList=[]
		delList=[]
		attrList.extend(mc.listAttr(self.Handle,k=True))
		attrList.extend(mc.listAttr(self.Handle,cb=True))
			
		for i in range(0,len(attrList)):
			if mc.objExists(self.Handle+'.'+attrList[i]) and mc.getAttr(self.Handle+'.'+attrList[i],type=True)!='message':
				c=mc.listConnections(self.Handle+'.'+attrList[i],s=True,d=False)
				if isIterable(c) and len(c)>0:
					delList.append(attrList[i])
			else:
				delList.append(attrList[i])
		
		delList.extend(['visibility','translateX','translateY','translateZ','rotateX','rotateY','rotateZ','scaleX','scaleY','scaleZ'])
		for d in delList:
			attrList.remove(d)
				
		tempList=attrList
		attrList=[]
		
		for a in tempList:
			if(len(a.split('.'))==1 and mc.getAttr(self.Handle+'.'+a,type=True)!='message'):
				attrList.append(a)
		
		if(len(attrList)>0):
			returnVal+=',\n	'
			for i in range(0,len(attrList)):
				returnVal+=attrList[i]+'='+str(mc.getAttr(self.Handle+'.'+attrList[i]))
				if(i<len(attrList)-1):
					returnVal+=','
					
		returnVal+=',\n'
		
		#get the name
		if "opposite" in self.__dict__:
			returnVal+='	name=["'+self.Muscle+'","'+self.opposite.Muscle+'"],\n'
		else:
			returnVal+='	name="'+self.Muscle+'",\n'
			
		returnVal+='	axis='+str(self.getAxis())+','
		
		returnVal+='spans='+str(self.spans)+','
			
		if(mc.objExists(self.Handle+'.jiggle')):
			returnVal+='jiggle=True\n'
		else:
			returnVal+='jiggle=False\n'
			
		returnVal+=')\n'
		
		#auto-flex
		
		autoFlexPlugs=mc.ls(self.Handle+'.zaf[*]')
		
		if(isinstance(autoFlexPlugs,list) and len(autoFlexPlugs)>0):
		
			for p in autoFlexPlugs:
				
				infAttrs=mc.listConnections(p+'.zenPoseAttr',p=True,s=True,d=False)
				infAttrValues=[]

				if isIterable(infAttrs):
					for i in range(0,len(infAttrs)):
						attributeValue=mc.getAttr(p+'.zenAttrVal['+str(i)+']')
						if(isinstance(attributeValue,(float,int))):
							infAttrValues.append(attributeValue)
						elif(isIterable(attributeValue)):
							infAttrValues.append(attributeValue[0])

				counter=0
				
				if(isinstance(infAttrs,list) and isinstance(infAttrValues,list)):
					
					length=len(infAttrs)
					if(len(infAttrValues)<length): length=len(infAttrValues)
					if(length>0):
						if(counter==0):
							returnVal+=self.Muscle+'.addAutoFlex\\\n(\n'
							if "opposite" in self.__dict__:
								returnVal+='	mirror=True,\n'
							returnVal+='	pose={'
						for i in range(0,length):
							returnVal+='"'+infAttrs[i]+'":'+str(infAttrValues[i])
							if(i<length-1):
								returnVal+=','
							else:
								returnVal+='},\n	'
								
					attrList=mc.listAttr(p,leaf=True)
					if(isinstance(attrList,list) and len(attrList)>0):
						ii=0
						for i in range(0,len(attrList)):
							if mc.objExists(p+'.'+attrList[i]):
								c=mc.listConnections(p+'.'+attrList[i],s=True,d=False)
								if\
								(
									mc.getAttr(p+'.'+attrList[i],type=True)=='double' and 
									(
										not(isIterable(c)) or 
										len(c)==0 or
										mc.ls(c,o=True)[0]==mc.ls(p,o=True)[0]
									)
								):
									if(ii>0): returnVal+=','
									returnVal+=attrList[i]+'='+str(mc.getAttr(p+'.'+attrList[i]))
									ii+=1
								
					counter+=1
					
				if(counter>0):
					returnVal+='\n)\n'
			
		return returnVal

def rename(name):
	Muscle(mc.ls(sl=True)).rename(name)

def autoFlex():
	m=Muscle(mc.ls(sl=True))
	m.addAutoFlex()

def generateScript():
	sel=mc.ls("*.zenMuscleInputs",o=True,sl=True)
	if not isIterable(sel) or len(sel)==0:
		sel=mc.ls("*.zenMuscleInputs",o=True)
		if not isIterable(sel):
			raise('You must select one or more muscles or Muscle Handle from which to generate creation scripts.')
	returnVal=''
	completed=[]
	for m in sel:
		myMuscle=Muscle(m)
		if myMuscle.Muscle not in completed:
			returnVal+=myMuscle.generateScript()
			completed.append(myMuscle.Muscle)
			if('opposite' in myMuscle.__dict__): 
				completed.append(myMuscle.opposite.Muscle)
	if len(returnVal)>0:
		returnVal='import maya.mel as mel\nmel.eval("source zenTools")\nimport zen\n'+returnVal
		mel.eval('zenDisplayText("Muscle Script","'+mc.encodeString(returnVal)+'")')
	return returnVal