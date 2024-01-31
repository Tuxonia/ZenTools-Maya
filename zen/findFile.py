#use glob instead of listdir

import sys,os,fnmatch
import re
from platform import system

from zen.iterable import iterable
from zen.isIterable import isIterable
from zen.getReversed import getReversed
from zen.intersect import intersect
from zen.removeDuplicates import removeDuplicates
from zen.removeAll import removeAll

_mayaNative=False

for m in sys.modules:
	if type(sys.modules[m]).__name__=='module' and sys.modules[m].__name__.lower()=='maya':
		_mayaNative=True

if _mayaNative:
	import maya.cmds as mc
	import maya.mel as mel
	import maya.utils as mu
	from zen.findWorkSpace import findWorkSpace

def findFile(*args,**keywords):

	"""
Returns an absolute path for each given file name or partial file path.
Arguments:
	The file name or names for which to search. Accepts regular expressions as well as exact names.
Keywords:
	searchPath(sp):
		Specifies an exclusive search directory. Input type: string or list.
	path(p):
		Specifies a non-exclusive search directory. If the file is not found in the path given, smart search will be used. Input type: string or list.
	all(a):
		Find all occurences of given file or directory names. Input type: bool. Default: False.
	applications(app):
		Search in the given application directory(s). Matches by regular expression.
	each(e):
		Find one occurence of each given file or directory name in each directory in searchPath.
		Input type: bool. Default: if applications==True: False, otherwise: True.
	file(f):
		Search for files. Input type: bool. Default: True.
	directory(d,dir):
		Search for directories. Input type: bool. Default: If argument contains a '.': False, otherwise: True.
	regularExpression(re):
		Treat arguments as regular expressions. Default: If argument contains "special" characters such as '*': True, otherwise: False.
	pathRegularExpression(re):
		Treat searchPath, path, and application keywords values as regular expressions or lists of regular expressions.
		Default: If any keywords values contain "special" characters such as '*': True, otherwise: False.
	"""

	return _FileSearch(*args,**keywords)

