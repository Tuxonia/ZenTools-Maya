import maya.cmds as mc
import maya.mel as mel
from copy import copy
from array import array
from re import search
from sets import Set
from zen.isIterable import isIterable
from zen.removeAll import removeAll
from zen.geometry.polyComponentList import PolyComponentList

class PolyFaceList(PolyComponentList):
	def __init__(self,*args, **keywords):
		keywords['type']='f'
		self.create(*args,**keywords)

		
		
