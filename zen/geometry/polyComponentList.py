import maya.cmds as mc
import maya.mel as mel
from array import array
from re import search
from sets import Set
from zen.isIterable import isIterable
from zen.removeAll import removeAll
from zen.iterable import iterable
from zen.getIDs import getIDs
from zen.getReversed import getReversed
from zen.iterable import iterable
	
class PolyComponentList(list):
	
	"""Perform sorting operations on a list of polygon components."""

	def __init__(self,*args,**keywords):
		
		self.create(*args,**keywords)
		
	def create(self,*args,**keywords):
				
		self.type=''
		self.shape=''
		self.obj=''
		self.tr=''
		self.edges=[]
		self.faces=[]
		self.vertices=[]
		self.uvs=[]
		self.etcObj=[]
		self.etc=[]
		self.ordered=False
		flatten=False
		
		if len(args)==0: args=mc.ls(sl=True)

		for a in args: self.extend(iterable(mc.ls(a))) #make sure we are using the name maya will use

		for s in self:
			if len(s.split('.'))<=1 or len(s.split('['))<=1:#it's an object, stash it in etcObj
				self.etcObj.append(s)
		
		self[:]=removeAll(self.etcObj,self)
				
		for k in keywords:
			if k=='f' or k=='flatten' and keywords[k]:
				flatten=True
			elif k in self.__dict__:
				if type(eval('self.'+k)).__name__==type(keywords[k]).__name__:
					exec('self.'+k+'=keywords[k]')
					
		self.shape=self.getShape()
		self.obj=self.getObj()
		self.tr=self.getTr()
		
		if self.type=='e' or self.type=='edges':
			self.etc.extend(removeAll(self.getEdges(),self))
			self[:]=self.edges
		elif self.type=='v' or self.type=='vertices':
			self.etc.extend(removeAll(self.getVertices(),self))
			self[:]=self.vertices
		elif self.type=='f' or self.type=='faces':
			self.etc.extend(removeAll(self.getFaces(),self))
			self[:]=self.faces
		elif self.type=='uv' or self.type=='uvs':
			self.etc.extend(removeAll(self.getUVs(),self))
			self[:]=self.uvs
			
		if flatten: self.flatten()
		
	def getObjVertCount(self):
		if len(self)>0:
			if 'objVertCount' not in self.__dict__ or self.objVertCount==-1:
				self.objVertCount = mc.polyEvaluate( self.obj, v=True )
			return self.objVertCount
		else: 
			return
		
	def getObjFaceCount( self ):
		if ( len(self)>0 ):
			if 'objFaceCount' not in self.__dict__ or self.objFaceCount==-1:
				self.objFaceCount = mc.polyEvaluate( self.obj, f=True )	
			return self.objFaceCount
		else: return
							
	def getObjEdgeCount( self ):
		if (len(self)>0):
			if('objEdgeCount' not in self.__dict__) or self.objEdgeCount==-1:
				self.objEdgeCount = mc.polyEvaluate( self.obj, e=True )
			return self.objEdgeCount
		else: 
			return
		
	def getShape(self):
		"Returns the shape on which the components reside."
		if len(self)>0:
			if 'shape' not in self.__dict__ or len(self.shape)==0:
				self.shape = mc.ls(self,o=True)[0]	
			return self.shape
		else: 
			return
			
	def getTr(self):
		if len(self)>0:
			if 'tr' not in self.__dict__ or len(self.tr)==0:
				self.tr=mc.listRelatives(self.getShape(),p=True)[0]
			return self.tr
				
	def getObj(self):
		"""
		Returns a unique indentifier for the object on which the components reside.
		If the components reside on a shape which shares a transform with other shapes,
		the returned name is that of the shape node, otherwise the returned 
		name is that of the transform node.
		"""
		if len(self)>0:
			if 'obj' not in self.__dict__ or len(self.obj)==0:
				n = self[0].split('.')
				n.pop(len(n)-1)
				self.obj=''.join(n[:])	
			return self.obj
		else: 
			return

	def getFlattened(self):
		"Returns the list of components flattened."
		if len(self)>0:
			if 'flattened' not in self.__dict__ or len(self.flattened)<len(self):
				self.flattened=PolyComponentList(mc.ls(self,fl=True))
			return self.flattened
		else:
			return self
		
	def getIDs(self):
		"Returns component id's for the component list."
		if 'ids' not in self.__dict__ or len(self.getFlattened())!=len(iterable(self.ids)):
			self.ids=iterable(getIDs(self.getFlattened()))
		return self.ids
		
	def flatten(self):
		self[:]=self.getFlattened()[:]
	
	def getEdges(self):
		if len(self)>0:
			if 'edges' not in self.__dict__ or len(self.edges)==0:
				self.edges=PolyComponentList(mc.polyListComponentConversion(self[:],fe=True,te=True))
			return self.edges
		else:
			return
			
	def getVertices(self):
		if len(self)>0:
			if 'vertices' not in self.__dict__ or len(self.vertices)==0:
				self.vertices=PolyComponentList(mc.polyListComponentConversion(self[:],fv=True,tv=True))
			return self.vertices
		else:
			return
			
	def getFaces(self):
		if len(self)>0:
			if 'faces' not in self.__dict__ or len(self.faces)==0:
				self.faces=PolyComponentList(mc.polyListComponentConversion(self[:],ff=True,tf=True))
			return self.faces
		else:
			return
			
	def getUVs(self):
		if len(self)>0:
			if 'uvs' not in self.__dict__ or len(self.uvs)==0:
				self.uvs=PolyComponentList(mc.polyListComponentConversion(self[:],fuv=True,tuv=True))
			return self.uvs
		else:
			return