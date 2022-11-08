import ast, os

from diagrams import Diagram, Cluster, Edge
from diagrams.programming.language import Python
from argparse import ArgumentParser
from sys import argv
import json
from pathlib import Path
from argparse import ArgumentParser


include_vars=False
func_dict=dict()
name_cats_dict=dict()
parser = ArgumentParser()
parser.add_argument('-f','--filename', type=str , help='Filename to parse as AST.')
cli_args = parser.parse_args()
filename_in = cli_args.filename

parsed_ast = ast.parse(Path(filename_in).read_text())
walked = ast.walk(parsed_ast)

filename_in = os.path.basename(filename_in)

calls = list()
functions = list()
imports = list()
classes = list()
modules = list()
func_dict = dict()
imp_dict = dict()

builtins_set = {"abs","all","any","ascii","bin","bool","bytearray","bytes","callable","chr","classmethod","compile","complex","delattr","dict","dir","divmod","enumerate","eval","exec","filter","float","format","frozenset","getattr","globals","hasattr","hash","help","hex","id","input","int","isinstance","issubclass","iter","len","list","locals","map","max","memoryview","min","next","object","oct","open","ord","pow","print","property",""	"","range","repr","reversed","round","set","setattr","slice","sorted","staticmethod","str","sum","super","tuple","type","vars","zip","__import__"}

for node in walked:
    if isinstance(node, ast.Call):
        calls.append(node)
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        functions.append(node)
    if isinstance(node, ast.ClassDef):
        classes.append(node)
    if isinstance(node, ast.Module):
        modules.append(node)
    if isinstance(node, (ast.Import, ast.ImportFrom)):
        imports.append(node)
imp_names = list()
imp_dict = dict()
for imp in imports:
    if 'module' in imp.__dict__.keys() and 'names' in imp.__dict__.keys():
        imp_dict[imp.module]=set()
        for name in imp.names:
            imp_dict[imp.module].add(name.name)
            imp_names.append(name.name)
    elif 'names' in imp.__dict__.keys():
        for name in imp.names:
            imp_dict[name.name] = set()
            imp_dict[name.name].add(name.name)
            imp_names.append(name.name)

for func in functions:
    func_dict[func.name] = {'native':set(),'imports':set()}
    func_walked = ast.walk(func)
    for node in func_walked:
        if isinstance(node, ast.Call):
            if 'id' in node.func.__dict__.keys() and node.func.id not in builtins_set:
                if node.func.id in imp_names:
                    func_dict[func.name]['imports'].add(node.func.id)
                else:
                    func_dict[func.name]['native'].add(node.func.id)

def show_info(functionNode,typestring):
    print(f"{typestring} name: {functionNode.name}")
    print("Args:")
#    for arg in functionNode.args.args:
#        import pdb; pdb.set_trace()
#        print("\tParameter name:", arg.arg)

#for function in functions:
    #show_info(function, "function")
    #print(f"function.__dict__: {function.__dict__}")
    #print(f"Function name: {function.name}")
    #print(f"Args: {', '.join([arg.arg for arg in function.args.args])}")

#for class_ in classes:
#    print("Class name:", class_.name)
#    methods = [n for n in class_.body if isinstance(n, ast.FunctionDef)]
#    for method in methods:
        #show_info(method, "class_.name method")
print(f"func_dict:{func_dict}")
print(f"imp_dict:{imp_dict}")

#best layout so far: osage
graph_attributes = {
        "bgcolor":"#3D9ABB",
        "decorate":"true",
        "layout":"osage"
}
filename_prefix = filename_in.split(".")[0]
filename_out=f"{filename_prefix}_functions"
with Diagram(f"{filename_in} Function Diagram", show=False, filename=filename_out, direction="LR", graph_attr=graph_attributes):
    nodes_by_name = dict()
    with Cluster(f"{filename_in} Imports"):
        nodes_by_name['imports'] = dict()
        for mod in imp_dict:
            nodes_by_name['imports'][mod] = dict()
            with Cluster(mod):
                for name in imp_dict[mod]:
                    nodes_by_name['imports'][mod][name] = Python(name)

    with Cluster(f"{filename_in} Functions"):
        nodes_by_name['native'] = dict()
        for mod in func_dict:
            nodes_by_name['native'][mod] = dict()
            nodes_by_name['native'][mod]['MODNODE'] = Python(mod)
            with Cluster(mod):
                with Cluster("Native"):
                    for inner in func_dict[mod]['native']:
                        nodes_by_name['native'][mod][inner] = Python(inner)
                with Cluster("Imports"):
                    for inner in func_dict[mod]['imports']:
                        nodes_by_name['native'][mod][inner] = Python(inner)
        print(f"nodes_by_name:{nodes_by_name}")
        for mod in func_dict:
            for inner in func_dict[mod]['native']:
                if inner in nodes_by_name['native'] and inner in nodes_by_name['native'][mod]:
                    this_label=f"used by {mod}"
                    nodes_by_name['native'][inner]['MODNODE'] >> Edge(color="blue", label=this_label) >> nodes_by_name['native'][mod][inner]
            for inner in func_dict[mod]['imports']:
                for imp in imp_dict:
                    if inner in nodes_by_name['native'][mod] and inner in nodes_by_name['imports'][imp]:
                        this_label=f"used by {mod}"
                        nodes_by_name['imports'][imp][inner] >> Edge(color="green",label=this_label) >>nodes_by_name['native'][mod][inner]

