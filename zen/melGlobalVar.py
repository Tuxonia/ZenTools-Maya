import maya.mel as mel
from zen.melEncode import melEncode
from zen.isIterable import isIterable

class MelGlobalVar:
	
	"""gets and sets mel global variables"""
	
	def __init__(self,*args,**keywords):
		
		self.type=''
		self.name=''
		self.array=False
		
		types=['int','float','string','vector']
		
		if len(args)>0 and isinstance(args[0],str):
			if ' ' in args[0]:
				vl=args[0].split(' ')
				for v in vl:
					if v=='': vl.remove(v)
				if vl[0] in types: self.type=vl[0]
				if(args[0][-2:]=='[]'):
					self.array=True
					self.name=vl[-1][:-2]
				else:
					self.name=vl[-1]
			else:
				self.name=args[0]
			if not self.name[0]=='$':self.name='$'+self.name
			
		elif len(keywords)>0:
			for k in keywords:
				self.name=k
				if not self.name[0]=='$':self.name='$'+self.name
				self.set(keywords[k])
				
	def __call__(self):
		return self.get()
		
	def get(self):
		
		melGlobals=mel.eval('env')
		
		if self.name in melGlobals: 
			return mel.eval(self.name+'='+self.name)
		else:
			return
						
	def set(self,val):
		
		if self.type=='vector':#vectors must be explicitly set
			if isIterable(val):
				if isIterable(val[0]):
					self.array=True
					valString='{'
					for i in range(0,len(val)):
						valString+='<<'+str(val[i][0])+','+str(val[i][1])+','+str(val[i][2])+'>>'
						if i<(len(val)-1): valString+=','
						else: valString+='}'
				else:
					valString='<<'+str(val[0])+','+str(val[1])+','+str(val[2])+'>>'
		else:
			if isIterable(val):
				self.array=True
				if len(val)>0:
					testVal=val[0]
				else:
					testVal=''
			else:
				testVal=val
				
			if isinstance(testVal,str):
				self.type='string'
			if isinstance(testVal,(int,float)):
				if self.type!='' and self.type in ['int','float']: pass
				else:
					if isinstance(testVal,float): self.type='float'
					else: self.type='int'
			valString=melEncode(val)
			
		cmd=self.type+' '+self.name
		if self.array: cmd+='[]'
		cmd+='='+valString
		
		return mel.eval(cmd)
