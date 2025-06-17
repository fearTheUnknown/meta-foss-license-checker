def process_staticlibs(pkgfiles, d):
    import subprocess

    nm_command = d.getVar('NM')

    #Get a list of debug files generated in <recipe_name>-dbg of the current recipe
    debug_pkg_name = d.getVar('PN') + '-dbg'
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
