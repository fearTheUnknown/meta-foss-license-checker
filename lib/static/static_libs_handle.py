from static.file import *
from pprint import pprint
import oe.package
import os
import subprocess
import fnmatch
import json


def process_staticlibs(pkgfiles, d):

    nm_command = d.getVar('NM')

    #Get the debug package name
    for pkg in pkgfiles.keys():
        if pkg.endswith('-dbg'):
            debug_pkg_name = pkg
            break

    #Get a list of debug files generated in <recipe_name>-dbg of the current recipe
    debug_file_paths = pkgfiles[debug_pkg_name]

    #Extract list of shared libs .so
    shared_lib_paths = [shared_lib_path for shared_lib_path in debug_file_paths if '.so' in os.path.basename(shared_lib_path)]

    #Extract list of executables
    executable_paths = [executable_path for executable_path in debug_file_paths if os.access(executable_path, os.X_OK) and '.so' not in os.path.basename(executable_path)]

    #Get a list of all static libraries .a in the "RECIPE_SYSROOT" directory
    recipe_sysroot = d.getVar('RECIPE_SYSROOT')
    static_lib_paths = []

    for roots, dirs, files in os.walk(recipe_sysroot):
        for file in files:
            if file.endswith('.a'):
                static_lib_paths.append(os.path.join(roots, file))
    
    #Create dictionary of static libs which contains all text defined symbols of each
    static_lib_text_defined_symbol_table = {}
    for static_lib_path in static_lib_paths:

        static_lib_symbol_table_raw = subprocess.run([nm_command, '--defined-only', static_lib_path], capture_output=True, text=True).stdout
        print("Static lib %s: " % {static_lib_path})
        print(static_lib_symbol_table_raw)
        static_lib_symbol_table = [line.split()[2] for line in static_lib_symbol_table_raw.splitlines() if len(line.split()) > 2 and (line.split()[1] == 'T' or line.split()[1] == 't')]

        static_lib_text_defined_symbol_table[os.path.basename(static_lib_path)] = static_lib_symbol_table


    #With each executable and shared lib .so found in the debug folder <recipe_name>-dbg, check if the file has static linking to static libs in "RECIPE_SYSROOT"
    target_debug_file_paths = shared_lib_paths + executable_paths
    for target_debug_file_path in target_debug_file_paths:
        #Get list of defined symbols in the target debug file
        debug_file_symbol_table_raw = subprocess.run([nm_command, '--defined-only', target_debug_file_path], capture_output=True, text=True).stdout
        print("Debug file %s: " % {target_debug_file_path})
        print(debug_file_symbol_table_raw)
        debug_file_defined_symbols = [line.split()[2] for line in debug_file_symbol_table_raw.splitlines() if len(line.split()) > 2 and (line.split()[1] == 'T' or line.split()[1] == 't')]

        #Check if there is a defined symbol in debug file which is defined by a static lib
        for defined_symbol in debug_file_defined_symbols:

            for static_lib_name in static_lib_text_defined_symbol_table.keys():
                #Check if any defined symbol of the executable or shared lib .so file is defined by a static lib
                if defined_symbol in static_lib_text_defined_symbol_table[static_lib_name]:
                    #If yes, add the static lib into list of linked static libs
                    print("Found linked symbol in lib: ", static_lib_name)
                    print("The linked symbol: ", defined_symbol)
                else:
                    #else, do nothing to ignore the lib
                    pass
                
    # #Set linked static libs to env variable "STATICDEPENDLIST"
    # pass

# Return type (bits):
# 0 - not elf
# 1 - ELF
# 2 - stripped
# 4 - executable
# 8 - shared library
# 16 - kernel module
# 32 - object file
# 64 - AR Archive (static library)
def is_elf(path):
    exec_type = 0
    result = subprocess.check_output(["file", "-b", path], stderr=subprocess.STDOUT).decode("utf-8")

    if "ELF" in result:
        exec_type |= 1
        if "not stripped" not in result:
            exec_type |= 2
        if "executable" in result:
            exec_type |= 4
        if "shared" in result:
            exec_type |= 8
        if "relocatable" in result:
            if path.endswith(".ko") and path.find("/lib/modules/") != -1 and oe.package.is_kernel_module(path):
                exec_type |= 16
            elif path.endswith(".o"):
                exec_type |= 32
    elif "ar archive" in result:
        exec_type |= 64
    return (path, exec_type)

def __find_path(filepath, d):

    pkgdata_dir_path = d.getVar('PKGDATA_DIR')

    found = False
    for root, dirs, files in os.walk(os.path.join(pkgdata_dir_path, 'runtime')):
        for fn in files:
            with open(os.path.join(root,fn)) as f:
                for line in f:
                    if line.startswith('FILES_INFO:'):
                        val = line.split(': ', 1)[1].strip()
                        dictval = json.loads(val)
                        for fullpth in dictval.keys():
                            if fnmatch.fnmatchcase(fullpth, filepath):
                                found = True
                                return (fn, fullpth)
                        break
    if not found:
        bb.error("Unable to find any packages producing path %s" % filepath)

def __get_recipe_of_package(package_name, d):
    pkgdata_dir_path = d.getVar('PKGDATA_DIR')

    package_metadata_file_path = os.path.join(pkgdata_dir_path, 'runtime', package_name)

    if os.path.exists(package_metadata_file_path):
        with open(package_metadata_file_path, 'r') as f:
            for line in f:
                if line.startswith('PN:'):
                    recipe_name = line.split(':')[1].strip()
                    return recipe_name
    else:
        bb.error("Package metadata file %s does not exist" % package_metadata_file_path)

