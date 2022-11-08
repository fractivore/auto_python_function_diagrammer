import ast, os
import diagrams
from diagrams import Diagram, Cluster, Edge
from diagrams.programming.language import Python
from diagrams.custom import Custom
from argparse import ArgumentParser
from sys import argv
import json
from pathlib import Path
from argparse import ArgumentParser
from shutil import rmtree

from PIL import Image, ImageDraw, ImageFont

def text_wrap(text, font, max_width):
        """Wrap text base on specified width. 
        This is to enable text of width more than the image width to be display
        nicely.
        @params:
            text: str
                text to wrap
            font: obj
                font of the text
            max_width: int
                width to split the text with
        @return
            lines: list[str]
                list of sub-strings
        """
        lines = []
        
        # If the text width is smaller than the image width, then no need to split
        # just add it to the line list and return
        if font.getsize(text)[0]  <= max_width:
            lines.append(text)
        else:
            #split the line by spaces to get words
            words = text.split('.')
            i = 0
            # append every word to a line while its width is shorter than the image width
            while i < len(words):
                line = ''
                while i < len(words) and font.getsize(line + words[i])[0] <= max_width:
                    line = line + words[i]+ " "
                    i += 1
                if not line:
                    line = words[i]
                    i += 1
                lines.append(line)
        return lines

#TODO: put this in a different module
str_to_hex_dict = {'a':5,'b':1,'c':2,'d':3,'e':4,'f':0,'g':6,'h':7,'i':8,'j':6,'k':10,'l':11,'m':12,'n':13,'o':14,'p':15,'q':0,'r':1,'s':2,'t':3,'u':4,'v':5,'w':9,'x':7,'y':8,'z':9,' ':10,'_':'11','L':12,'A':13,'B':14,'C':15,'D':0,'E':1,'F':2,'G':3,'H':4,'I':5,'J':6,'K':7,'L':8,'M':9,'N':10,'O':11,'P':12,'Q':13,'R':14,'S':15,'T':0,'U':1,'V':2,'W':3,'X':4,'Y':5,'Z':6,'.':7,'*':8,'0':9,'1':10,'2':11,'3':12,'4':13,'5':14,'6':15,'7':0,'8':1,'9':2}
def encode_text_as_RGB_simple(string_in):
    string_out_list = ["00","00","00"]
    index = 0
    for char in string_in:
        lst_ind = index%3
        tmp_int = int(string_out_list[lst_ind],base=16)
        tmp_int += (int(str_to_hex_dict[char])+tmp_int)%15
        string_out_list[lst_ind] = str(tmp_int).zfill(2)[0:2]
        index += 1
    string_out = "#"+string_out_list[0]+string_out_list[1]+string_out_list[2]
    return string_out

def get_opposite_color_tuple(string_in):
    r = (255-int(string_in[1:3]))
    g = (255-int(string_in[3:5]))
    b = (255-int(string_in[5:]))
    tuple_out = (r,g,b)
    return tuple_out

def create_img(text,color):
#    width = 200
#    height = 200
    fontsize=40
    font = ImageFont.truetype("Gidole-Regular.ttf", fontsize)
    lines = []
    for i in range(0, len(text), 10):
        lines.append(text[i:i+10])
    width = font.getsize(lines[0])[0]
    height = font.getsize(text)[1]
    img = Image.new('RGB', (width+10, height*len(lines)+10), color=color)
    imgDraw = ImageDraw.Draw(img)
#    lines = text_wrap(text,font,180)
#    print(lines)
    x=0
    y=0
    for line in lines:
        imgDraw.text((x,y), line, fill=get_opposite_color_tuple(color), font=font)
        y += fontsize +5  

    return img

#create tmp directory
os.mkdir("tmp_resources")
include_vars=False
EDGE_LABELS_ON=False
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
        "bgcolor":"#DDDDFF",
        "decorate":"true",
        "layout":"osage",
        "fontsize":"100.0",
        "concentrate":"true"
}
filename_prefix = filename_in.split(".")[0]
filename_out=f"{filename_prefix}_functions"
folder_path = f"./generated_diagrams/"
diagram_path = f"./generated_diagrams/{filename_out}"
if not os.path.exists(folder_path) or not os.path.isdir(folder_path):
    os.mkdir(folder_path)
with Diagram(f"{filename_in} Function Diagram", show=False, filename=filename_out, direction="LR", graph_attr=graph_attributes):
    nodes_by_name = dict()
    with Cluster(f"{filename_in} Imports"):
        nodes_by_name['imports'] = dict()
        for mod in imp_dict:
            nodes_by_name['imports'][mod] = dict()
            with Cluster(mod):
                for name in imp_dict[mod]:
                    color = encode_text_as_RGB_simple(name)
                    img = create_img(name,color)
                    saved_img=f"./tmp_resources/{name}.png"
                    img.save(saved_img)
                    nodes_by_name['imports'][mod][name] = Custom(name, saved_img)

    with Cluster(f"{filename_in} Functions"):
        nodes_by_name['native'] = dict()
        for mod in func_dict:
            nodes_by_name['native'][mod] = dict()
            color = encode_text_as_RGB_simple(mod)
            img = create_img(mod,color)
            saved_img=f"./tmp_resources/{mod}.png"
            img.save(saved_img)
            nodes_by_name['native'][mod]['MODNODE'] = Custom("",saved_img)
            with Cluster(mod):
                with Cluster("Native"):
                    for inner in func_dict[mod]['native']:
                        img = create_img(inner,color)
                        saved_img=f"./tmp_resources/{inner}.png"
                        img.save(saved_img)
                        nodes_by_name['native'][mod][inner] = Custom("",saved_img)
                with Cluster("Imports"):
                    for inner in func_dict[mod]['imports']:
                        img = create_img(inner,color)
                        saved_img=f"./tmp_resources/{inner}.png"
                        img.save(saved_img)
                        nodes_by_name['native'][mod][inner] = Custom("",saved_img)
        print(f"nodes_by_name:{nodes_by_name}")
        for mod in func_dict:
            for inner in func_dict[mod]['native']:
                if inner in nodes_by_name['native'] and inner in nodes_by_name['native'][mod]:
                    this_label=f"used by {mod}"
                    if EDGE_LABELS_ON:
                        nodes_by_name['native'][inner]['MODNODE'] >> Edge(color=encode_text_as_RGB_simple(this_label), label=this_label,penwidth="10",style="dashed") >> nodes_by_name['native'][mod][inner]
                    if not EDGE_LABELS_ON:
                        nodes_by_name['native'][inner]['MODNODE'] >> Edge(color=encode_text_as_RGB_simple(this_label), penwidth="10") >> nodes_by_name['native'][mod][inner]
                    print(encode_text_as_RGB_simple(this_label))
            for inner in func_dict[mod]['imports']:
                for imp in imp_dict:
                    if inner in nodes_by_name['native'][mod] and inner in nodes_by_name['imports'][imp]:
                        this_label=f"used by {mod}"
                        if EDGE_LABELS_ON:
                            nodes_by_name['imports'][imp][inner] >> Edge(color=encode_text_as_RGB_simple(this_label),label=this_label,penwidth="10",style="dotted") >>nodes_by_name['native'][mod][inner]
                        if not EDGE_LABELS_ON:
                            nodes_by_name['imports'][imp][inner] >> Edge(color=encode_text_as_RGB_simple(this_label),penwidth="10", style="dotted") >>nodes_by_name['native'][mod][inner]
rmtree('./tmp_resources')
