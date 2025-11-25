from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import JSONParser, FormParser, MultiPartParser
from rest_framework.response import Response
from .serializers import *
import json
from urllib.parse import urlencode
from urllib.request import urlopen, Request
from urllib.error import HTTPError
from django.contrib.auth.models import User
from workspace.models import Project, Theme
from copy import deepcopy
import markdown
import base64
import mimetypes
import yaml
from jinja2 import Template, Environment, meta
import traceback
import re
import os
from glide import *
from django.conf import settings
import pathlib, shutil, subprocess

def _isBinary(fileName):
  fileType, encoding = mimetypes.guess_type(fileName)
  if fileType.startswith('text/')\
    or fileType == 'application/json'\
    or fileType == 'application/x-latex'\
    or fileType == 'application/javascript'\
    or fileType == 'application/yaml'\
    or fileName.endswith('.md'): # Just in case
    return False
  else:
    return True

# @api_view(['GET'])
# def theme(request, slug):
#   """
#   Responds with a list of all the themes available
#     or a theme when specified
#   """
#   themes = Theme.objects.all()
#   if slug:
#     themes = themes.filter(slug=slug)
#   serializer = ThemeSerializer(themes, many=True)
#   return Response(serializer.data)


# @api_view(['GET'])
# def project(request, slug):
#   """
#   Responds with a project object specified
#   """
#   projects = Project.objects.all()
#   if slug:
#     projects = projects.filter(slug=slug)
#   serializer = ProjectSerializer(projects, many=True)
#   return Response(serializer.data)


@api_view(['GET'])
def repositories(request):
  """
  Responds with a list of repositories
    that are accessible to the authenticated user
  """
  accessToken = request.session['accessToken']
  getAllReposUrl = 'https://api.github.com/user/repos?&per_page=100&access_token={}'
  getAllReposUrl = getAllReposUrl.format(accessToken)
  getAllReposUrl = getAuthUrl(getAllReposUrl)
  with urlopen(getAllReposUrl) as allReposRes:
    resStr = allReposRes.read().decode('utf-8')
    return Response({ 'repositories': resStr })


@api_view(['GET'])
def readme(request, owner, repo):
  """
  Responds with HTML-rendered README.md
    that are accessible to the authenticated user
  """
  accessToken = request.session['accessToken']
  getReadmeUrl = 'https://api.github.com/repos/{}/{}/readme?access_token={}'
  getReadmeUrl = getReadmeUrl.format(owner, repo, accessToken)
  getReadmeUrl = getAuthUrl(getReadmeUrl)
  req = Request(
    url=getReadmeUrl, method='GET',
    headers={'Content-Type': 'application/vnd.github.v3.html+json'})
  try:
    with urlopen(req) as readmeRes:
      resStr = readmeRes.read().decode('utf-8')
      readmeObj = json.loads(resStr)
      mdContent = readmeObj['content']
      if readmeObj['encoding'] == 'base64':
        mdContent = base64.b64decode(mdContent).decode('utf-8')
        res = _mdToHtml(mdContent)
        return Response({
          'readme': res
        })
      else:
        return Response({
          'error': 'decoding'
        })
  except HTTPError:
    return Response({
      'error': 'HTTPError'
    })


@api_view(['POST'])
def cdn(request, owner, repo):
  """
  Responds with RawGit url for the specified file
  """
  res = {}
  accessToken = request.session['accessToken']
  file = request.data['file']
  # branch = request.data['branch']
  commit = _getLatestCommit(accessToken, owner, repo)
  cdnUrl = 'https://cdn.rawgit.com/{}/{}/{}/{}'
  cdnUrl = cdnUrl.format(owner, repo, commit['sha'], file['path'])
  return Response({
    'cdnUrl': cdnUrl
  })


@api_view(['POST'])
def parse(request):
  template = request.data['templateFileContent']
  jinjaEnv = Environment(autoescape=False)
  absSynTree = jinjaEnv.parse(template)
  keys = list(meta.find_undeclared_variables(absSynTree))
  keys = sorted(keys, key=lambda x:template.index('{{'+x+'}}'))
  return Response({
    'keys': keys
  })