def __get_license_of_package(package_name, d):
    pkgdata_dir_path = d.getVar('PKGDATA_DIR')

    package_metadata_file_path = os.path.join(pkgdata_dir_path, 'runtime', package_name)

    if os.path.exists(package_metadata_file_path):
        with open(package_metadata_file_path, 'r') as f:
            for line in f:
                if line.startswith('LICENSE:'):

                    parsed_license_entry = line.split(':')

                    if len(parsed_license_entry) == 2:
                        license_name = parsed_license_entry[1].strip()
                        return license_name

                    elif len(parsed_license_entry) == 3:
                        license_name = parsed_license_entry[2].strip()
                        return license_name
                    
                    else:
                        bb.warn("Undefined format of LICENSE entry in package metadata file %s" % package_metadata_file_path)
                    
    else:
        bb.error("Package metadata file %s does not exist" % package_metadata_file_path)

def __add_info_from_pkgdata_dir(files, d):

    #Get base directories where metadata of files are accessible
    pkgdest_dir_path = d.getVar('PKGDEST')
    recipe_sysroot_dir_path = d.getVar('RECIPE_SYSROOT')
    pkgdata_dir_path = d.getVar('PKGDATA_DIR')

    for file in files:

        file_path = file.get_path()

        #Check if the file is located in RECIPE_SYSROOT or PKGDEST directory
        if recipe_sysroot_dir_path in file_path:
            root_filesystem_path_to_file = os.path.sep + os.path.relpath(file_path, recipe_sysroot_dir_path)

            #Find which package provide the file
            (package_name, file_path_in_filesystem) = __find_path(root_filesystem_path_to_file, d)

            #Get recipe of the package
            recipe_name = __get_recipe_of_package(package_name, d)

            #Get license of the package
            license_name = __get_license_of_package(package_name, d)

            #Set package, recipe and license of the provided file
            file.set_from_package(package_name)
            file.set_from_recipe(recipe_name)
            file.set_license(license_name)

        elif pkgdest_dir_path in file_path:

            #Get the path of file inside a root filesystem
            relative_path_to_file = os.path.relpath(file_path, pkgdest_dir_path)
            root_filesystem_path_to_file = os.path.sep + relative_path_to_file.split(os.path.sep, 1)[1]

            #Find which package provide the file
            (package_name, file_path_in_filesystem) = __find_path(root_filesystem_path_to_file, d)

            #Get recipe of the package
            recipe_name = __get_recipe_of_package(package_name, d)

            #Get license of the package
            license_name = __get_license_of_package(package_name, d)

            #Set package, recipe and license of the provided file
            file.set_from_package(package_name)
            file.set_from_recipe(recipe_name)
            file.set_license(license_name)

        else:
            bb.warn("File %s is not located in RECIPE_SYSROOT or PKGDEST directory" % file_path)

