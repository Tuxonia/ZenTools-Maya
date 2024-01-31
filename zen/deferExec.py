import maya.mel as mel
from zen.isIterable import isIterable
from zen.melGlobalVar import MelGlobalVar
from zen.removeAll import removeAll
from zen.removeDuplicates import removeDuplicates
from zen.melEncode import melEncode
def deferExec(*args,**keywords):
	#defaults
	melCommand=False
	repeatable=True
	showErrors=True
	shortNames={
		'mel':'melCommand',
		're':'repeatable',
		'se':'showErrors'
	}
	if len(args)==0: return
	for k in keywords:
		if k in locals():
			exec(k+'=keywords[k]')
		elif k in shortNames:
			exec(shortNames[k]+'=keywords[k]')
	zdc=MelGlobalVar('zenDelayedCommands')
	dcStr=zdc.get()
	if isinstance(dcStr,str):
		dc=dcStr.split(';')
	else:
		dcStr=''
		dc=[]
	dcsjVar=MelGlobalVar('zenDelayedCommandsSJ')
	dcsj=dcsjVar.get()
	if type(dcsj).__name__=='NoneType':
		dcsj=''
	for a in args:
		if not repeatable:
			dc.remove(a)
		if isinstance(a,str):
			if melCommand:
				dc.append(a)
			else:
				lines=a.split('\n')
				if len(lines)==1:
					dc.append('python('+melEncode(a)+')')
				else:
					pyCmd='python(\n'
					for l in lines:
						pyCmd+=melEncode(l+'\n')+'+\n'
					pyCmd=pyCmd[:-2]+')'
					dc.append(pyCmd)
	sjExists=False
	if isIterable(dc) and len(dc)>0 and isinstance(dcsj,(int,float)) and dcsj!=0 and mel.eval('scriptJob -ex '+str(dcsj)):
		sjExists=True
	dc=removeAll([''],dc)
	zdc.set(';'.join(dc))
	if not(sjExists):
		cmd=(
			'scriptJob \n'+
			'	-ro true\n'+
			'	-e "idle" \n'+
			'	(\n'+
			'		'+melEncode('string $zenDeferExec_errCmds[]={};\n')+'+\n'+
			'		'+melEncode('for($c in (stringArrayRemoveDuplicates(stringToStringArray($zenDelayedCommands,\";\"))))\n')+'+\n'+
			'		'+melEncode('{\n')+'+\n'+
			'		'+melEncode('	if(catch(`eval($c)`)) $zenDeferExec_errCmds[size($zenDeferExec_errCmds)]=$c;\n')+'+\n'+
			'		'+melEncode('}\n')+'+\n'+
			'		'+melEncode('for($c in $zenDeferExec_errCmds) warning("errors encountered: \\n"+$c+"\\n");\n')+'+\n'+
			'		'+melEncode('$zenDelayedCommands="";\n')+'+\n'+
			'		'+melEncode('$zenDelayedCommandsSJ=0;\n')+'\n'+
			'	)'
		)
		dcsjVar.set(mel.eval(cmd))