@api_view(['GET'])
def branches(request, repositoryFullName):
  """
  Responds with a list of branches in the specified project
  """
  accessToken = request.session['accessToken']
  getBranchesUrl = 'https://api.github.com/repos/{}/branches?&per_page=100&access_token={}'
  getBranchesUrl = getBranchesUrl.format(repositoryFullName, accessToken)
  getBranchesUrl = getAuthUrl(getBranchesUrl)
  with urlopen(getBranchesUrl) as branchesRes:
    resStr = branchesRes.read().decode('utf-8')
    res = json.loads(resStr)
    return Response({ 'branches': res })


@api_view(['GET'])
def commits(request, owner, repo, branch):
  """
  Responds with a list of commits on the specified branch
    in the specified repository
  """
  accessToken = request.session['accessToken']
  getCommitsUrl = 'https://api.github.com/repos/{}/{}/commits?sha={}&access_token={}'
  getCommitsUrl = getCommitsUrl.format(owner, repo, branch, accessToken)
  getCommitsUrl = getAuthUrl(getCommitsUrl)
  with urlopen(getCommitsUrl) as commitsRes:
    resStr = commitsRes.read().decode('utf-8')
    res = json.loads(resStr)
    return Response({ 'commits': res })


def _getLatestCommit(accessToken, repoUsername, projectSlug):
  """
  Returns the latest commit object of a repository
  """
  commitsUrl = 'https://api.github.com/repos/{}/{}/commits?access_token={}'
  commitsUrl = commitsUrl.format(repoUsername, projectSlug, accessToken)
  commitsUrl = getAuthUrl(commitsUrl)
  with urlopen(commitsUrl) as commitsRes:
    res = commitsRes.read().decode('utf-8')
    commits = json.loads(res)
    return commits[0]


def _getLatestSha(accessToken, repoUsername, projectSlug):
  """
  Returns the hash value of the latest commit of a repository
  """
  latestCommit = _getLatestCommit(accessToken, repoUsername, projectSlug)
  return latestCommit['sha']


def _getRepoTree(accessToken, repoUsername, projectSlug, branch='master', commit=None):
  """
  Returns the latest tree structure of a repository.
  The branch can be specified. Otherwise, it assumes master.
  The commit SHA can be specified. Otherwise, it assumes latest commit.
  """
  sha = ''
  if not commit:
    sha = _getLatestSha(accessToken, repoUsername, projectSlug)
  else:
    sha = commit
  repoTreeUrl = 'https://api.github.com/repos/{}/{}/git/trees/{}?recursive=1?access_token={}'
  repoTreeUrl = repoTreeUrl.format(repoUsername, projectSlug, sha, accessToken)
  repoTreeUrl = getAuthUrl(repoTreeUrl)
  with urlopen(repoTreeUrl) as repoTreeRes:
    res = repoTreeRes.read().decode('utf-8')
    repoTree = json.loads(res)
    for file in repoTree['tree']:
      file['name'] = file['path'].split('/')[-1]
    return repoTree


def _createReference(accessToken, owner, repo, ref, refTo):
  createRefUrl = 'https://api.github.com/repos/{}/{}/git/refs?access_token={}'.format(owner, repo, accessToken)
  createRefUrl = getAuthUrl(createRefUrl)
  createRefData = {
    'ref': 'refs/heads/' + ref,
    'sha': refTo
  }
  createRefData = json.dumps(createRefData).encode('utf-8')
  with urlopen(createRefUrl, createRefData) as createRefRes:
    resStr = createRefRes.read().decode('utf-8')
    return json.loads(resStr)


def _updateReference(accessToken, owner, repo, ref, refTo):
  updateRefUrl = 'https://api.github.com/repos/{}/{}/git/refs/{}?access_token={}'
  updateRefUrl = updateRefUrl.format(owner, repo, ref, accessToken)
  updateRefUrl = getAuthUrl(updateRefUrl)
  updateRefData = {
    'sha': refTo
  }
  updateRefData = json.dumps(updateRefData).encode('utf-8')
  req = Request(
    url=updateRefUrl, headers={'Content-Type': 'application/json'},
    data=updateRefData, method='PATCH')
  with urlopen(req) as createFileRes:
    resStr = createFileRes.read().decode('utf-8')
    return json.loads(resStr)