def __create_symbol_table_static_lib(file_path, d):
    symbol_table = {}

    checked_symbols = []

    #Get READELF command
    readelf = d.getVar('READELF')

    #Get symbol table log
    symbol_table_log = subprocess.check_output([readelf, '-sW', file_path], stderr=subprocess.STDOUT).decode("utf-8")

    previous_object_file_name = ''
    for line in symbol_table_log.splitlines():

        if line.startswith('File:'):
            line_parts = line.split(':')

            #Extract the file path
            file_path = line_parts[1].strip()

            #Extract lib name
            lib_name = os.path.basename(file_path)

            #Extract the name of object file
            bracket_start = lib_name.index('(') + 1
            bracket_end = lib_name.index(')')
            object_file_name = lib_name[bracket_start:bracket_end]

            #Add object file to the symbol table
            symbol_table[object_file_name] = {}

            #Set previous object file name for further use in the loop
            previous_object_file_name = object_file_name

            #Clear the checked symbols for the new object file
            checked_symbols = []
        
        elif len(line) == 0:
            #Ignore the line
            pass
        
        elif line.startswith('Symbol table'):
            #Ignore the line
            pass
        
        elif 'Num:' in line:
            #Ignore the line
            pass

        else: #This can only be a line containning symbol entry info of the previous object file
            #Split the current line into a list
            line_parts = line.split()

            #Add the symbol and its attributes to the symbol table
            if len(line_parts) == 8: #Valid symbol entry with symbol name
                symbol_index = int(line_parts[0].split(':')[0])
                symbol_value = line_parts[1]
                symbol_size = line_parts[2]
                symbol_type = line_parts[3]
                symbol_bind = line_parts[4]
                symbol_visibility = line_parts[5]
                symbol_location = line_parts[6]
                symbol_name = line_parts[7]

                #If symbol has overlapping, then simply append the index to the symbol name of the symbol
                if symbol_name in checked_symbols:
                    symbol_name = symbol_name + str(symbol_index)
                
                symbol_attributes = {
                    'index': symbol_index,
                    'value': symbol_value,
                    'size': symbol_size,
                    'type': symbol_type,
                    'bind': symbol_bind,
                    'visibility': symbol_visibility,
                    'location': symbol_location
                }

                #Add the symbol to the object file in symbol table
                symbol_table[previous_object_file_name][symbol_name] = {}
                symbol_table[previous_object_file_name][symbol_name] = symbol_attributes

                #Update the symbol for checking overlapping in the future
                checked_symbols.append(symbol_name)

            elif len(line_parts) == 7: #Valid symbol entry without symbol name
                symbol_index = int(line_parts[0].split(':')[0])
                symbol_value = line_parts[1]
                symbol_size = line_parts[2]
                symbol_type = line_parts[3]
                symbol_bind = line_parts[4]
                symbol_visibility = line_parts[5]
                symbol_location = line_parts[6]
                symbol_name = 'blank' + str(symbol_index) #Assign blank name with index position

                symbol_attributes = {
                    'index': symbol_index,
                    'value': symbol_value,
                    'size': symbol_size,
                    'type': symbol_type,
                    'bind': symbol_bind,
                    'visibility': symbol_visibility,
                    'location': symbol_location
                }

                #Add the symbol attributes to the object file in symbol table
                symbol_table[previous_object_file_name][symbol_name] = {}
                symbol_table[previous_object_file_name][symbol_name] = symbol_attributes
            
            elif len(line_parts) == 9: #Valid symbol with additional PCS variant attribute
                symbol_index = int(line_parts[0].split(':')[0])
                symbol_value = line_parts[1]
                symbol_size = line_parts[2]
                symbol_type = line_parts[3]
                symbol_bind = line_parts[4]
                symbol_visibility = line_parts[5]
                symbol_pcs_variant = line_parts[6] # This attribute shows that the symbol has a different Procedure Call Standard (PCS) as compared to standard one
                symbol_location = line_parts[7]
                symbol_name = line_parts[8]

                #If symbol has overlapping, then simply append the index to the symbol name of the symbol
                if symbol_name in checked_symbols:
                    symbol_name = symbol_name + str(symbol_index)
                
                symbol_attributes = {
                    'index': symbol_index,
                    'value': symbol_value,
                    'size': symbol_size,
                    'type': symbol_type,
                    'bind': symbol_bind,
                    'visibility': symbol_visibility,
                    'location': symbol_location,
                    'special': symbol_pcs_variant # Indicate that this symbol has a different PCS variant
                }

                #Add the symbol attributes to the object file in symbol table
                symbol_table[previous_object_file_name][symbol_name] = {}
                symbol_table[previous_object_file_name][symbol_name] = symbol_attributes

                #Update the symbol for checking overlapping in the future
                checked_symbols.append(symbol_name)
            else:
                #If the line does not match the expected format, give the warning
                bb.warn("Unexpected symbol format in symbol table of %s at line: %s" % (file_path, line))
                pass

    return symbol_table

def __create_symbol_table(file_path, d):
    symbol_table = {}

    checked_symbols = []

    #Get READELF command
    readelf = d.getVar('READELF')

    #Get symbol table log
    symbol_table_log = subprocess.check_output([readelf, '-sW', file_path], stderr=subprocess.STDOUT).decode("utf-8")

    is_start_parsing = False

    #Extract only symbols in .symtab, .dynsym is ignored
    for line in symbol_table_log.splitlines():

        #Begin to parse the symbole table when .symtab is hit
        if '.symtab' in line:
            #Trigger the parsing for incoming lines
            is_start_parsing = True
            continue

        elif 'Num:' in line:
            #Ignore lines which contain 'Num:' as these lines are not symbol info
            continue

        elif is_start_parsing:
            #Split the current line into a list
            line_parts = line.split()

            #Add the symbol and its attributes to the symbol table
            if len(line_parts) == 8: #Valid symbol entry with symbol name
                symbol_index = int(line_parts[0].split(':')[0])
                symbol_value = line_parts[1]
                symbol_size = line_parts[2]
                symbol_type = line_parts[3]
                symbol_bind = line_parts[4]
                symbol_visibility = line_parts[5]
                symbol_location = line_parts[6]
                symbol_name = line_parts[7]

                #If symbol has overlapping, then simply append the index to the symbol name of the symbol
                if symbol_name in checked_symbols:
                    symbol_name = symbol_name + str(symbol_index)

                #Add the symbol to the symbol table
                symbol_table[symbol_name] = {
                    'index': symbol_index,
                    'value': symbol_value,
                    'size': symbol_size,
                    'type': symbol_type,
                    'bind': symbol_bind,
                    'visibility': symbol_visibility,
                    'location': symbol_location
                }

                #Update the symbol for checking overlapping in the future
                checked_symbols.append(symbol_name)

            elif len(line_parts) == 7: #Valid symbol entry without symbol name
                symbol_index = int(line_parts[0].split(':')[0])
                symbol_value = line_parts[1]
                symbol_size = line_parts[2]
                symbol_type = line_parts[3]
                symbol_bind = line_parts[4]
                symbol_visibility = line_parts[5]
                symbol_location = line_parts[6]
                symbol_name = 'blank' + str(symbol_index) #Assign blank name with index position

                #Add the symbol to the symbol table
                symbol_table[symbol_name] = {
                    'index': symbol_index,
                    'value': symbol_value,
                    'size': symbol_size,
                    'type': symbol_type,
                    'bind': symbol_bind,
                    'visibility': symbol_visibility,
                    'location': symbol_location
                }
            
            elif len(line_parts) == 9: #Valid symbol with additional PCS variant attribute
                symbol_index = int(line_parts[0].split(':')[0])
                symbol_value = line_parts[1]
                symbol_size = line_parts[2]
                symbol_type = line_parts[3]
                symbol_bind = line_parts[4]
                symbol_visibility = line_parts[5]
                symbol_pcs_variant = line_parts[6] # This attribute shows that the symbol has a different Procedure Call Standard (PCS) as compared to standard one
                symbol_location = line_parts[7]
                symbol_name = line_parts[8]

                #If symbol has overlapping, then simply append the index to the symbol name of the symbol
                if symbol_name in checked_symbols:
                    symbol_name = symbol_name + str(symbol_index)

                #Add the symbol to the symbol table
                symbol_table[symbol_name] = {
                    'index': symbol_index,
                    'value': symbol_value,
                    'size': symbol_size,
                    'type': symbol_type,
                    'bind': symbol_bind,
                    'visibility': symbol_visibility,
                    'location': symbol_location,
                    'special': symbol_pcs_variant # Indicate that this symbol has a different PCS variant
                }

                #Update the symbol for checking overlapping in the future
                checked_symbols.append(symbol_name)
            else:
                #If the line does not match the expected format, give the warning
                bb.warn("Unexpected symbol format in symbol table of %s at line: %s" % (file_path, line))
                continue

    return symbol_table