class FileSearch(list):
	"Constructs search data for findFile."
	def __init__(self,*args,**keywords):

		# default options
		self.shortNames=\
		{
			'pr':'project',
			'w':'workspace'
		}

		#attributes
		self.melPath=[]
		self.pyPath=[]
		self.openWorkSpaces=[]
		self.allWorkSpaces=[]
		self.workSpaces=[]
		self.openFiles=[]
		self.homeDirs=[]
		self.programDirs=[]
		self.roots=[]

		self.__call__(*args,**keywords)

	def __call__(self,*args,**keywords):

		# default options
		recursive=True
		applications=[]
		home=True
		roots=True
		path=[]
		pathRegularExpression=False
		searchPath=[]
		plugin=False
		isDirectory=False # keyword directory
		isFile=False # keyword file
		all=False
		each=False
		regularExpression=False

		shortNames=\
		{
			'a':'all',
			'd':'isDirectory',
			'directory':'isDirectory',
			'dir':'isDirectory',
			'p':'path',
			'pre':'pathRegularExpression',
			'f':'isFile',
			'file':'isFile',
			'ss':'smartSearch',
			'sp':'searchPath',
			're':'regularExpression',
			'app':'applications',
			'rec':'recursive',
			'e':'each'
		}

		self.openWorkSpaces=[]
		self.openFiles=[]

		for k in keywords:
			if k in self.__dict__:
				exec('self.'+k+'=keywords[k]')
			elif k in locals():
				exec(k+'=keywords[k]')
			elif k in self.shortNames:
				exec('self.'+self.shortNames[k]+'=keywords[k]')
			elif k in shortNames:
				exec(shortNames[k]+'=keywords[k]')

		sel=[]
		for a in args:
			sel.extend(iterable(a))

		if not isDirectory and not isFile and len(sel)>0:
			if len(sel[0].split('.'))<2:
				isDirectory=True
			isFile=True

		if isinstance(applications,bool) and applications:
			applications=['*.*']

		path=iterable(path)
		searchPath=iterable(searchPath)
		applications=iterable(applications)

		for p in searchPath:
			if '*' in p or not os.path.isdir(p):
				pathRegularExpression=True

		if len(applications)>0:
			pathRegularExpression=True
			if 'each' not in keywords and 'e' not in keywords: each=True

		filePaths=[]

		for s in sel:

			if '*' in s:
				regularExpression=True

			selRE=re.compile(s)

			f=[]
			searched=[]

			if len(applications)>0:
				searchPath=self.getProgramDirs(pre=pathRegularExpression,*applications)
				pathRegularExpression=False

			if len(searchPath)>0 and not pathRegularExpression:
				searchDirCmds=['searchPath']
			elif s.split('.')[-1].split('*')[-1] in ['py','pyc','pyo']:
				searchDirCmds=['path','getReversed(sys.path)','self.getOpenFiles()','self.getOpenWorkSpaces()','self.getAllWorkSpaces()','self.getMelPath()','self.getProgramDirs('+str(applications)+',pre='+str(pathRegularExpression)+')']
			elif s.split('.')[-1].split('*')[-1] in ['mel']:
				searchDirCmds=['path','self.getMelPath()','self.getOpenFiles()','self.getOpenWorkSpaces()','self.getAllWorkSpaces()','getReversed(sys.path)','self.getProgramDirs('+str(applications)+',pre='+str(pathRegularExpression)+')']
			else:
				searchDirCmds=['path','self.getOpenFiles()','self.getOpenWorkSpaces()','self.getAllWorkSpaces()','getReversed(sys.path)','self.getMelPath()','self.getProgramDirs('+str(applications)+',pre='+str(pathRegularExpression)+')']
			if home and not applications:
				searchDirCmds.append('self.getHomeDirs()')
			if roots and not applications:
				searchDirCmds.append('self.getRoots()')

			for sdCmd in searchDirCmds:

				searchDir=removeAll(searched,eval(sdCmd))
				searched.extend(searchDir)

				while len(searchDir)>0 and (f==[] or all):

					sd=[]
					for d in searchDir:

						found=False

						matchDir=True

						if pathRegularExpression:
							matchDir=False
							for p in (searchPath+path):
								if type(re.compile(p).search(d+'/')).__name__!='NoneType':
									matchDir=True

						if matchDir:

							if s in d and os.path.exists(d) and os.access(d,os.F_OK):
								if d[-len(s):]==s:
									if\
									(
										(os.path.isfile(d) and isFile) or
										(os.path.isdir(d) and isDirectory)
									):
										f.append(d.replace('\\','/'))
										found=True
										if not(all or each): break
								elif\
								(
									isDirectory and
									d[d.index(s)-1] in ['/','\\'] and
									d[d.index(s)+len(s)] in ['/','\\']
								):
									if os.path.isdir(d[:d.index(s)+len(s)]):
										f.append(d[:d.index(s)+len(s)].replace('\\','/'))
										found=True
										if not(all or each): break

							elif regularExpression and type(selRE.search(d)).__name__!='NoneType':
								if  d[-len(selRE.search(d).group()):]==selRE.search(d).group():
									if\
									(
										(os.path.isfile(d) and isFile) or
										(os.path.isdir(d) and isDirectory)
									):
										f.append(d.replace('\\','/'))
										found=True
										if not(all or each): break

						if\
						(
							(all or not found) and
							os.path.isdir(d) and
							not(not(recursive) and (os.path.dirname(d) in searchPath or os.path.dirname(d) in path))
						):
							if d[-1] in ['/','\\']:
								d=d[:-1]
							try:#avoids acess denied errors
								for fn in iterable(os.listdir(d)):
									sd.append((d+'/'+fn).replace('\\','/'))
							except:
								pass
					searchDir[:]=sd[:]

				if f!=[] and not all: break

			filePaths.extend(iterable(f))

		if len(filePaths)==0:
			self[:]=[]
			return []
		else:
			self[:]=filePaths
			if len(filePaths)==1:
				return filePaths[0]
			else:
				return filePaths

	def getMelPath(self):

		if self.melPath==[] and _mayaNative:
			if system()[:3].lower()=='win':
				seperator=';'
			else:
				seperator=':'
			self.melPath=getReversed(mel.eval('getenv("MAYA_SCRIPT_PATH")').split(seperator))

		return self.melPath

	def getOpenFiles(self):

		if self.openFiles==[] and _mayaNative:
			self.openFiles=mc.file(q=True,l=True)

		return self.openFiles

	def getOpenWorkSpaces(self):

		if self.openWorkSpaces==[] and _mayaNative:

			self.openWorkSpaces=[mc.workspace(q=True,rd=True)]
			if self.getOpenFiles()[0] not in self.openWorkSpaces[0]:
				 self.openWorkSpaces.extend(iterable(findWorkSpace()))

		return self.openWorkSpaces

	def getAllWorkSpaces(self):

		if self.allWorkSpaces==[] and _mayaNative:
			 self.allWorkSpaces=iterable(mc.workspace(q=True,l=True))

		return self.allWorkSpaces

	def getHomeDirs(self):

		if self.homeDirs==[]:
			self.homeDirs=[os.path.expanduser('~')]

		return self.homeDirs

	def getRoots(self):

		if self.roots==[]:

			pass

		return self.roots

	def getAllProgramDirs(self):

		if self.programDirs==[]:

			if sys.platform[:3].lower()=='win':
				path=os.environ['PATH'].split(';')
			else:
				path=os.environ['PATH'].split(':')

			common=os.path.commonprefix(path)

			if common=='' or os.path.dirname(common)==common:

				roots={}
				if common=='':
					for p in path:
						if p.split('/')[0] not in roots:
							roots[p.split('/')[0]]=[p]
						else:
							roots[p.split('/')[0]].append(p)
				else:
					roots[common.split('/')[0]]=path

				for r in roots:
					progDirs={}
					for p in roots[r]:
						rootDir='/'.join(p.split('/')[:2])
						if rootDir not in progDirs:
							progDirs[rootDir]=[p]
						else:
							if p not in progDirs[rootDir]:
								progDirs[rootDir].append(p)
					for pd in progDirs:
						useTop=True
						progDirs[pd].sort()
						if len(progDirs[pd])>1:
							for d in progDirs[pd][2:]:
								if progDirs[pd][0] not in d:
									useTop=False
						if not useTop:
							pd=os.path.commonprefix(progDirs[pd])

						if pd[-1]=='/': pd=pd[:-1]

						if os.path.exists(pd):
							self.programDirs.append(pd)

			else:
				self.programDirs=[common]

		return self.programDirs

	def getProgramDirs(self,*args,**keywords):

		pathRegularExpression=False

		shortNames=\
		{
			'pre':'pathRegularExpression'
		}

		for k in keywords:
			if k in locals():
				exec(k+'=keywords[k]')
			elif k in shortNames:
				exec(shortNames[k]+'=keywords[k]')

		sel=[]
		for a in args:
			sel.extend(iterable(a))

		for s in sel:
			if s=='*.*':
				return self.getAllProgramDirs()

		dirs=self.getAllProgramDirs()
		returnVal=[]

		i=0

		while i<2:

			ds=dirs
			dirs=[]

			for d in ds:

				matchDir=False

				for s in sel:
					if (pathRegularExpression and type(re.compile(s).search(d+'/')).__name__!='NoneType') or (s in d):
						matchDir=True
						returnVal.append(d)
						break

				if not matchDir:
					try:#avoids acess denied errors
						for p in os.listdir(d):
							if os.path.isdir(d+'/'+p):
								dirs.append(d+'/'+p)
					except:
						pass

			i+=1

		return returnVal