def _mdToHtml(md):
  return markdown.markdown(md)


@api_view(['POST'])
def clone(request):
  """
  Clone a project from specified GitHub url.
  GETs existing repositories on GitHub to check potential name duplicates.
  POSTs a new repository on GitHub and create a project instance on Glide server.
  """
  accessToken = request.session['accessToken']
  repoUrl = request.data['repoUrl']
  owner = request.data['owner']
  repo = request.data['repo']
  getRepoUrl = 'https://api.github.com/repos/{}/{}?access_token={}'.format(owner, repo, accessToken)
  getRepoUrl = getAuthUrl(getRepoUrl)
  with urlopen(getRepoUrl) as reposRes:
    resStr = reposRes.read().decode('utf-8')
    return Response({ 'repository': resStr })


@api_view(['GET', 'POST'])
def branch(request, owner=None, repo=None, branch=None):
  """
  GETs a branch from GitHub
  POSTs a reference on GitHub repo as a new branch
  """
  if request.method == 'GET':
    accessToken = request.session['accessToken']
    getBranchUrl = 'https://api.github.com/repos/{}/{}/branches/{}?access_token={}'
    getBranchUrl = getBranchUrl.format(owner, repo, branch, accessToken)
    getBranchUrl = getAuthUrl(getBranchUrl)
    with urlopen(getBranchUrl) as branchRes:
      resStr = branchRes.read().decode('utf-8')
      return Response({ 'branch': json.loads(resStr) })
  elif request.method == 'POST':
    accessToken = request.session['accessToken']
    newBranchName = request.data['newBranchName']
    shaBranchFrom = request.data['shaBranchFrom']
    owner = request.data['owner']
    repo = request.data['repo']
    createRefRes = _createReference(accessToken, owner, repo, newBranchName, shaBranchFrom)
    return Response({
      'createRefRes': createRefRes
    })


@api_view(['POST'])
def commit(request):
  repositoryFullName = request.data['repository']
  tree = request.data['tree']
  branch = 'heads/{}'.format(request.data['branch'])
  commit = request.data['commit']
  message = request.data['message']
  accessToken = request.session['accessToken']
  createTreeUrl = 'https://api.github.com/repos/{}/git/trees?access_token={}'
  createTreeUrl = createTreeUrl.format(repositoryFullName, accessToken)
  createTreeUrl = getAuthUrl(createTreeUrl)
  createTreeData = {
    'tree': tree
  }
  createTreeData = json.dumps(createTreeData).encode('utf-8')
  with urlopen(createTreeUrl, createTreeData) as createTreeRes:
    resStr = createTreeRes.read().decode('utf-8')
    res = json.loads(resStr)
    treeSha = res['sha']
    createCommitUrl = 'https://api.github.com/repos/{}/git/commits?access_token={}'
    createCommitUrl = createCommitUrl.format(repositoryFullName, accessToken)
    createCommitUrl = getAuthUrl(createCommitUrl)
    createCommitData = {
      'message': message,
      'tree': treeSha,
      'parents': [commit]
    }
    createCommitData = json.dumps(createCommitData).encode('utf-8')
    with urlopen(createCommitUrl, createCommitData) as createCommitRes:
      resStr = createCommitRes.read().decode('utf-8')
      newCommit = json.loads(resStr)
      newCommitSha = newCommit['sha']
      updateRefUrl = 'https://api.github.com/repos/{}/git/refs/{}?access_token={}'
      updateRefUrl = updateRefUrl.format(repositoryFullName, branch, accessToken)
      updateRefUrl = getAuthUrl(updateRefUrl)
      updateRefData = {
        'sha': newCommitSha
      }
      updateRefData = json.dumps(updateRefData).encode('utf-8')
      req = Request(
        url=updateRefUrl, headers={'Content-Type': 'application/json'},
        data=updateRefData, method='PATCH')
      with urlopen(req) as updateRefRes:
        resStr = updateRefRes.read().decode('utf-8')
        res = json.loads(resStr)
        return Response({
          'createTreeRes': treeSha,
          'createCommitRes': newCommit,
          'updateRefRes': res
        })


