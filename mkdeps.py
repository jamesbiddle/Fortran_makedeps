#!/usr/bin/env python3
import os
import sys
import fnmatch

if(len(sys.argv) > 1):
    program_dir = sys.argv[1]
else:
    program_dir = "."
programs = []
for file in os.listdir(program_dir):
    if fnmatch.fnmatch(file, "*.f90"):
        programs.append(os.path.join(program_dir, file))
depends = os.path.join(program_dir, "depends.mk")

if(len(sys.argv) >= 3):
    srcdirs = sys.argv[2:]
else:
    srcdirs = [program_dir]


def scan_program(program):
    """
    Scan fortran source file for modules.

    Also returns whether source is a program or module.

    """
    f = open(program, "r")
    module_names = []
    is_program = False
    for line in f:
        if(line.lstrip().startswith("program")):
            is_program = True

        if(line.lstrip().startswith("use")):
            line_list = line.split()
            name = remove_punctuation(line_list[1])
            module_names.append(name)

    f.close()
    return module_names, is_program


def get_name(path):
    """Returns basename of path without its extension."""
    return os.path.splitext(os.path.basename(path))[0]


def remove_punctuation(string):
    """Removes punctuation from a given string."""
    punctuations = '''!()-[]{};:'"\,<>./?@#$%^&*_~'''
    for x in string.lower():
        if x in punctuations:
            string = string.replace(x, "")

    return string


def find_modules(srcdir, progdir, module_names):
    """Scans directory for modules with matching names."""
    located_modules = []
    for file in os.listdir(srcdir):
        if file.endswith(".f90"):
            name = get_name(file)
            rel_dir = os.path.relpath(srcdir, progdir)
            file_match = [fnmatch.fnmatch(name.lower(), mod.lower())
                          for mod in module_names]
            if(any(file_match)):
                located_modules.append(os.path.join(rel_dir, name))

    return located_modules


dependencies = {}
for prog in programs:
    prog_name = get_name(prog)
    module_names, is_program = scan_program(prog)

    # If there are modules, locate their filenames
    located_modules = []
    missing_modules = []
    if module_names:
        for src in srcdirs:
            located_modules += find_modules(src, program_dir, module_names)

        names_lower = [mod.lower() for mod in module_names]
        located_lower = [os.path.basename(mod.lower())
                         for mod in located_modules]
        missing_modules = list(set(names_lower)
                               .symmetric_difference(set(located_lower)))
        missing_modules = [mod + ".o" for mod in missing_modules]
        located_modules = [mod + ".o" for mod in located_modules]

    if is_program:
        prog_name = prog_name + ".x"
        dependencies[prog_name] = located_modules
    else:
        prog_name = prog_name + ".o"
        dependencies[prog_name] = located_modules

# print(dependencies)

# Output result to depends.mk
f = open(depends, "w")
for key in dependencies:
    deps = " ".join(dependencies[key])
    f.write(key + ": " + deps + "\n")
f.close()

print("Generated ", depends, "\n")
