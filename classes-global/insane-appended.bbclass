def package_qa_check_license_compliance(pkgs, pkgfiles, d):
    from lib.linked_lib_generator import StaticLinkedLibsGenerator
    from lib.linked_lib_generator import DynamicLinkedLibsGenerator
    from foss_compliance_checker import FossComplianceChecker
    
    #Get list of statically linked files in the current recipe
    static_linking_files = StaticLinkedLibsGenerator(pkgfiles, d).generate()

    #Get list of dynamically linked files in the current recipe
    dynamic_linking_files = DynamicLinkedLibsGenerator(pkgfiles, d).generate()

    #Combine both static and dynamic linked files
    linked_libs = static_linking_files + dynamic_linking_files

    #Apply the FOSS license check algorithm on list of linked libs
    FossComplianceChecker(linked_files=linked_libs, d=d).run()

python do_package_qa:append() {
    #Get switch value to turn on/off the license checker tool
    is_license_check_on = d.getVar("ENABLE_LICENSE_CHECK_TOOL")

    #Check if the license checker tool is enabled
    if is_license_check_on == '1':
        #Execute license check compliance
        package_qa_check_license_compliance(pkgs=packages, pkgfiles=pkgfiles,d=d)
    else:
        #Do nothing
        pass
}