def __generate_weak_static_linked_libs(libs_to_compare,libs_to_be_compared,d):
    weak_static_linked_libs = []

    #For each file in libs_to_compare
    for file_to_compare in libs_to_compare:

        #Extract symbols of functions and variables with type FUNC/OBJECT, bind WEAK, visibility dont care, location is not UND
        file_to_compare_symbol_table = file_to_compare.get_symbol_table()
        symbols_to_compare = {}
        for symbol_name in file_to_compare_symbol_table.keys():
            if (file_to_compare_symbol_table[symbol_name]['type'] == 'FUNC' or file_to_compare_symbol_table[symbol_name]['type'] == 'OBJECT') and file_to_compare_symbol_table[symbol_name]['bind'] == 'WEAK' and file_to_compare_symbol_table[symbol_name]['location'] != 'UND':
                symbols_to_compare[symbol_name] = file_to_compare_symbol_table[symbol_name]
                
        #For each file in libs_to_be_compared
        for file_to_be_compared in libs_to_be_compared:

            #Check if the file is a static lib
            if isinstance(file_to_be_compared, StaticLib):

                file_to_be_compared_symbol_table = file_to_be_compared.get_symbol_table() #The file_to_be_compared_symbol_table is a dictionary of object files archived in the static lib

                 #If yes, for each object file in static lib
                for object_file_name in file_to_be_compared_symbol_table.keys():

                    is_weak_linking_found = False #Flag indicate that a weak symbol linking is found in this object file of the static lib under inspection

                    #Extract symbols of functions and data objects with type FUNC/OBJECT, bind WEAK, visibility dont care, location is not UND
                    object_file_symbols_to_be_compared = {}
                    for symbol_name in file_to_be_compared_symbol_table[object_file_name].keys():
                        if (file_to_be_compared_symbol_table[object_file_name][symbol_name]['type'] == 'FUNC' or file_to_be_compared_symbol_table[object_file_name][symbol_name]['type'] == 'OBJECT') and file_to_be_compared_symbol_table[object_file_name][symbol_name]['bind'] == 'WEAK' and file_to_be_compared_symbol_table[object_file_name][symbol_name]['location'] != 'UND':
                            object_file_symbols_to_be_compared[symbol_name] = file_to_be_compared_symbol_table[object_file_name][symbol_name]
                    
                    #Compare each symbol from symbols_to_compare to object_file_symbols_to_be_compared from the object file of the current static lib
                    for symbol_to_compare_name in symbols_to_compare.keys():

                        #If there is a symbol match
                        if symbol_to_compare_name in object_file_symbols_to_be_compared.keys():

                            #If the linking status of the corresponding static lib is already set
                            if file_to_be_compared.get_link_status() != '':
                                #Do nothing, by pass this static lib, we know for sure that this file might have some kinds of "strong linking" already
                                is_weak_linking_found = True
                                break
                            
                            #else if the linking status of the corresponding static lib is not set
                            elif file_to_be_compared.get_link_status() == '':
                                # Set linking status of the static lib to "weak static"
                                file_to_be_compared.set_link_status('weak static')

                                #Get file path list of libs in weak_static_linked_libs
                                weak_static_linked_libs_paths = [lib.get_path() for lib in weak_static_linked_libs]

                                # Add the current static lib to the weak_static_linked_libs if the current static lib is not already in the list
                                file_to_be_compared_path = file_to_be_compared.get_path()
                                if file_to_be_compared_path not in weak_static_linked_libs_paths:
                                    weak_static_linked_libs.append(file_to_be_compared)

                                #Go to next static lib
                                is_weak_linking_found = True
                                break

                    #If weak linking is found, break out to next static lib.
                    #A single sign of weak linking in an object file is enough to conclude linking status of the static lib
                    if is_weak_linking_found:
                        break

    return weak_static_linked_libs

