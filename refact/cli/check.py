from astroid.nodes import Call
from astroid.nodes.scoped_nodes.scoped_nodes import ClassDef, FunctionDef
import glob
import sys
from Levenshtein import distance
import os
from termcolor import colored
from astroid import parse



def add_module(modules, methods, calls, modname):
   
   modules[modname] = {}
   
   with open(modname) as mfr:
      lines = mfr.readlines()
      code = ''.join(lines)

   module = parse(code)
   
   modules[modname]["module"] = module
   modules[modname]["methods"] = {}
   modules[modname]["classes"] = {}
   modules[modname]["calls"] = {}
   
   for chunk in module.body:
      if isinstance(chunk, ClassDef):
         if chunk.name not in modules[modname]['classes']:
            modules[modname]['classes'][chunk.name] = {'class':chunk, 'methods':[]}
            
         if chunk.name not in modules[modname]['calls']:
            modules[modname]['calls'][chunk.name] = {}
            
         for meth in chunk.body:
            if isinstance(meth, FunctionDef):
               for cal in meth.body:
                  if hasattr(cal, 'value') and isinstance(cal.value, Call):
                     
                     func_name = cal.value.func.as_string()
                     
                     if func_name.find('.') >= 0:
                        mname = func_name.split('.')[1]
                     else:
                        mname = func_name
                     
                     if mname not in calls:
                        calls[mname] = 0
                     calls[mname] += 1
                  
               if meth.name not in modules[modname]["methods"]:
                  modules[modname]["methods"][meth.name] = []
                  
               if meth.name not in methods:
                  methods[meth.name] = []
                  
               module.name = modname
               method = { 'method': meth, 'class': chunk, 'module': module, 'source': ''.join(lines[meth.lineno-1:meth.end_lineno])}
               
               methods[meth.name] += [method]
               modules[modname]["methods"][meth.name] += [method]

               modules[modname]['classes'][chunk.name]['methods'] += [method]
        
def find_refactors(dir, pattern, dist):
   modules = {}
   methods = {}
   calls = {}

   os.chdir(dir)
   files = [file for file in glob.glob(pattern, recursive=True) if file.find("tests") == -1 and file.find("migrations") == -1 and file.find("__init__.py") == -1]
   for file in files:
      try:
         add_module(modules, methods, calls, file)
      except:
         import traceback
         print(traceback.format_exc())
         print("Error parsing ", file)
         del modules[file]

   counts = [(meth, len(methods[meth]), methods[meth]) for meth in methods if len(methods[meth]) > 1]

   def sort_counts(tup, pos, rev):
      tup.sort(key = lambda x: x[pos], reverse=rev)
      return tup
   
   def calc_similarity(methods):
      
      results = []
      
      for method in methods:
         source = method['source']
         for _method in methods:
            if _method != method:
               _source = _method['source']
               _dist = distance(source,_source)
               # print(_dist,_method['method'].name,  _method['module'].name+":"+_method['class'].name, method['module'].name+method['class'].name)
               if _dist < dist:
                  results += [(_dist, _method, method)]
      
      return results
   
   tree = {}
   
   for item in sort_counts(counts,1,True):
      results = calc_similarity(item[2])
      for result in sort_counts(results, 0, False):
         if result[1]["method"].name not in tree:
            tree[result[1]["method"].name] = []
            
         tree[result[1]["method"].name] += [(result[0], result[1], result[2])]
            
   return tree, calls