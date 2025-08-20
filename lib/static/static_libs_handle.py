from utils import *
import os

class StaticLinkedLibsGenerator:
    def __init__(self, pkgfiles, d):
        self.m_pkgfiles = pkgfiles
        self.m_d = d
    
    def generate(self):
        #Create list of linked static libs
        linked_static_libs = self.__generate_list_of_statically_linked_libs(self.m_pkgfiles, self.m_d)

        #Create list of linked header files
        linked_header_files = self.__generate_list_of_statically_linked_header_files(self.m_d)

        #Combine the two lists into a list of static linked files
        static_linked_files = linked_static_libs + linked_header_files
        
        return static_linked_files

    def __generate_weak_static_linked_libs(self, libs_to_compare, libs_to_be_compared, d):
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

                elif isinstance(file_to_be_compared, ObjectFile):

                    #Get the symbol table of the object file
                    file_to_be_compared_symbol_table = file_to_be_compared.get_symbol_table()

                    #Extract symbols of functions and data objects with type FUNC/OBJECT, bind WEAK, visibility dont care, location is not UND
                    object_file_symbols_to_be_compared = {}
                    for symbol_name in file_to_be_compared_symbol_table.keys():
                        if (file_to_be_compared_symbol_table[symbol_name]['type'] == 'FUNC' or file_to_be_compared_symbol_table[symbol_name]['type'] == 'OBJECT') and file_to_be_compared_symbol_table[symbol_name]['bind'] == 'WEAK' and file_to_be_compared_symbol_table[symbol_name]['location'] != 'UND':
                            object_file_symbols_to_be_compared[symbol_name] = file_to_be_compared_symbol_table[symbol_name]
                    
                    #Compare each symbol from symbols_to_compare to object_file_symbols_to_be_compared from the object file of the current static lib
                    for symbol_to_compare_name in symbols_to_compare.keys():

                        #If there is a symbol match
                        if symbol_to_compare_name in object_file_symbols_to_be_compared.keys():

                            #If the linking status of the corresponding statically linked file is already set
                            if file_to_be_compared.get_link_status() != '':
                                #Do nothing, by pass this object file, we know for sure that this file might have some kinds of "strong linking" already
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
                                
                                #Go to next object file
                                break

        return weak_static_linked_libs

    def __generate_strong_static_linked_libs(self, libs_to_compare, libs_to_be_compared, d):
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
        
        #Refine the duplicate symbols of strong static linked libs
        duplicate_strong_static_linked_libs = [lib for lib in strong_static_linked_libs if lib.get_duplicate_linked_symbols() != {}]

        for duplicate_strong_static_linked_lib in duplicate_strong_static_linked_libs:
            #Get duplicated symbols
            duplicated_symbols = duplicate_strong_static_linked_lib.get_duplicate_linked_symbols()

            #For each duplicated symbol
            for symbol_name in duplicated_symbols.keys():
                #Get the list of files which report this duplicated symbol
                report_files = duplicated_symbols[symbol_name]['reported_by']

                #For each file which report this symbol
                for report_file_name in report_files.keys():
                    #Convert duplicate_files from real object into a list of file paths
                    report_files[report_file_name]['duplicate_files'] = [file.get_path() for file in report_files[report_file_name]['duplicate_files'].values()]

                
        return strong_static_linked_libs


    def __generate_linked_libs(self, libs_to_compare, libs_to_be_compared, d):
        #Get a list of libs with strong static linking
        strong_static_linked_libs = self.__generate_strong_static_linked_libs(libs_to_compare, libs_to_be_compared, d)

        #Get a list of libs with weak static linking (libs with strong static linking are excluded in this list)
        weak_static_linked_libs = self.__generate_weak_static_linked_libs(libs_to_compare, libs_to_be_compared, d)

        #Combine 2 lists into a list of linked libs
        static_linked_libs = strong_static_linked_libs + weak_static_linked_libs

        #Clear symbol table of all static linked libs
        for lib in static_linked_libs:
            lib.set_symbol_table(symbolTable={})

        #Return the linked libs
        return static_linked_libs

    def __generate_list_of_statically_linked_libs(self, pkgfiles, d):
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

            debug_shared_libs_and_executables = generate_list_of_shared_libs_and_executables(file_paths=debug_file_paths, d=d)

            #Add from package, from recipe and license information to each shared lib and executable
            add_info_from_pkgdata_dir(debug_shared_libs_and_executables, d)

            #Create a list of static libs located in the RECIPE_SYSROOT directory
            recipe_sysroot_file_paths = []
            for root, dirs, files in os.walk(recipe_sysroot):
                for file in files:
                    if file.endswith('.a') or file.endswith('.o'):
                        recipe_sysroot_file_paths.append(os.path.join(root, file))
            
            recipe_sysroot_static_libs_and_executables = generate_list_of_shared_libs_and_executables(file_paths=recipe_sysroot_file_paths, d=d)

            #Add from package, from recipe and license information to each static lib and executable
            add_info_from_pkgdata_dir(recipe_sysroot_static_libs_and_executables, d)

            #Perform the symbol compare to identify which static libs might be linked and set the linking status accordingly
            linked_libs = self.__generate_linked_libs(debug_shared_libs_and_executables, recipe_sysroot_static_libs_and_executables, d)

            #Return the linked libs
            return linked_libs
            
        else:
            #There is nothing to check in this case since we do not have package that provide debugging info
            return linked_libs


    def __generate_list_of_statically_linked_header_files(self, d):
        recipe_sysroot = d.getVar('RECIPE_SYSROOT')

        #Create a list of header files located in the RECIPE_SYSROOT directory
        recipe_sysroot_file_paths = []
        for root, dirs, files in os.walk(recipe_sysroot):
            for file in files:
                if file.endswith('.h'):
                    recipe_sysroot_file_paths.append(os.path.join(root, file))
        
        #Generate a list of header files in the RECIPE_SYSROOT directory
        recipe_sysroot_header_files = generate_list_of_shared_libs_and_executables(file_paths=recipe_sysroot_file_paths, d=d)

        #Add from package, from recipe and license information to each header file
        add_info_from_pkgdata_dir(recipe_sysroot_header_files, d)

        return recipe_sysroot_header_files