#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import ast
from graphviz import Digraph
import random
import argparse
from pathlib import Path


class PyScript:
    def __init__(self, full_path, project_name=None):
        # Initializing attributes
        self.full_path = full_path
        # If there is a project
        if project_name:
            project_path = full_path.split(project_name, 1)[1]
            project_path = project_path[1:]
            self.project_name = project_name
        # if not, assuming that the project name is the last folder
        else:
            project_path = full_path.split('/')[-2] + '/' + full_path.split('/')[-1]
            self.project_name = full_path.split('/')[-2]
        self.module_name = []
        # cutting the extension
        self.start_name = project_path[:-3].replace('/', '.')
        # Breaking the relative address into parts
        parts = self.start_name.split('.')
        # determining how deep the module is
        self.module_level = len(parts)
        # adding all parts of the name
        self.module_name.extend(parts)
        # imports
        self.importses = set()
        self.project_import = set()
        self.external_import = set()
        self.import_separated = False
        self.have_errors = False
        # classes and independent functions
        self.class_funct_def = []
        # the entire possible set of names for export
        self.name_to_export = set()
        # filling in the imports, classes and procedures
        self.get_data(full_path)
        self.gen_names_to_export()

    # filling in the imports, classes and procedures
    def get_data(self, full_path):
        # read the file
        with open(full_path, 'r', encoding='utf-8') as file:
            source_code = file.read()
        # parsing ast
        try:
            tree = ast.parse(source_code)
        except Exception as e:
            print(e)
            self.have_errors = True
            return None
        for node in ast.walk(tree):
            # if the import is simple, adding it as is
            if isinstance(node, ast.Import):
                for alias in node.names:
                    self.importses.add(alias.name)
            # if the import is complicated
            elif isinstance(node, ast.ImportFrom):
                # getting the names of imported items
                for alias in node.names:
                    # if the import is via a name, forming an import string
                    if node.module:
                        self.importses.add(node.module)
                        self.importses.add(node.module + "." + alias.name)
                    # if the import is via dots
                    else:
                        # going to the full address of the module and generate the import address
                        self.importses.add(self.full_path.split('/') [-node.level-1] + "." + alias.name)
            # here separating the functions within the class from the individual functions
            if isinstance(node, ast.FunctionDef):
                if not hasattr(node, "parent"):
                    self.class_funct_def.append(node.name)
            if isinstance(node, ast.ClassDef):
                # if a function is formed inside a function inside a class 
                # and does not receive self as input, then it will be 
                # considered independent, which is not very correct, 
                # but it does not matter specifically her
                for child in node.body:
                    if isinstance(child, ast.FunctionDef):
                        child.parent = node
                self.class_funct_def.append(node.name)
            self.outside_impor = self.importses
        return None

    # creating a set of names for export
    def gen_names_to_export(self):
        names_to_export = []
        buffer = ""
        # here we simply go through all possible combinations of options for accessing 
        # the module and the classes/procedures in it, assuming that the __init__ files are formed
        for nameses in self.module_name:
            names_to_export.append(nameses)
            names_to_export.append(self.project_name + '.' + nameses)
            if buffer:
                names_to_export.append(buffer + '.' + nameses)
                names_to_export.append(self.project_name + '.' + buffer + '.' + nameses)
            for defindes in self.class_funct_def:
                names_to_export.append(self.project_name + '.' + nameses + '.' + defindes)
                names_to_export.append(nameses + '.' + defindes)
                names_to_export.append(self.project_name + '.' + defindes)
                if buffer:
                    names_to_export.append(self.project_name + '.' + buffer + '.' + nameses + '.' + defindes)
                    names_to_export.append(nameses + '.' + buffer + '.' + defindes)
                    names_to_export.append(self.project_name + '.' + buffer + '.' + defindes)
            if buffer:
                buffer = buffer + '.' + nameses
            else:
                buffer = nameses
        self.names_to_export = set(names_to_export)
        return None

    # forming a string of what exactly is being exported
    def gen_inner_export(self, intersectes):
        in_export = set()
        # looking for matching names 
        for item in intersectes:
            # looking for procedures and classes
            for definded in self.class_funct_def:
                if definded in item:
                    in_export.add(definded)
        # if there are none, then write "All"
        if len(in_export) == 0:
            in_export = "All"
        # otherwise, assembling it into a single line with cr-lf
        else:
            in_export = '\n'.join(in_export)
        return in_export

    # specifying internal and external imports
    def separate_import(self, full_intersectes):
        self.internal_import = full_intersectes.intersection(self.importses)
        self.external_import = self.importses.difference(self.internal_import)
        # if something is imported directly by the project name
        self.external_import.discard(self.project_name)
        self.import_separated = True
        return None

    # creating a string of what exactly is being imported
    def gen_external_import(self):
        grouped = {}
        to_dots = {}
        # just in case, checking that the import has already been split
        if self.import_separated:
            for item in self.external_import:
                # if the external import contains a compound name
                if '.' in item:
                    # dividing it by a point
                    first_part, rest = item.split('.', 1)
                    # the first part is the package name
                    if first_part not in grouped:
                        # and if there was something after the dot,
                        grouped[first_part] = []
                    # adding this as part of the dictionary
                    grouped[first_part].append(rest)
                else:
                    # or expand the dictionary if this package has already been encountered
                    if item not in grouped:
                        grouped[item] = []
            # assembling it into a single line with cr-lf
            for item in grouped:
                to_dots[item] = '\n'.join(grouped[item])
            return to_dots
        else:
            return ""


