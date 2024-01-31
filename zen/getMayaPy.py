import os
from sys import modules,platform
import sys
import re
from zen.findFile import findFile

def getMayaPy(*keywords):
	
	version=''
	
	shortNames=\
	{
		'v':'version'
	}

	for k in keywords:
		if k in locals():
			exec(k+'=keywords[k]')
		elif k in shortNames:
			exec(shortNames[k]+'=keywords[k]')
	
	mayaNative=False
	
	for m in modules:
		
		if type(modules[m]).__name__=='module' and modules[m].__name__.lower()=='maya':
			_mayaNative=True
	
	if not mayaNative:
		
		mayaAppDirs={}
		mayaBinDirs={}
		mayaPyDirs={}
		
		versionRE=re.compile('[Mm]aya[0-9\.]*[0-9\.]')
		
		#for pyDir in findFile('maya/__init__.py',sp='[Mm]aya[0-9\.]*[0-9\.]',a=True)		
		
		if len(mayaPyDirs)>0:
			
			if version=='': version=v

			sys.path.append(os.path.dirname(mayaPyDirs[version]))
			os.environ['MAYA_LOCATION']=mayaPyDirs[version]

			if 'linux' in platform.lower():
				if 'LD_LIBRARY_PATH' in os.environ:
					if platform[:3].lower()=='win':
						os.environ['LD_LIBRARY_PATH']+=';'
					else:
						os.environ['LD_LIBRARY_PATH']+=':'
				else:
					os.environ['LD_LIBRARY_PATH']=''
				
			os.environ['LD_LIBRARY_PATH']+=os.path.dirname(sys.path[-1])
				
			import maya.standalone
			maya.standalone.initialize()