def __generate_strong_static_linked_libs(libs_to_compare,libs_to_be_compared,d):
    strong_static_linked_libs = []

    #For each file in libs_to_compare
    for file_to_compare in libs_to_compare:

        #Creat list of previous strong linked symbols
        previous_strong_linked_symbols = {}

        #Extract symbols of functions and variables with type FUNC/OBJECT, bind GLOBAL, visibility dont care, location is not UND
        file_to_compare_symbol_table = file_to_compare.get_symbol_table()
        symbols_to_compare = {}
        for symbol_name in file_to_compare_symbol_table.keys():
            if (file_to_compare_symbol_table[symbol_name]['type'] == 'FUNC' or file_to_compare_symbol_table[symbol_name]['type'] == 'OBJECT') and file_to_compare_symbol_table[symbol_name]['bind'] == 'GLOBAL' and file_to_compare_symbol_table[symbol_name]['location'] != 'UND':
                symbols_to_compare[symbol_name] = file_to_compare_symbol_table[symbol_name]

        #For each file in libs_to_be_compared
        for file_to_be_compared in libs_to_be_compared:

            #Check if the file is a static lib
            if isinstance(file_to_be_compared, StaticLib):
                file_to_be_compared_symbol_table = file_to_be_compared.get_symbol_table() #The file_to_be_compared_symbol_table is a dictionary of object files archived in the static lib

                #If yes, for each object file in static lib
                for object_file_name in file_to_be_compared_symbol_table.keys():

                    is_strong_linking_found = False #Flag indicate that a strong symbol linking is found in this object file of the static lib under inspection

                    #Extract symbols of functions and data objects with type FUNC/OBJECT, bind not LOCAL, visibility dont care, location is not UND
                    object_file_symbols_to_be_compared = {}
                    for symbol_name in file_to_be_compared_symbol_table[object_file_name].keys():
                        if (file_to_be_compared_symbol_table[object_file_name][symbol_name]['type'] == 'FUNC' or file_to_be_compared_symbol_table[object_file_name][symbol_name]['type'] == 'OBJECT') and file_to_be_compared_symbol_table[object_file_name][symbol_name]['bind'] != 'LOCAL' and file_to_be_compared_symbol_table[object_file_name][symbol_name]['location'] != 'UND':
                            object_file_symbols_to_be_compared[symbol_name] = file_to_be_compared_symbol_table[object_file_name][symbol_name]

                    #Compare each symbol from symbols_to_compare to object_file_symbols_to_be_compared from the object file of the current static lib
                    for symbol_to_compare_name in symbols_to_compare.keys():

                        #If there is a symbol match
                        if symbol_to_compare_name in object_file_symbols_to_be_compared.keys():

                            #If the object file symbol is WEAK
                            if object_file_symbols_to_be_compared[symbol_to_compare_name]['bind'] == 'WEAK':
                                #Ignore it, no strong linking can happen with weak symbols
                                pass

                            #else if the object file symbol is in previous_strong_linked_symbols
                            elif symbol_to_compare_name in previous_strong_linked_symbols.keys():
                                #Get the duplicated strong symbols of the current static lib
                                file_to_be_compared_duplicate_symbols = file_to_be_compared.get_duplicate_linked_symbols()

                                #Get file path of the file to compare
                                file_to_compare_path = file_to_compare.get_path()

                                #Set linking status of the current static lib to "duplicate strong static"
                                file_to_be_compared.set_link_status('duplicate strong static')

                                #Add duplicate symbol to file_to_be_compared_duplicate_symbols
                                if symbol_to_compare_name not in file_to_be_compared_duplicate_symbols.keys():
                                    #If the duplicate symbol is not already recorded as duplicate symbol before, it is then created now for this lib
                                    file_to_be_compared_duplicate_symbols[symbol_to_compare_name] = {}
                                    file_to_be_compared_duplicate_symbols[symbol_to_compare_name]['reported_by'] = {}
                                else:
                                    #Do nothing, the symbol is already recorded before
                                    pass

                                #Add the file_to_compare which report this duplicate symbol and a list of files which have the same duplicate symbol
                                if file_to_compare_path not in file_to_be_compared_duplicate_symbols[symbol_to_compare_name]['reported_by'].keys():
                                    file_to_be_compared_duplicate_symbols[symbol_to_compare_name]['reported_by'][file_to_compare_path] = {}
                                    file_to_be_compared_duplicate_symbols[symbol_to_compare_name]['reported_by'][file_to_compare_path]['duplicate_files'] = previous_strong_linked_symbols[symbol_to_compare_name]
                                else:
                                    #If the file_to_compare is already recorded as reporting this duplicate symbol, do nothing to avoid overwriting
                                    pass

                                #Set linking status of all libs corresponding to the same strong symbol in previous_strong_linked_symbols to "duplicate strong static" and create the corresponding duplicate symbols also
                                for linked_lib in previous_strong_linked_symbols[symbol_to_compare_name].values():
                                    #Set linking status of the linked lib to "duplicate strong static"
                                    linked_lib.set_link_status('duplicate strong static')

                                    #Get the duplicate symbols of the linked lib
                                    linked_lib_duplicate_symbols = linked_lib.get_duplicate_linked_symbols()

                                    #The steps below are the same as steps above which used to create a list of duplicate symbols
                                    #We have to manually repeat these 2 steps to ensure that we are actually appending the new reporter to the  duplicate symbols of the linked lib
                                    #Setting the duplicate linked symbols using the method "set_duplicate_linked_symbols" is replacing the whole duplicate symbols of the linked lib, which is not what we want

                                    #Add the duplicate symbol to the linked lib
                                    if symbol_to_compare_name not in linked_lib_duplicate_symbols.keys():
                                        #If the duplicate symbol is not already recorded as duplicate symbol before, it is then created now for this lib
                                        linked_lib_duplicate_symbols[symbol_to_compare_name] = {}
                                        linked_lib_duplicate_symbols[symbol_to_compare_name]['reported_by'] = {}
                                    else:
                                        #Do nothing, the symbol is already recorded before
                                        pass

                                    #Add the file_to_compare which report this duplicate symbol and a list of files which have the same duplicate symbol
                                    if file_to_compare_path not in linked_lib_duplicate_symbols[symbol_to_compare_name]['reported_by'].keys():
                                        linked_lib_duplicate_symbols[symbol_to_compare_name]['reported_by'][file_to_compare_path] = {}
                                        linked_lib_duplicate_symbols[symbol_to_compare_name]['reported_by'][file_to_compare_path]['duplicate_files'] = previous_strong_linked_symbols[symbol_to_compare_name]
                                    else:
                                        #If the file_to_compare is already recorded as reporting this duplicate symbol, do nothing to avoid overwriting
                                        pass

                                #Add the current static lib to the corresponding symbol in previous_strong_linked_symbols also
                                previous_strong_linked_symbols[symbol_to_compare_name][file_to_be_compared.get_name()] = file_to_be_compared

                                #Get file path list of libs in strong_static_linked_libs
                                strong_static_linked_libs_paths = [lib.get_path() for lib in strong_static_linked_libs]

                                #Add the current static lib to the strong_static_linked_libs if the current static lib is not already in the list
                                file_to_be_compared_path = file_to_be_compared.get_path()
                                if file_to_be_compared_path not in strong_static_linked_libs_paths:
                                    strong_static_linked_libs.append(file_to_be_compared)

                                #Set the flag to indicate that strong linking is found
                                is_strong_linking_found = True

                                #Break out since there is no need to check for other symbols in symbols_to_compare
                                break

                            #else if the object file symbol is not WEAK and is not in previous_strong_linked_symbols
                            elif object_file_symbols_to_be_compared[symbol_to_compare_name]['bind'] != 'WEAK' and symbol_to_compare_name not in previous_strong_linked_symbols.keys():
                                #Set linking status of the static lib to "strong static"
                                file_to_be_compared.set_link_status('strong static')

                                #Add the symbol to previous_strong_linked_symbols with reference to the corresponding static lib
                                previous_strong_linked_symbols[symbol_to_compare_name] = {}
                                previous_strong_linked_symbols[symbol_to_compare_name][file_to_be_compared.get_name()] = file_to_be_compared

                                #Get file path list of libs in strong_static_linked_libs
                                strong_static_linked_libs_paths = [lib.get_path() for lib in strong_static_linked_libs]

                                #Add the current static lib to the strong_static_linked_libs if the current static lib is not already in the list
                                file_to_be_compared_path = file_to_be_compared.get_path()
                                if file_to_be_compared_path not in strong_static_linked_libs_paths:
                                    strong_static_linked_libs.append(file_to_be_compared)

                                #Set the flag to indicate that strong linking is found
                                is_strong_linking_found = True

                                #Break out since there is no need to check for other symbols in symbols_to_compare
                                break
                        else:
                            #If there is no symbol match, do nothing
                            pass
                    

                    #If strong linking is found, break the loop to avoid checking other object files in the static lib
                    if is_strong_linking_found:
                        break

            #Check if the file is an object file
            elif isinstance(file_to_be_compared, ObjectFile):
                
                #Get symbol table of the object file
                file_to_be_compared_symbol_table = file_to_be_compared.get_symbol_table()

                #Extract symbols of functions and data objects with type FUNC/OBJECT, bind not LOCAL, visibility dont care, location is not UND
                object_file_symbols_to_be_compared = {}
                for symbol_name in file_to_be_compared_symbol_table.keys():
                    if (file_to_be_compared_symbol_table[symbol_name]['type'] == 'FUNC' or file_to_be_compared_symbol_table[symbol_name]['type'] == 'OBJECT') and file_to_be_compared_symbol_table[symbol_name]['bind'] != 'LOCAL' and file_to_be_compared_symbol_table[symbol_name]['location'] != 'UND':
                        object_file_symbols_to_be_compared[symbol_name] = file_to_be_compared_symbol_table[symbol_name]
                
                #Compare each symbol from symbols_to_compare to object_file_symbols_to_be_compared from the object file of the current static lib
                for symbol_to_compare_name in symbols_to_compare.keys():
                    
                    #If there is a symbol match
                    if symbol_to_compare_name in object_file_symbols_to_be_compared.keys():
                        
                        #If the object file symbol is WEAK
                        if object_file_symbols_to_be_compared[symbol_to_compare_name]['bind'] == 'WEAK':
                            #Ignore it, no strong linking can happen with weak symbols
                            pass

                        #else if the object file symbol is in previous_strong_linked_symbols
                        elif symbol_to_compare_name in previous_strong_linked_symbols.keys():
                            #Get the name of the file to be compared
                            file_to_be_compared_name = file_to_be_compared.get_name()

                            #Get the duplicated strong symbols of the current object file
                            file_to_be_compared_duplicate_symbols = file_to_be_compared.get_duplicate_linked_symbols()

                            #Get file path of the file to compare
                            file_to_compare_path = file_to_compare.get_path()
                            
                            #Set linking status of the current object file to "duplicate strong static"
                            file_to_be_compared.set_link_status('duplicate strong static')

                            
                            #Add duplicate symbol to file_to_be_compared_duplicate_symbols
                            if symbol_to_compare_name not in file_to_be_compared_duplicate_symbols.keys():
                                #If the duplicate symbol is not already recorded as duplicate symbol before, it is then created now for this lib
                                file_to_be_compared_duplicate_symbols[symbol_to_compare_name] = {}
                                file_to_be_compared_duplicate_symbols[symbol_to_compare_name]['reported_by'] = {}
                            else:
                                #Do nothing, the symbol is already recorded before
                                pass

                            #Add the file_to_compare which report this duplicate symbol and a list of files which have the same duplicate symbol
                            if file_to_compare_path not in file_to_be_compared_duplicate_symbols[symbol_to_compare_name]['reported_by'].keys():
                                file_to_be_compared_duplicate_symbols[symbol_to_compare_name]['reported_by'][file_to_compare_path] = {}
                                file_to_be_compared_duplicate_symbols[symbol_to_compare_name]['reported_by'][file_to_compare_path]['duplicate_files'] = previous_strong_linked_symbols[symbol_to_compare_name]
                            else:
                                #If the file_to_compare is already recorded as reporting this duplicate symbol, do nothing to avoid overwriting
                                pass

                            #Set linking status of all linked files corresponding to the same strong symbol in previous_strong_linked_symbols to "duplicate strong static" and create the corresponding duplicate symbols also
                            for linked_file in previous_strong_linked_symbols[symbol_to_compare_name].values():
                                #Set linking status of the linked file to "duplicate strong static"
                                linked_file.set_link_status('duplicate strong static')

                                #Get the duplicate symbols of the linked file
                                linked_lib_duplicate_symbols = linked_file.get_duplicate_linked_symbols()

                                #The steps below are the same as steps above which used to create a list of duplicate symbols
                                #We have to manually repeat these 2 steps to ensure that we are actually appending the new reporter to the  duplicate symbols of the linked file
                                #Setting the duplicate linked symbols using the method "set_duplicate_linked_symbols" is replacing the whole duplicate symbols of the linked file, which is not what we want

                                #Add the duplicate symbol to the linked file
                                if symbol_to_compare_name not in linked_lib_duplicate_symbols.keys():
                                    #If the duplicate symbol is not already recorded as duplicate symbol before, it is then created now for this file
                                    linked_lib_duplicate_symbols[symbol_to_compare_name] = {}
                                    linked_lib_duplicate_symbols[symbol_to_compare_name]['reported_by'] = {}
                                else:
                                    #Do nothing, the symbol is already recorded before
                                    pass

                                #Add the file_to_compare which report this duplicate symbol and a list of files which have the same duplicate symbol
                                if file_to_compare_path not in linked_lib_duplicate_symbols[symbol_to_compare_name]['reported_by'].keys():
                                    linked_lib_duplicate_symbols[symbol_to_compare_name]['reported_by'][file_to_compare_path] = {}
                                    linked_lib_duplicate_symbols[symbol_to_compare_name]['reported_by'][file_to_compare_path]['duplicate_files'] = previous_strong_linked_symbols[symbol_to_compare_name]
                                else:
                                    #If the file_to_compare is already recorded as reporting this duplicate symbol, do nothing to avoid overwriting
                                    pass

                            #Add the current object file to the corresponding symbol in previous_strong_linked_symbols also
                            previous_strong_linked_symbols[symbol_to_compare_name][file_to_be_compared_name] = file_to_be_compared

                            #Get file path list in strong_static_linked_libs
                            strong_static_linked_file_paths = [file.get_path() for file in strong_static_linked_libs]

                            #Add the current object file to the strong_static_linked_libs if the current object file is not already in the list
                            file_to_be_compared_path = file_to_be_compared.get_path()
                            if file_to_be_compared_path not in strong_static_linked_file_paths:
                                strong_static_linked_libs.append(file_to_be_compared)
                            
                            #Break out since there is no need to check for other symbols in symbols_to_compare
                            break

                        #else if the object file symbol is not WEAK and is not in previous_strong_linked_symbols
                        elif object_file_symbols_to_be_compared[symbol_to_compare_name]['bind'] != 'WEAK' and symbol_to_compare_name not in previous_strong_linked_symbols.keys():
                            file_to_be_compared_name = file_to_be_compared.get_name()

                            #Set linking status of the static lib to "strong static"
                            file_to_be_compared.set_link_status('strong static')

                            #Add the symbol to previous_strong_linked_symbols with reference to the corresponding static lib
                            previous_strong_linked_symbols[symbol_to_compare_name] = {}
                            previous_strong_linked_symbols[symbol_to_compare_name][file_to_be_compared_name] = file_to_be_compared

                            #Get file path list in strong_static_linked_libs
                            strong_static_linked_file_paths = [file.get_path() for file in strong_static_linked_libs]

                            #Add the current object file to the strong_static_linked_libs if the current object file is not already in the list
                            file_to_be_compared_path = file_to_be_compared.get_path()
                            if file_to_be_compared_path not in strong_static_linked_file_paths:
                                strong_static_linked_libs.append(file_to_be_compared)

                            #Break out since there is no need to check for other symbols in symbols_to_compare
                            break
            else:
                #TODO: Handle other types of files, simply extract symbols of functions and variables of the file
                pass
            
    return strong_static_linked_libs


