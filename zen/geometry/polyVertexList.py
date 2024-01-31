import maya.cmds as mc
import maya.mel as mel
from copy import copy
from array import array
from re import search
from sets import Set
from zen.isIterable import isIterable
from zen.removeAll import removeAll
from zen.iterable import iterable
from zen.getReversed import getReversed
from zen.geometry.polyComponentList import PolyComponentList
		
class PolyVertexList(PolyComponentList):
	
	def __init__( self, *args, **keywords ):
		keywords['type']='v'
		self.create(*args, **keywords)

	def shortestPath(self):
		
		"Returns a list of adjacent vertices defining the shortest path from vertA to vertB."

		vertA=str(self[0])
		vertB=str(self[1])
		
		del self[2:]# make sure there are only two vertices in the list
		
		vertPath=list([vertA])
		vert=str(vertA)
		distanceList=self.distanceList(vertB,vertA)
		sizeList=len(distanceList)
			
		for i in range(1,sizeList):
		
			tempList=distanceList[ sizeList-i-1 ]
			tempList=mc.ls( tempList, fl=True )
			vertices=mc.polyListComponentConversion( vert, te=True )
			vertices=mc.polyListComponentConversion( vertices, tv=True )
			vertices=mc.ls( vertices, fl=True )
			tempA=list([vert])
			vertices=removeAll(tempA,vertices)

			intersectorSet=Set(vertices)
			intersectorSet.intersection_update(tempList)
			vertTempArray=list(intersectorSet)
			
			vert=str(vertTempArray[0])
			vertPath.append( vert )
	
		vertPath.append( vertB )

		return	vertPath
		
	def distanceList(self,vert,stopVert):
		
		"""
		Used by shortestPathBetween2Verts.
		returnVal[i] contains a list of vertices which are i edges distant from vert.
		returnVal will be generated until returnVal[len(returnVal)-1] contains stopVert.
		"""
	
		vertices=[vert]
		estimate=25
		returnVal=[]
			
		mc.progressWindow(ii=1,title="Working",status="Sorting",max=estimate,progress=0)
	
		for i in range(0,self.getObjVertCount()):
			
			tempArray = mc.ls(vertices,fl=True)
			vertices = mc.polyListComponentConversion(vertices,te=True)
			vertices = mc.polyListComponentConversion(vertices,tv=True)
			flattenedListVerts=mc.ls(vertices, fl=True)
			tempArray=removeAll(tempArray,flattenedListVerts)
			tempArray=mc.polyListComponentConversion(tempArray,fv=True,tv=True)
			returnVal.append(tempArray)
			
			if(stopVert in flattenedListVerts): break
			
			mc.progressWindow(e=True,s=1)
			
			if( mc.progressWindow(q=True,ic=True)):
				
				mc.progressWindow(ep=True)
				mc.error("User Interupt.")
			
			if( mc.progressWindow(q=True, progress=True)>=mc.progressWindow(q=True, max=True)):  
	
				mc.progressWindow(ep=True)
				mc.progressWindow(progress=0)
		
		mc.progressWindow( endProgress=True )
						
		return	returnVal

def shortestPathBetween2Verts( vertA, vertB, **keywords ):
	
	"Returns a list of adjacent vertices defining the shortest path from vertA to vertB."
	
	return(PolyVertexList( vertA, vertB, **keywords ).shortestPath())
		