# @api_view(['POST'])
# def createProject(request):
#   """
#   Create a new instance of project.
#   GETs existing repositories on GitHub to check potential name duplicates.
#   POSTs a new repository on GitHub and create a project instance on Glide server.
#   """
#   username = request.session['username']
#   repoUsername = username.split('@')[0]
#   user = User.objects.filter(username=username)[0]
#   accessToken = request.session['accessToken']
#   title = request.data['title']
#   slug = request.data['slug']
#   description = request.data['description']
#   repoUrl = request.data['repoUrl']
#   theme = request.data['theme']
#   getAllReposUrl = 'https://api.github.com/user/repos?access_token={}'.format(accessToken)
#   getAllReposUrl = getAuthUrl(getAllReposUrl)
#   with urlopen(getAllReposUrl) as allReposRes:
#     resStr = allReposRes.read().decode('utf-8')
#     allReposJson = json.loads(resStr)
#     repoNames = [repo['name'] for repo in allReposJson]
#     if not slug in repoNames:
#       if not Project.objects.filter(owner=username, slug=slug):
#         createRepoUrl = 'https://api.github.com/user/repos?access_token={}'.format(accessToken)
#         createRepoData = {'name': slug, 'description': description, 'auto_init': True}
#         createRepoData = json.dumps(createRepoData).encode('utf-8')
#         createRepoUrl = getAuthUrl(createRepoUrl)
#         with urlopen(createRepoUrl, createRepoData) as createRepoRes:
#           resStr = createRepoRes.read().decode('utf-8')
#           theme = Theme.objects.get(slug=theme)
#           project = Project.objects.create(
#             owner=user,
#             title=title,
#             slug=slug,
#             description=description,
#             repoUrl=repoUrl,
#             theme=theme
#           )
#           projects = Project.objects.all()
#           themeTree = _getRepoTree(accessToken, theme.author, theme.slug)
#           for file in themeTree['tree']:
#             if file['type'] == 'tree' or not file['downloadUrl']:
#               continue
#             newFile = {}
#             newFile['path'] = 'theme/' + file['path']
#             with urlopen(file['downloadUrl']) as fileContentRes:
#               newFile['originalContent'] = getBase64Bytes(fileContentRes.read())
#               _createFile(accessToken, repoUsername, slug, newFile)
#           return Response({
#             'project': ProjectSerializer(project, many=False).data,
#             'projects': ProjectSerializer(projects, many=True).data
#           })
#     return Response({'error': 'The project title is being used.'})