def __generate_linked_libs(libs_to_compare,libs_to_be_compared,d):
    #Get a list of libs with strong static linking
    strong_static_linked_libs = __generate_strong_static_linked_libs(libs_to_compare, libs_to_be_compared, d)

    #Get a list of libs with weak static linking (libs with strong static linking are excluded in this list)
    weak_static_linked_libs = __generate_weak_static_linked_libs(libs_to_compare, libs_to_be_compared, d)

    #Combine 2 lists into a list of linked libs
    static_linked_libs = strong_static_linked_libs + weak_static_linked_libs

    #Return the linked libs
    return static_linked_libs

def __generate_list_of_shared_libs_and_executables(file_paths=[], d=None):
    elf_readable_list = []

    #Loop through each file path in the package
    for file_path in file_paths:

        #Extract file attributes
        file_name = os.path.basename(file_path)
        file_extension = os.path.splitext(file_name)[1]

        #Inquiry the properties of the file
        (path,file_type) = is_elf(file_path)

        #Check if file is a shared lib
        if (file_type & 1) and (file_type & 8):

            #Create a symbol table for the file
            symbol_table = __create_symbol_table(file_path, d)
            
            #Create shared lib object
            shared_lib = SharedLib(path=file_path, name=file_name, extension=file_extension,
                                   fromPackage='', fromRecipe='',
                                   license='', symbolTable=symbol_table, strongLinkedSymbols={},weakLinkedSymbols={},duplicateLinkedSymbols={})

            #Add shared lib object to the list
            elf_readable_list.append(shared_lib)

        #Check if file is an ELF executable
        elif (file_type & 1) and (file_type & 4):

            #Create a symbol table for the file
            symbol_table = __create_symbol_table(file_path, d)

            #Create executable object
            executable = Executable(path=file_path, name=file_name, extension=file_extension,
                                    fromPackage='', fromRecipe='',
                                    license='', symbolTable=symbol_table, strongLinkedSymbols={},weakLinkedSymbols={},duplicateLinkedSymbols={})

            #Add file to the list
            elf_readable_list.append(executable)
        
        #Check if file is an object file
        elif (file_type & 1) and (file_type & 32):

            #Create a symbol table for the file
            symbol_table = __create_symbol_table(file_path, d)

            #Create object file object
            object_file = ObjectFile(path=file_path, name=file_name, extension=file_extension,
                                     fromPackage='', fromRecipe='',
                                     license='', symbolTable=symbol_table, strongLinkedSymbols={},weakLinkedSymbols={},duplicateLinkedSymbols={})

            #Add object file object to the list
            elf_readable_list.append(object_file)
        
        #Check if file is an AR archive (static library)
        elif (file_type & 64):

            #Create a symbol table for the file
            symbol_table = __create_symbol_table_static_lib(file_path, d)

            #Create static lib object
            static_lib = StaticLib(path=file_path, name=file_name, extension=file_extension,
                                   fromPackage='', fromRecipe='',
                                   license='', symbolTable=symbol_table, strongLinkedSymbols={},weakLinkedSymbols={},duplicateLinkedSymbols={})

            #Add static lib object to the list
            elf_readable_list.append(static_lib)
        
        else:
            #If file is not a shared lib or executable, ignore it
            pass
    
    return elf_readable_list