_FileSearch=FileSearch()

def openFile(*args,**keywords):

	for f in iterable(findFile(*args,**keywords)):
		os.startfile(f)

def showFile(*args,**keywords):

	for f in iterable(findFile(*args,**keywords)):
		os.startfile(os.path.dirname(f))

#Filename globbing utility.
#standard lib in Python 2.5 and later, included for backwards compatibility with 2.4

def glob(pathname):
    """Return a list of paths matching a pathname pattern.

    The pattern may contain simple shell-style wildcards a la fnmatch.

    """
    return list(iglob(pathname))

def iglob(pathname):
    """Return a list of paths matching a pathname pattern.

    The pattern may contain simple shell-style wildcards a la fnmatch.

    """
    if not has_magic(pathname):
        if os.path.lexists(pathname):
            yield pathname
        return
    dirname, basename = os.path.split(pathname)
    if not dirname:
        for name in glob1(os.curdir, basename):
            yield name
        return
    if has_magic(dirname):
        dirs = iglob(dirname)
    else:
        dirs = [dirname]
    if has_magic(basename):
        glob_in_dir = glob1
    else:
        glob_in_dir = glob0
    for dirname in dirs:
        for name in glob_in_dir(dirname, basename):
            yield os.path.join(dirname, name)

# These 2 helper functions non-recursively glob inside a literal directory.
# They return a list of basenames. `glob1` accepts a pattern while `glob0`
# takes a literal basename (so it only has to check for its existence).

def glob1(dirname, pattern):
    if not dirname:
        dirname = os.curdir
    try:
        names = os.listdir(dirname)
    except os.error:
        return []
    if pattern[0]!='.':
        names=[x for x in names if x[0]!='.']
    return fnmatch.filter(names,pattern)

def glob0(dirname, basename):
    if basename == '':
        # `os.path.split()` returns an empty basename for paths ending with a
        # directory separator.  'q*x/' should match only directories.
        if os.path.isdir(dirname):
            return [basename]
    else:
        if os.path.lexists(os.path.join(dirname, basename)):
            return [basename]
    return []


magic_check = re.compile('[*?[]')

def has_magic(s):
    return magic_check.search(s) is not None