@api_view(['GET', 'POST'])
def tree(request, owner, repo, branch, commit):
  """
  Returns tree structure of a project.
  The HTTP parameter specifies the project ID (slug).
  GETs the latest commit hash value (sha) of the repository.
  GETs the tree (file structure in GitHub repo) data for the commit.
  Actual content requests and delivery will be on client side (AJAX).
  """
  accessToken = request.session['accessToken']
  if request.method == 'POST':
    pass
  elif request.method == 'GET':
    repoTree = _getRepoTree(accessToken, owner, repo, branch, commit)
    paths = list(set([file['path'] for file in repoTree['tree'] if file['type']=='tree']))
    paths = sorted(paths, key=lambda x:len(x.split('/')), reverse=True)
    
    def pathToDict(pathString):
      pathList = pathString.split('/')
      pathList.reverse()
      stack = [{}]
      for path in pathList:
        stack.append({path: stack.pop()})
      return stack[0]

    def mergeDicts(d1, d2):
      res = {}
      commonKeys = list(set(d1.keys()) & set(d2.keys()))
      for commonKey in commonKeys:
        res[commonKey] = mergeDicts(d1[commonKey], d2[commonKey])
      for key in list(d1.keys()):
        if not key in commonKeys:
          res[key] = d1[key]
      for key in list(d2.keys()):
        if not key in commonKeys:
          res[key] = d2[key]
      return res

    def traversFs(fsDict, stack, f):
      for folder in list(fsDict.keys()):
        stack.append(folder)
        traversFs(fsDict[folder], stack, f)
        filesInFolder = [file for file in f if file['type'] != 'tree' and file['path'].startswith('/'.join(stack))]
        for file in filesInFolder:
          name = file['name']
          file['originalContent'] = None
          file['modified'] = False
          file['added'] = False
          fsDict[folder][name] = file
          f.remove(file)
        stack.pop()

    def transformFs(fsDict, res, parentPath):
      def _isFolder(x):
        if not 'originalContent' in x:
          return True
        else:
          return False
      res['nodes'] = []
      for key in fsDict:
        if _isFolder(fsDict[key]):
          path = '/'.join([parentPath, key])
          thisFolder = {'name': key, 'path': path, 'type': 'tree'}
          res['nodes'].append(transformFs(fsDict[key], thisFolder, path))
        else:
          fsDict[key]['nodes'] = []
          res['nodes'].append(fsDict[key])
      return res

    pathDicts = []
    fs = {}
    for path in paths:
      pathDict = pathToDict(path)
      pathDicts.append(pathDict)
    for pathDict in pathDicts:
      fs = mergeDicts(fs, pathDict)
    rootFiles = [file for file in repoTree['tree'] if file['path'] == file['name'] and file['type'] != 'tree']
    for file in rootFiles:
      name = file['name']
      file['originalContent'] = None
      file['modified'] = False
      file['added'] = False
      fs[file['name']] = file
    recursiveTree = transformFs(fs, {}, '')
    return Response({ 'recursiveTree': recursiveTree, 'tree': repoTree })


@api_view(['GET', 'POST'])
def blob(request, owner, repo, sha=None):
  """
  GET a blob specified and return it
  POST a blob to create it on GitHub
  """
  accessToken = request.session['accessToken']
  if request.method == 'GET':
    if sha:
      getBlobUrl = 'https://api.github.com/repos/{}/{}/git/blobs/{}?access_token={}'
      getBlobUrl = getBlobUrl.format(owner, repo, sha, accessToken)
      getBlobUrl = getAuthUrl(getBlobUrl)
      with urlopen(getBlobUrl) as blobRes:
        resStr = blobRes.read().decode('utf-8')
        return Response({ 'blob': json.loads(resStr) })
    else:
      return Response({ 'error': 'sha should be specified' })
  elif request.method == 'POST':
    content = request.data['originalContent']
    encoding = 'utf-8'
    if 'encoding' in request.data:
      encoding = request.data['encoding']
    createBlobUrl = 'https://api.github.com/repos/{}/{}/git/blobs?access_token={}'
    createBlobUrl = createBlobUrl.format(owner, repo, accessToken)
    createBlobUrl = getAuthUrl(createBlobUrl)
    createBlobData = { 'content': content, 'encoding': encoding }
    createBlobData = json.dumps(createBlobData).encode('utf-8')
    with urlopen(createBlobUrl, createBlobData) as createBlobRes:
      resStr = createBlobRes.read().decode('utf-8')
      createBlobRes = json.loads(resStr)
      return Response({
        'url': createBlobRes['url'],
        'sha': createBlobRes['sha']
      })


@api_view(['POST'])
def pr(request):
  repositoryFullName = request.data['repository']
  head = request.data['head']
  base = request.data['base']
  title = request.data['pullReqTitle']
  body = request.data['pullReqBody']
  accessToken = request.session['accessToken']
  createPullReqUrl = 'https://api.github.com/repos/{}/pulls?access_token={}'
  createPullReqUrl = createPullReqUrl.format(repositoryFullName, accessToken)
  createPullReqUrl = getAuthUrl(createPullReqUrl)
  createPullReqData = {
    'title': title,
    'head': head,
    'base': base,
    'body': body
  }
  createPullReqData = json.dumps(createPullReqData).encode('utf-8')
  req = Request(
    url=createPullReqUrl, headers={'Content-Type': 'application/json'},
    data=createPullReqData, method='POST')
  try:
    with urlopen(req) as createPullReqRes:
      resStr = createPullReqRes.read().decode('utf-8')
      return Response({
        'createPullReqRes': json.loads(resStr),
        'code': createPullReqRes.getcode()
      })
  except HTTPError as ex:
    for e in ex:
      e = e.decode('utf-8')
      e = json.loads(e)
      errors = e['errors']
      for error in errors:
        if error['resource'] == 'PullRequest' and error['message'].startswith('A pull request already exists for'):
          return Response({
            'createPullReqRes': None,
            'code': None,
            'message': 'A pull request already exists.'
          })


