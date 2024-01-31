import re,os,sys
#settings
__author__="David Belais"
__helpURL__="http://www.belais.net/zentools"
__version__=1.61
__requiredPlugins__=["pointOnMeshInfo","decomposeMatrix","closestPointOnCurve"]

#auto config
_mayaNative=False
for m in sys.modules:
	if type(sys.modules[m]).__name__=='module' and sys.modules[m].__name__.lower()=='maya':
		_mayaNative=True
		break
if _mayaNative:
	import maya.cmds as mc
	import maya.mel as mel
	import maya.utils as mu
	#plugin check
	mc.progressWindow(
		 title="Working",
		 status="Checking For Necessary Plugins...",
		 progress=0,
		 max=len(__requiredPlugins__)+1
	)
	for plugin in __requiredPlugins__:
		if(not(mc.pluginInfo(plugin,q=True,l=True))):
			try:
				mc.loadPlugin(plugin)
			except:
				raise Exception("ZenTools requires the plugin "+plugin+" to be installed.")
		mc.progressWindow(e=True,s=1)
	mc.progressWindow(ep=True)
	#default options
	mel.eval('source "'+os.path.join(__path__[0],'mel/zenTools_defaultOptions.mel').replace('\\','/')+'"')
	#user options
	up=os.path.join(mc.internalVar(upd=True),'zenTools_userOptions.mel').replace('\\','/')
	if os.path.exists(up):
		mel.eval('source "'+up+'"')
	#mel scripts
	os.environ['MAYA_SCRIPT_PATH']+=os.pathsep+os.path.join(__path__[0],'mel').replace('\\','/')
	mel.eval('rehash')
	#menus
	mel.eval('source "'+os.path.join(__path__[0],'mel/zenScriptsMenu.mel').replace('\\','/')+'"')
	mel.eval('zenScriptsMenu')
	#keep track of component selection order
	sel=[]

