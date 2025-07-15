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

def recursively_add_dependent_packages(parent_package=None, linked_packages={}, common_packages={}, d=None):

    shlibs_dir = d.getVar('SHLIBSDIRS')
    pkg_data_dir = d.getVar('PKGDATA_DIR')

    for linked_package in linked_packages.keys():

        #Check if the linked package is not already created before
        if linked_package not in common_packages.keys():

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

            for package_file_path in package_file_paths:
                #Open the corresponding package file
                if os.access(package_file_path, os.R_OK):
                    with open(package_file_path, 'r') as package_file_fd:
                        package_file_lines = package_file_fd.readlines()
                else:
                    bb.fatal("Package file cannot be read: %s" % package_file_path)
                
                #Create all attributes of the package
                linked_packages[linked_package]['depends_on_packages']= {}
                linked_packages[linked_package]['license'] = []
                linked_packages[linked_package]['linked_libs'] = {}
                linked_packages[linked_package]['name'] = linked_package
                linked_packages[linked_package]['end'] = False

                #Create all extracted attributes
                extracted_licenses = []
                extracted_rdepends = []
                extracted_linked_libs = []
                extracted_provided_libs = []

                for line in package_file_lines:
                    #Add the license
                    if 'LICENSE' == line.split(':')[0]:
                        splitted_license_entry = line.split(':')
                        
                        #Check if the LICENSE contains 2 or 3 parts separated by ':'
                        if len(splitted_license_entry) == 3:
                            license_name = line.split(':')[2]

                        elif len(splitted_license_entry) == 2:
                            license_name = line.split(':')[1]

                        else:
                            bb.error("Undefined LICENSE entry format in package file: %s" % package_file_path)
                        
                        #Add the license name to the extracted license list
                        extracted_licenses.append(license_name.strip())
                    
                    #Add the depends attribute based on RDEPENDS of the package file
                    elif 'RDEPENDS' == line.split(':')[0]:
                        #Get list of dependent packages
                        rdepend_packages_raw = line.split(':')[2]
                        rdepend_packages = bb.utils.explode_deps(rdepend_packages_raw)

                        #Set list of dependent packages to its corresponding extracted attribute
                        extracted_rdepends = rdepend_packages
                    
                    #Add all shared libs which the current package is depending on
                    elif 'FILERDEPENDS' == line.split(':')[0]:
                        #Record all of linked libs
                        raw_linked_libs = line.split(':')[3]
                        list_of_linked_libs_without_version_info = explode_libs(raw_linked_libs)
                        extracted_linked_libs.extend(list_of_linked_libs_without_version_info)
                    
                    #Add all provided libs which the current package is providing
                    elif 'FILERPROVIDESFLIST' == line.split(':')[0]:
                        #Record all of provided libs
                        raw_provided_libs = line.split(':')[2]
                        list_of_provided_lib_paths = raw_provided_libs.split()
                        extracted_provided_libs = [os.path.basename(provided_lib_path) for provided_lib_path in list_of_provided_lib_paths]
                
                #Add the extracted licenses to the existing 'license' attribute
                linked_packages[linked_package]['license'] = extracted_licenses

                #With each dependent package in the extracted dependent packages, create an empty dictionary with package name as the key
                for rdepend_package in extracted_rdepends:
                    linked_packages[linked_package]['depends_on_packages'][rdepend_package] = {}
                
                #With each linked lib in the extracted linked libs, create an dictionary with linked lib name as the key
                non_duplicate_extracted_linked_libs = list(set(extracted_linked_libs))
                for linked_lib in non_duplicate_extracted_linked_libs:

                    linked_packages[linked_package]['linked_libs'][linked_lib] = {}

                    #Add linking status
                    if len(linked_lib.split('.')) > 1:
                        lib_extension = linked_lib.split('.')[1]
                        if lib_extension == 'so':
                            linked_packages[linked_package]['linked_libs'][linked_lib]['linking_status'] = 'dynamic'
                        elif lib_extension == 'a':
                            linked_packages[linked_package]['linked_libs'][linked_lib]['linking_status'] = 'static'
                        else:
                            linked_packages[linked_package]['linked_libs'][linked_lib]['linking_status'] = 'unknown'
                    else:
                        linked_packages[linked_package]['linked_libs'][linked_lib]['linking_status'] = 'unknown'

                    #TODO: Add path to the lib file
                
                if parent_package is not None:
                    #Check which linked lib of the parent package is provided by the current package
                    parent_package_linked_libs = parent_package['linked_libs'].keys()

                    for parent_linked_lib in parent_package_linked_libs:
                        for extracted_provided_lib in extracted_provided_libs:
                            #IF the parent linked lib is provided by the current package
                            if parent_linked_lib in extracted_provided_lib:
                                #Set reference of the parent linked lib to the current package
                                parent_package['linked_libs'][parent_linked_lib]['provided_by'] = {}
                                parent_package['linked_libs'][parent_linked_lib]['provided_by'][linked_package] = linked_packages[linked_package]
                            else:
                                #Do nothing, the current package does not provide the corresponding parent linked lib
                                pass
                
                #Update the created package into common packages
                common_packages[linked_package] = linked_packages[linked_package]

                extracted_rdepends_str = ' '.join(extracted_rdepends)
                bb.note("Package [%s] depends on packages [%s]" % (linked_package, extracted_rdepends_str))

                #Check to decide whether to recursively add dependent packages deep down in the dependency tree
                if linked_packages[linked_package]['depends_on_packages'] != {}:
                    #Go down the dependency tree with each dependent package
                    __recursively_add_dependent_packages(parent_package=linked_packages[linked_package], linked_packages=linked_packages[linked_package]['depends_on_packages'], common_packages=common_packages, d=d)
                else:
                    #Do nothing, this linked package does not depend on any other packages
                    pass

        else:
            #Create empty attributes for the overlapped linked package
            linked_packages[linked_package]['depends_on_packages'] = {}
            linked_packages[linked_package]['license'] = []
            linked_packages[linked_package]['linked_libs'] = {}
            linked_packages[linked_package]['name'] = linked_package
            linked_packages[linked_package]['end'] = True # This attribute indicates that this is the end of this branch in the dependency tree

            #Set reference of the overlapped linked package to its corresponding package in the common package pool
            linked_packages[linked_package]['depends_on_packages'] = common_packages[linked_package]['depends_on_packages']
            linked_packages[linked_package]['license'] = common_packages[linked_package]['license']
            linked_packages[linked_package]['linked_libs'] = common_packages[linked_package]['linked_libs']