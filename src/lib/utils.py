import subprocess
from lib.file import *
import json
import fnmatch
import oe.package
import hashlib

def explode_libs(s):

    lib_list = s.split()

    def remove_parentheses(s):
        while '(' in s and ')' in s:
            start = s.find('(')
            end = s.find(')', start)
            if end == -1:
                break
            s = s[:start] + s[end+1:]
        return s
    
    return_list = [remove_parentheses(lib) for lib in lib_list]

    return return_list

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

#Function code copied from https://www.geeksforgeeks.org/python/python-program-to-find-hash-of-file/
def compute_file_hash(file_path, algorithm='sha256'):
    """Compute the hash of a file using the specified algorithm."""
    hash_func = hashlib.new(algorithm)
    
    with open(file_path, 'rb') as file:
        # Read the file in chunks of 8192 bytes
        while chunk := file.read(8192):
            hash_func.update(chunk)
    
    return hash_func.hexdigest()

def find_path(filepath, d):

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

def convert_to_list_of_readable_object_files(file_paths=[], d=None):
    """Convert given file paths into Python objects for easy access and processing.

    Keyword Arguments:
        file_paths -- List of file paths to be converted into objects (default: {[]})
        d -- datastore of Yocto build system (default: {None})

    Returns:
        List of readable objects in Python of the given list of file paths
    """    
    
    #Initialize object file list
    readable_object_file_list = []

    #Loop through each file path in the package
    for file_path in file_paths:

        #Extract file attributes
        file_name = os.path.basename(file_path)
        file_name_parts = file_name.split('.',1)
        file_extension = '.' + file_name_parts[1] if len(file_name_parts) > 1 else ''

        #Calculate checksum of the file
        checksum = compute_file_hash(file_path, 'sha256')

        #Inquiry the properties of the file
        (path,file_type) = is_elf(file_path)

        #Check if file is a shared lib
        if (file_type & 1) and (file_type & 8):

            #Create a symbol table for the file
            symbol_table = __create_symbol_table(file_path, d)
            
            #Create shared lib object
            shared_lib = SharedLib(path=file_path, name=file_name, extension=file_extension,
                                   fromPackage='', fromRecipe='',
                                   license='', symbolTable=symbol_table, strongLinkedSymbols={},weakLinkedSymbols={},duplicateLinkedSymbols={}, checksum=checksum)

            #Add shared lib object to the list
            readable_object_file_list.append(shared_lib)

        #Check if file is an ELF executable
        elif (file_type & 1) and (file_type & 4):

            #Create a symbol table for the file
            symbol_table = __create_symbol_table(file_path, d)

            #Create executable object
            executable = Executable(path=file_path, name=file_name, extension=file_extension,
                                    fromPackage='', fromRecipe='',
                                    license='', symbolTable=symbol_table, strongLinkedSymbols={},weakLinkedSymbols={},duplicateLinkedSymbols={}, checksum=checksum)

            #Add file to the list
            readable_object_file_list.append(executable)
        
        #Check if file is an object file
        elif (file_type & 1) and (file_type & 32):

            #Create a symbol table for the file
            symbol_table = __create_symbol_table(file_path, d)

            #Create object file object
            object_file = ObjectFile(path=file_path, name=file_name, extension=file_extension,
                                     fromPackage='', fromRecipe='',
                                     license='', symbolTable=symbol_table, strongLinkedSymbols={},weakLinkedSymbols={},duplicateLinkedSymbols={}, checksum=checksum)

            #Add object file object to the list
            readable_object_file_list.append(object_file)
        
        #Check if file is an AR archive (static library)
        elif (file_type & 64):

            #Create a symbol table for the file
            symbol_table = __create_symbol_table_static_lib(file_path, d)

            #Create static lib object
            static_lib = StaticLib(path=file_path, name=file_name, extension=file_extension,
                                   fromPackage='', fromRecipe='',
                                   license='', symbolTable=symbol_table, strongLinkedSymbols={},weakLinkedSymbols={},duplicateLinkedSymbols={}, checksum=checksum)

            #Add static lib object to the list
            readable_object_file_list.append(static_lib)
        
        #Check if file is a C header file
        elif file_type == 0 and file_extension == '.h':

            #Create header file
            header_file = HeaderFile(path=file_path, name=file_name, extension=file_extension,
                                     fromPackage='', fromRecipe='',
                                     license='', symbolTable={}, strongLinkedSymbols={}, weakLinkedSymbols={}, duplicateLinkedSymbols={}, checksum=checksum)
            
            #Add header file to the list
            readable_object_file_list.append(header_file)
        
        else:
            #If file is not among predefined file types above, ignore it
            pass

    #Add meta info to list of generated object files
    add_info_from_pkgdata_dir(files=readable_object_file_list, d=d)

    return readable_object_file_list


def add_info_from_pkgdata_dir(files, d):

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
            (package_name, file_path_in_filesystem) = find_path(root_filesystem_path_to_file, d)

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
            (package_name, file_path_in_filesystem) = find_path(root_filesystem_path_to_file, d)

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