@api_view(['POST'])
def renderFile(request):
  """
  Respond with rendered html
  Consider using Misaka (https://github.com/FSX/misaka) package,
    which has more like GitHub flavored markdown renderer
  """
  file = request.data['file']
  fileName = file['name']
  extension = fileName.split('.')
  res = { 'srcDoc': None }
  
  if len(extension) > 1:
    extension = extension[-1]
  else:
    extension = None

  if extension in ['md', 'markdown', 'mdown', 'mkdn', 'mkd']:
    if 'newContent' in file and file['newContent']:
      res['srcDoc'] = _mdToHtml(file['newContent'])
    else:
      res['srcDoc'] = _mdToHtml(file['originalContent'])

  return Response(res)


@api_view(['POST'])
def hardclone(request):
  cloneUrl = request.data['cloneUrl']
  repositoryFullName = request.data['repository']
  branch = request.data['branch']
  username = request.session['username'].split('@')[0]
  userBasePathStr = os.path.join(settings.MEDIA_ROOT, 'repos', repositoryFullName, branch, username)
  userBasePath = pathlib.Path(userBasePathStr)
  if userBasePath.exists():
    if userBasePath.is_file():
      userBasePath.unlink()
    elif userBasePath.is_dir():
      shutil.rmtree(userBasePathStr, ignore_errors=True)
  userBasePath.mkdir(mode=0o777, parents=True)
  cloneCommand = 'git clone -b {} {} {}'.format(branch, cloneUrl, userBasePathStr)
  cloneCompProc = subprocess.run(
    cloneCommand.split(), stdin=subprocess.PIPE,
    input=None, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
  )
  return Response({
    'args': cloneCompProc.args,
    'returncode': cloneCompProc.returncode,
    'stdout': cloneCompProc.stdout,
    'stderr': cloneCompProc.stderr
  })


@api_view(['POST'])
def newFile(request):
  repositoryFullName = request.data['repository']
  branch = request.data['branch']
  path = request.data['path']
  fileName = request.data['fileName']
  fileOrFolder = request.data['fileOrFolder']
  username = request.session['username'].split('@')[0]
  userBasePathStr = os.path.join(settings.MEDIA_ROOT, 'repos', repositoryFullName, branch, username)
  
  if fileOrFolder == 'file':
    newFilePath = pathlib.Path(userBasePathStr) / path / fileName
    newFile = {}
    newFile['path'] = str(newFilePath)
    newFile['path'] = newFile['path'].replace(userBasePathStr, '')
    newFile['path'] = newFile['path'][1:]
    newFile['name'] = os.path.basename(newFile['path'])
    newFile['nodes'] = []
    newFile['added'] = True
    newFile['modified'] = False
    newFile['sha'] = None
    newFile['url'] = None
    newFile['type'] = 'blob'
    newFile['mode'] = '100644'
    newFile['originalContent'] = ''
    newFile['size'] = 0
    with open(str(newFilePath), 'w') as nf:
      nf.write(newFile['originalContent'])
    return Response({
      'res': newFilePath.exists(),
      'createdFiles': [newFile]
    })
  elif fileOrFolder == 'folder':
    newFolderPath = pathlib.Path(userBasePathStr) / path / fileName
    newFolderPath.mkdir(mode=0o777, parents=True)
    newFolder = {
      'path': str(newFolderPath).replace(userBasePathStr + '/', ''),
      'name': fileName,
      'nodes': [],
      'type': 'tree',
      'mode': '040000'
    }
    return Response({
      'res': newFolderPath.exists(),
      'createdFiles': [newFolder]
    })


