from sys import modules
class Module():
	def __init__(*args,**keywords):
		shortNames={
		}
		if len(args)==0: return
		for k in keywords:
			if k in self.__dict__():
				exec('self.'+k+'=keywords[k]')
			elif k in shortNames:
				exec('self.'+shortNames[k]+'=keywords[k]')
	