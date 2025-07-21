from utils import *
from pathlib import Path

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

def __generate_linked_shared_lib_names(pkgfiles, d):
    shlibs_dir = d.getVar('SHLIBSDIRS')
    pkg_data_dir = d.getVar('PKGDATA_DIR')

    #Create a list of all linked libs of all packages
    linked_libs = []

    #Loop through each package in the current recipe
    for linked_package in pkgfiles.keys():

        #Create a list of file paths
        package_file_paths = []
    
        #Check for file with the same package name in PKGDATA_DIR/runtime
        if os.path.exists(os.path.join(pkg_data_dir,'runtime',linked_package)):
            #Get the found file path
            found_file_path = os.path.join(pkg_data_dir,'runtime',linked_package)

            #Add the found file path to list of file paths
            package_file_paths.append(found_file_path)

        #Check for if linked package is a directory which contains symbolic links
        elif os.path.exists(os.path.join(pkg_data_dir,'runtime-rprovides',linked_package)):
            #Get the package directory path
            package_dir_path = os.path.join(pkg_data_dir,'runtime-rprovides',linked_package)

            #Check for all items in the package directory
            for file in os.listdir(package_dir_path):

                file_path = os.path.join(package_dir_path, file)

                #Check if the file path is a symbolic link
                if os.path.islink(file_path):
                    #Add symbolic link path to the list of file paths
                    package_file_paths.append(file_path)

                #Check if the item is a file
                elif os.path.isfile(file_path):

                    #Add file path to the list of file paths
                    package_file_paths.append(file_path)
                else:
                    bb.warn("The following entity is not a file or symbolic link: %s" % file_path)
                    bb.warn ("Package dependency tree may not be valid for linked package: %s" % linked_package)

        else:
            bb.fatal("Package file not found for linked package: %s" % linked_package)
        
        #Linked libs in all package file paths
        package_linked_libs = []

        #Read each package file and extract the essential info
        for package_file_path in package_file_paths:
            #Open the corresponding package file
            if os.access(package_file_path, os.R_OK):
                with open(package_file_path, 'r') as package_file_fd:
                    package_file_lines = package_file_fd.readlines()
            else:
                bb.fatal("Package file cannot be read: %s" % package_file_path)

            #Create all extracted attributes
            extracted_linked_libs = []

            for line in package_file_lines:
                               
                #Add all shared libs which the current package is depending on
                if 'FILERDEPENDS' == line.split(':')[0]:
                    #Record all of linked libs
                    raw_linked_libs = line.split(':')[3]
                    list_of_linked_libs_without_version_info = explode_libs(raw_linked_libs)
                    extracted_linked_libs.extend(list_of_linked_libs_without_version_info)
            
            #Create a list of non duplicate linked libs
            non_duplicate_extracted_linked_libs = list(set(extracted_linked_libs))

            #Create a list of shared linked libs only
            extracted_shared_linked_libs = [lib for lib in non_duplicate_extracted_linked_libs if '.so' in lib]

            #Add the shared linked libs to the package linked libs
            package_linked_libs.extend(extracted_shared_linked_libs)
        
        #Add linked libs of the current package to the linked libs of all packages
        linked_libs.extend(package_linked_libs)
    
    #Filter the linked_libs to ensure no duplicate files
    linked_libs = list(set(linked_libs))
    
    return linked_libs

def generate_dynamic_linking_list(pkgfiles, d):

    recipe_sysroot = d.getVar('RECIPE_SYSROOT')

    #Get list of linked shared lib names which linked to packages of the recipe
    shared_lib_file_names = __generate_linked_shared_lib_names(pkgfiles, d)
    
    #Create a list of linked shared lib paths in the RECIPE_SYSROOT directory 
    recipe_sysroot_linked_shared_lib_paths = []
    for root, dirs, files in os.walk(recipe_sysroot):
        for file in files:
            if file in shared_lib_file_names:

                file_path = os.path.join(root, file)

                (path,file_type) = is_elf(file_path)
                
                #Check if the file path is really a shared library
                if file_type & 8:
                    #Add file path to the list of linked shared lib paths
                    recipe_sysroot_linked_shared_lib_paths.append(file_path)
                
                #Check if the file path is a symbolic link
                elif file_type == 0 and os.path.islink(file_path):
                    #Read real file path of the symbolic link
                    real_file_path = subprocess.check_output(['readlink', '-f', file_path], stderr=subprocess.STDOUT).decode("utf-8").rstrip()

                    (real_path, real_file_type) = is_elf(real_file_path)

                    #Check if the real file path is an ELF shared lib
                    if real_file_type & 8:
                        #Add real file path to the list of linked shared lib paths
                        recipe_sysroot_linked_shared_lib_paths.append(real_file_path)
                    else:
                        bb.warn("Symbolic link [%s] point to an invalid shared library [%s]. Please help to check" % (file_path, real_file_path))
                
                else:
                    bb.warn("Cannot detect file type of the shared lib: %s" % file_path)

    #Create a list of shared libs located in the RECIPE_SYSROOT
    recipe_sysroot_linked_shared_libs = generate_list_of_shared_libs_and_executables(file_paths=recipe_sysroot_linked_shared_lib_paths, d=d)

    #Add from package, from recipe and license information to each shared lib
    add_info_from_pkgdata_dir(recipe_sysroot_linked_shared_libs, d)

    #Set linking status of all shared libs to "dynamic"
    for lib in recipe_sysroot_linked_shared_libs:
        lib.set_link_status('dynamic')
    
    #Return the list of linked shared libs
    return recipe_sysroot_linked_shared_libs