def __generate_list_of_statically_linked_libs(pkgfiles, d):
    recipe_sysroot = d.getVar('RECIPE_SYSROOT')
    linked_libs = []

    #Look for debug package in the recipe
    debug_pkg_name = None
    for pkg in pkgfiles.keys():
        if pkg.endswith('-dbg'):
            debug_pkg_name = pkg
            break
    
    if debug_pkg_name is not None:
        #Create a list of shared libs and executables located inside the debug package of the recipe
        debug_file_paths = pkgfiles[debug_pkg_name]

        debug_shared_libs_and_executables = __generate_list_of_shared_libs_and_executables(file_paths=debug_file_paths, d=d)

        #Add from package, from recipe and license information to each shared lib and executable
        __add_info_from_pkgdata_dir(debug_shared_libs_and_executables, d)

        #Create a list of static libs located in the RECIPE_SYSROOT directory
        recipe_sysroot_file_paths = []
        for root, dirs, files in os.walk(recipe_sysroot):
            for file in files:
                if file.endswith('.a') or file.endswith('.o'):
                    recipe_sysroot_file_paths.append(os.path.join(root, file))
        
        recipe_sysroot_static_libs_and_executables = __generate_list_of_shared_libs_and_executables(file_paths=recipe_sysroot_file_paths, d=d)

        #Add from package, from recipe and license information to each static lib and executable
        __add_info_from_pkgdata_dir(recipe_sysroot_static_libs_and_executables, d)

        #Perform the symbol compare to identify which static libs might be linked and set the linking status accordingly
        linked_libs = __generate_linked_libs(debug_shared_libs_and_executables, recipe_sysroot_static_libs_and_executables, d)

        #Return the linked libs
        return linked_libs
        
    else:
        #There is nothing to check in this case since we do not have package that provide debugging info
        return linked_libs

def generate_static_linking_list(pkgfiles, d):
    #Create list of linked static libs
    linked_static_libs = __generate_list_of_statically_linked_libs(pkgfiles, d)

    #Create list of linked header files

    #Combine the two lists into a list of static linked files
    pass