@api_view(['POST'])
@parser_classes((FormParser, MultiPartParser, ))
def uploadFile(request):
  repositoryFullName = request.data['repository']
  branch = request.data['branch']
  path = request.data['path']
  file = request.data['files']
  username = request.session['username'].split('@')[0]
  userBasePathStr = os.path.join(settings.MEDIA_ROOT, 'repos', repositoryFullName, branch, username)
  uploadedFilePath = pathlib.Path(userBasePathStr) / path / file.name
  fileContent = file.read()
  with open(str(uploadedFilePath), 'wb') as fo:
    fo.write(fileContent)
  newFile = {}
  newFile['path'] = str(uploadedFilePath)
  newFile['path'] = newFile['path'].replace(userBasePathStr, '')
  newFile['path'] = newFile['path'][1:]
  newFile['name'] = os.path.basename(newFile['path'])
  newFile['nodes'] = []
  newFile['added'] = True
  newFile['modified'] = False
  newFile['sha'] = None
  newFile['url'] = None
  newFile['type'] = 'blob'
  newFile['mode'] = '100644'
  newFile['originalContent'] = base64.b64encode(fileContent).decode('utf-8')
  newFile['size'] = os.stat(str(uploadedFilePath)).st_size
  return Response({
    'res': uploadedFilePath.exists(),
    'createdFiles': [newFile],
    'size': newFile['size']
  })


@api_view(['POST'])
def updateFile(request):
  repositoryFullName = request.data['repository']
  branch = request.data['branch']
  filePath = request.data['filePath']
  newVal = request.data['newVal']
  username = request.session['username'].split('@')[0]
  userBasePathStr = os.path.join(settings.MEDIA_ROOT, 'repos', repositoryFullName, branch, username)
  actualPath = pathlib.Path(userBasePathStr) / filePath
  with open(str(actualPath), 'w') as fo:
    fo.write(newVal)
  return Response({
    'res': actualPath.exists(),
    'size': os.stat(str(actualPath)).st_size
  })

@api_view(['POST'])
def manipulateFile(request):
  accessToken = request.session['accessToken']
  manipulation = request.data['manipulation']
  source = request.data['source']
  targetPath = request.data['targetPath']
  repositoryFullName = request.data['repository']
  branch = request.data['branch']
  username = request.session['username'].split('@')[0]
  userBasePathStr = os.path.join(settings.MEDIA_ROOT, 'repos', repositoryFullName, branch, username)
  userBasePath = pathlib.Path(userBasePathStr)
  if manipulation == 'rename':
    sourcePath = str(userBasePath / source['path'])
    targetPath = str(userBasePath / targetPath)
    shutil.move(sourcePath, targetPath)
    fileContent = None
    with open(targetPath, 'rb') as f:
      fileContent = f.read()
    content = base64.b64encode(fileContent).decode('utf-8')
    return Response({
      'content': content
    })
  elif manipulation == 'delete':
    targetPath = str(userBasePath / targetPath)
    if os.path.isfile(targetPath):
      os.remove(targetPath)
    else:
      shutil.rmtree(targetPath, ignore_errors=True)
    return Response({
      'targetPath': targetPath
    })
  elif manipulation == 'copy':
    sourcePath = str(userBasePath / source['path'])
    targetPath = str(userBasePath / targetPath)
    dupName = ''
    if sourcePath == targetPath + '/' + source['name']:
      nameSplit = source['name'].split('.')
      if len(nameSplit) > 1:
        nameSplit[-2] += ' copy'
        dupName = '.'.join(nameSplit)
      else:
        dupName = source['name'] + ' copy'
    else:
      dupName = source['name']
    targetPath += '/' + dupName
    res = shutil.copy(sourcePath, targetPath)
    fileContent = None
    with open(targetPath, 'rb') as f:
      fileContent = f.read()
    content = base64.b64encode(fileContent).decode('utf-8')
    return Response({
      'content': content,
      'targetPath': res.replace(userBasePathStr + '/', ''),
      'targetName': os.path.basename(res)
    })