# collecting all the python files in a folder
def find_python_files(directory):
    py_paths = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                py_path = os.path.join(root, file)
                py_paths.append(py_path)
    return py_paths


# generating the project name
def get_project_name(directory):
    # if there is no / at the end, add it
    if directory[:-1] != "/":
        directory = directory + "/"
    return os.path.basename(os.path.dirname(directory))


# checking the project directory
def check_directory(directory):
    directory = Path(directory)
    if not directory.exists():
        print(f"Error: The directory '{directory}' does not exist.")
        exit()
    elif not directory.is_dir():
        print(f"Error: The path '{directory}' is not a directory.")
        exit()
    return


# checking for write access to the svg file
def check_file_access(svg_file):
    try:
        with open(svg_file, 'a') as f:
            pass  # Just open the file for recording
        return
    except PermissionError:
        print(f"Error: There is no write access on the way '{svg_file}'.")
        exit()
    except Exception as e:
        print(f"Error: {e}")
        exit()


# creating objects from py files
def get_pyscript_obj(py_paths, project_name):
    py_scripts = []
    for py_path in py_paths:
        new_obj = PyScript(py_path, project_name)
        py_scripts.append(new_obj)
    return py_scripts


# adding a node for internal import and an edge:
def add_inner_edge(dot, scripts, moduleses, intersectes, args):
    dot.node(moduleses.full_path, moduleses.start_name, shape="box", color='green')
    # drawing an edge between them with the label that we imported
    label = ""
    # if label is enabled
    if not args.no_label:
        label = scripts.gen_inner_export(intersectes)
    # forming a random darker color
    color = f'#{random.randint(0, 150):02x}{random.randint(0, 150):02x}{random.randint(0, 150):02x}'
    dot.edge(scripts.full_path, moduleses.full_path, label=label, color=color, fontcolor=color)
    return None


# adding a node for external import and an edge:
def add_external_edge(dot, ext_import, item, args, scripts):
    dot.node(item, item, shape="box", color='red')
    label = ""
    # if label is enabled
    if not args.no_label:
        label = ext_import[item]
    # forming a random lighter color
    color = f'#{random.randint(140, 230):02x}{random.randint(140, 230):02x}{random.randint(140, 230):02x}'
    dot.edge(item, scripts.full_path, label=label, color=color, fontcolor=color)
    return None


usage = """%(prog)s PROJECT_DIRECTORI SVG_FILENAME -e -l"""
description = "Analysis of the import within the project and its graphical representation"
parser = argparse.ArgumentParser(usage=usage, description=description)
parser.add_argument('directory', type=str, help='The full address of the project folder')
parser.add_argument('svg_file', type=str, help='The name of the file to save the graph')
parser.add_argument(
        "-e",
        "--no-external",
        action="store_true",
        default=False,
        dest="no_external",
        help="Hide external import",
    )
parser.add_argument(
        "-l",
        "--no-label",
        action="store_true",
        default=False,
        dest="no_label",
        help="Hide import signatures",
    )
args = parser.parse_args()
directory = args.directory
check_directory(directory)
svg_file = args.svg_file
# Converting a file name to an absolute path if it is specified without a directory
if '/' not in svg_file and '\\' not in svg_file:
    svg_file = os.path.join(os.getcwd(), svg_file)
check_file_access(svg_file)
project_name = get_project_name(directory)
# finding all python files
py_paths = find_python_files(directory)
# objects based on each python file
py_scripts = get_pyscript_obj(py_paths, project_name)
# forming nodes and edges of a graph
dot = Digraph('wide')
print("Analyzing the project files")
for scripts in py_scripts:
    if scripts.have_errors:
        print("Error in the file", scripts.full_path)
        continue
    print(scripts.full_path)
    # a set for later separation of imports
    full_intersectes = set()
    # the node for the current file
    dot.node(scripts.full_path, scripts.start_name, shape="box", color='green')
    # getting the full set of possible combinations of names to import
    for moduleses in py_scripts:
        if moduleses.have_errors:
            print("Error in the file", moduleses.full_path)
            continue
        # if there are intersections in the set of names of the module and the imported one
        intersectes = scripts.names_to_export.intersection(moduleses.importses)
        if intersectes:
            # forming additional nodes and edges
            add_inner_edge(dot, scripts, moduleses, intersectes, args)
        full_intersectes.update(moduleses.names_to_export)
    # creating an external import
    if not args.no_external:
        # if the user has not forbidden it
        scripts.separate_import(full_intersectes)
        ext_import = scripts.gen_external_import()
        # If there is one, draw it.
        if ext_import:
            for item in ext_import:
                add_external_edge(dot, ext_import, item, args, scripts)

# image formation, saving to a file, display
dot.graph_attr['ranksep'] = str(len(py_scripts)/20)
dot.format = 'svg'
dot.render(filename=svg_file, view=True)
exit()
