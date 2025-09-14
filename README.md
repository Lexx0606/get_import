# get_import
Import analysis within the project and its graphical representation
Scans the python project folder and creates a graph of imports inside the project (communication between modules) and from external packages. When constructing the graph, only the script texts are analyzed. The presence of external packages is not required for graph construction. If the graph turns out to be overloaded, you can disable the construction of external imports with the -e key or the signatures of imported objects with the -l key.
Usage:
get_import.py PROJECT_DIRECTORI SVG_FILENAME -e -l
PROJECT_DIRECTORI - The full address of the python project folder
SVG_FILENAME - The name of the file to save the graph
-e (--no-external) - Hide external import
-l (--no-label) - Hide imported object labels
