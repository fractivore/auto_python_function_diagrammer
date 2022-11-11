import ast, os, re
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
    #look-behind regex splits at any of [_,.-/] preceded by 7 or more alphanumeric characters
    wrapped = re.split(r'(?<=[a-zA-Z0-9_,.-/]{7}[_,.-/])', text)
    #print(f"wrapped:{wrapped}")
    ind = max_len = ind_o_max = 0
    for word in wrapped:
        if len(word) > max_len:
            max_len = len(word)
            ind_o_max = ind
        ind += 1
        lines.append(word)
    width = font.getsize(lines[ind_o_max])[0]
    height = font.getsize(text)[1]
    img = Image.new('RGBA', (width+10, height*len(lines)+10), color=(255,0,0,0))
    imgDraw = ImageDraw.Draw(img)
#    lines = text_wrap(text,font,180)
#    print(lines)
    x=0
    y=0
    for line in lines:
        imgDraw.text((x,y), line, fill=color, font=font)
        y += fontsize +5  

    return img
def main():
    #create tmp directory
    if not os.path.exists("tmp_resources") or not os.path.isdir("tmp_resources"):
        os.mkdir("tmp_resources")
    include_vars=False
    EDGE_LABELS_ON=False
    NODE_LABELS_ON=False
    MOD_LABEL_ON=True
    func_dict=dict()
    name_cats_dict=dict()
    parser = ArgumentParser()
    parser.add_argument('-f','--filename', type=str , help='Filename to parse as AST.')
    cli_args = parser.parse_args()
    filename_in = cli_args.filename
    print(f"________FILENAME_IN______: {filename_in}")
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
    class_dict = dict()
    for class_ in classes:
        class_dict[class_.name] = {'definitions':dict(),'calls':{'native':set(),'imports':set()}}
    #    print("Class name:", class_.name)
        for node in class_.body:
            if isinstance(node, ast.FunctionDef):
                class_dict[class_.name]['definitions'][node.name] = {'native':set(),'imports':set()}
                node_walked = ast.walk(node)
                for subnode in node_walked:
                    for subsubnode in ast.walk(subnode):
                        if isinstance(subsubnode, ast.Call):
                            print(f"subnode.__dict__:{subnode.__dict__} ||||| subsubnode.__dict__:{subsubnode.__dict__}")
                    if isinstance(subnode, ast.Call):
                        #print(f"subnode.func.__dict__: {subnode.func.__dict__}")
                        #print(f"subnode.__dict__:{subnode.__dict__}")
                        #print(f"node.__dict__:{node.__dict__}")
                        if 'id' in subnode.func.__dict__.keys() and subnode.func.id not in builtins_set:
                            if subnode.func.id in imp_names:
                                class_dict[class_.name]['definitions'][node.name]['imports'].add(subnode.func.id)
                            else:
                                class_dict[class_.name]['definitions'][node.name]['native'].add(subnode.func.id)
                        #elif 'attr' in subnode.func.__dict__.keys():
                            #print(f"subnode.func.attr:{subnode.func.attr}")
                            #print(f"subnode.func.ctx.__dict__:{subnode.func.ctx.__dict__}")
                if node.name in func_dict:
                    del func_dict[node.name]
            if isinstance(node, ast.Call):
                if 'id' in node.func.__dict__.keys() and node.func.id not in builtins_set:
                    if node.func.id in imp_names:
                        class_dict[class_.name]['calls']['imports'].add(node.func.id)
                    else:
                        class_dict[class_.name]['calls']['native'].add(node.func.id)
    #    for method in methods:
            #show_info(method, "class_.name method")
    #print(f"func_dict:{func_dict}")
    #print(f"imp_dict:{imp_dict}")
    #print(f"class_dict:{class_dict}")

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
        with Cluster(f"{filename_in} Classes"):
            nodes_by_name['classes'] = dict()
            for mod in class_dict:
                nodes_by_name['classes'][mod] = dict()
                with Cluster(mod):
                    nodes_by_name['classes'][mod]['calls']=dict()
                    for name in class_dict[mod]['calls']['native']:
                        if NODE_LABELS_ON:
                            name_label = name
                        else:
                            name_label = ""
                        color = encode_text_as_RGB_simple(name)
                        img = create_img(name,color)
                        saved_img=f"./tmp_resources/{name}.png"
                        img.save(saved_img)
                        nodes_by_name['classes'][mod]['calls']['native'][name] = Custom(name_label, saved_img)
                    for name in class_dict[mod]['calls']['imports']:
                        if NODE_LABELS_ON:
                            name_label = name
                        else:
                            name_label = ""
                        color = encode_text_as_RGB_simple(name)
                        img = create_img(name,color)
                        saved_img=f"./tmp_resources/{name}.png"
                        img.save(saved_img)
                        nodes_by_name['classes'][mod]['calls']['imports'][name] = Custom(name_label, saved_img)
                    with Cluster("Methods"):
                        nodes_by_name['classes'][mod]['definitions']=dict()
                        for name in class_dict[mod]['definitions']:
                            nodes_by_name['classes'][mod]['definitions'][name]={'native':{},'imports':{}}
                            with Cluster(name):
                                for subname in class_dict[mod]['definitions'][name]['native']:
                                    if NODE_LABELS_ON:
                                        name_label = subname
                                    else:
                                        name_label = ""
                                    color = encode_text_as_RGB_simple(name)
                                    img = create_img(name,color)
                                    saved_img=f"./tmp_resources/{subname}.png"
                                    img.save(saved_img)
                                    nodes_by_name['classes'][mod]['definitions'][name]['native'][subname] = Custom(name_label, saved_img)
                                nodes_by_name['classes'][mod]['definitions'][name]['imports']=dict()
                                for subname in class_dict[mod]['definitions'][name]['imports']:
                                    if NODE_LABELS_ON:
                                        name_label = subname
                                    else:
                                        name_label = ""
                                    color = encode_text_as_RGB_simple(name)
                                    img = create_img(name,color)
                                    saved_img=f"./tmp_resources/{subname}.png"
                                    img.save(saved_img)
                                    nodes_by_name['classes'][mod]['definitions'][name]['imports'][subname] = Custom(name_label, saved_img)

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
            if 'native' not in nodes_by_name.keys():
                nodes_by_name['native'] = dict()
            if 'classes' not in nodes_by_name.keys():
                nodes_by_name['classes'] = dict()
            if 'imports' not in nodes_by_name.keys():
                nodes_by_name['imports'] = dict()
            for mod in func_dict:
                color = encode_text_as_RGB_simple(mod)
                if MOD_LABEL_ON:
                    mod_label = mod
                else:
                    mod_label = ""
                with Cluster(mod_label):
                    nodes_by_name['native'][mod] = dict()
                    img = create_img(mod,color)
                    saved_img=f"./tmp_resources/{mod}.png"
                    img.save(saved_img)
                    nodes_by_name['native'][mod]['MODNODE'] = Custom("",saved_img)
                    with Cluster(""):
                        with Cluster("In-file"):
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
            #print(f"nodes_by_name:{nodes_by_name}")
            for mod in class_dict:
                for inner in class_dict[mod]['definitions']:
                    for inner_layer_two in class_dict[mod]['definitions'][inner]['native']:
                        if inner_layer_two in nodes_by_name['native'] and inner_layer_two in nodes_by_name['classes:'][mod]['definitions'][inner]['native']:
                            this_label=f"{mod}"
                            if EDGE_LABELS_ON:
                                nodes_by_name['native'][inner_layer_two]['MODNODE'] >> Edge(color=encode_text_as_RGB_simple(this_label), label=this_label,penwidth="5",style="dashed") >> nodes_by_name['classes'][mod]['definitions'][inner]['native'][inner_layer_two]
                            if not EDGE_LABELS_ON:
                                nodes_by_name['native'][inner_layer_two]['MODNODE'] >> Edge(color=encode_text_as_RGB_simple(this_label), penwidth="5") >> nodes_by_name['classes'][mod]['definitions'][inner]['native'][inner_layer_two]
                    for inner_layer_two in class_dict[mod]['definitions'][inner]['imports']:
                        if inner_layer_two in nodes_by_name['imports'] and inner_layer_two in nodes_by_name['classes:'][mod]['definitions'][inner]['imports']:
                            this_label=f"used by {mod}"
                            if EDGE_LABELS_ON:
                                nodes_by_name['imports'][inner_layer_two]['MODNODE'] >> Edge(color=encode_text_as_RGB_simple(this_label), label=this_label,penwidth="5",style="dashed") >> nodes_by_name['classes'][mod]['definitions'][inner]['imports'][inner_layer_two]
                            if not EDGE_LABELS_ON:
                                nodes_by_name['imports'][inner_layer_two]['MODNODE'] >> Edge(color=encode_text_as_RGB_simple(this_label), penwidth="5") >> nodes_by_name['classes'][mod]['definitions'][inner]['imports'][inner_layer_two]
            for mod in func_dict:
                for inner in func_dict[mod]['native']:
                    if inner in nodes_by_name['native'] and inner in nodes_by_name['native'][mod]:
                        this_label=f"used by {mod}"
                        if EDGE_LABELS_ON:
                            nodes_by_name['native'][inner]['MODNODE'] >> Edge(color=encode_text_as_RGB_simple(this_label), label=this_label,penwidth="5",style="dashed") >> nodes_by_name['native'][mod][inner]
                        if not EDGE_LABELS_ON:
                            nodes_by_name['native'][inner]['MODNODE'] >> Edge(color=encode_text_as_RGB_simple(this_label), penwidth="5") >> nodes_by_name['native'][mod][inner]
                for inner in func_dict[mod]['imports']:
                    for imp in imp_dict:
                        if inner in nodes_by_name['native'][mod] and inner in nodes_by_name['imports'][imp]:
                            this_label=f"used by {mod}"
                            if EDGE_LABELS_ON:
                                nodes_by_name['imports'][imp][inner] >> Edge(color=encode_text_as_RGB_simple(this_label),label=this_label,penwidth="5",style="dotted") >>nodes_by_name['native'][mod][inner]
                            if not EDGE_LABELS_ON:
                                nodes_by_name['imports'][imp][inner] >> Edge(color=encode_text_as_RGB_simple(this_label),penwidth="5", style="dotted") >>nodes_by_name['native'][mod][inner]
    rmtree('./tmp_resources')


if __name__=='__main__':
    main()
