from foss.foss_config import *


def foss_license_compliance_check(linked_files, d):
    #Check if the list of linked files is not empty
    if linked_files != []:

        layer_dir = d.getVar('LAYERDIR_WS')
        foss_config_dir = os.path.join(layer_dir, 'tool-config')
        recipe_config_dir = os.path.join(layer_dir, 'recipe-config')
        log_dir = os.path.join(layer_dir, 'logs')
        recipe_name = d.getVar('PN')

        #Path to foss config file, recipe config file and log file
        foss_config_file_path = os.path.join(foss_config_dir, 'foss.yaml')
        recipe_config_file_path = os.path.join(recipe_config_dir, recipe_name + '.yaml')
        log_file_path = os.path.join(log_dir, recipe_name + '.log')

        #Create the FOSS config object and recipe config object
        foss_config_object = FossConfig()
        recipe_config_object = RecipeConfig()

        #Check if foss configuration exists and loads it
        if os.path.exists(foss_config_file_path):
            #Load the foss configuration file if it is created before
            foss_config_object.load_config_from_yaml_file(foss_config_file_path)
        else:
            #Create and load the foss configuration file if it is not created before
            foss_config_object.save_config_to_yaml_file(foss_config_file_path)
            foss_config_object.load_config_from_yaml_file(foss_config_file_path)

        #Check if recipe configuration exists and loads it
        if os.path.exists(recipe_config_file_path):
            #Load the recipe configuration file if it is created before
            recipe_config_object.load_config_from_yaml_file(recipe_config_file_path)
        else:
            #Create and load the recipe configuration file if it is not created before
            recipe_config_object.save_config_to_yaml_file(recipe_config_file_path)
            recipe_config_object.load_config_from_yaml_file(recipe_config_file_path)

        #Extract essential settings from foss configuration
        strict_licenses = foss_config_object.get_strict_licenses()
        half_strict_licenses = foss_config_object.get_half_strict_licenses()
        open_licenses = foss_config_object.get_open_licenses()

        approved_files = recipe_config_object.get_approved_files()
        files_to_be_checked = recipe_config_object.get_files_to_be_checked()

        approved_file_paths = [file.get_path() for file in approved_files]
        files_to_be_checked_paths = [file.get_path() for file in files_to_be_checked]

        #
        #Perform the FOSS license compliance check on the linked files
        #

        for linked_file in linked_files:

            #Get the file license
            file_license = linked_file.get_license()

            #Get the file linking status
            file_linking_status = linked_file.get_link_status()

            #Get the file extension
            file_extension = linked_file.get_extension()

            #Check if the file is in list of approved files
            if linked_file.get_path() in approved_file_paths:

                #Get instance of the correpsonding approved file
                for file in approved_files:
                    if file.get_path() == linked_file.get_path():
                        target_approved_file = file
                        break

                #Check if the checksum of the file is changed as compared to the previous run
                if target_approved_file.get_checksum() != linked_file.get_checksum():
                    #If the checksum is changed, log a warning and add file to the list of files to be checked again
                    recipe_config_object.add_message("Warning: File [%s] has changed since last run. Previous checksum: [%s], Current checksum: [%s]. Please help to check and update the approved file list accordingly." % (linked_file.get_path(), target_approved_file.get_checksum(), linked_file.get_checksum()))
                else:
                    #If the checksum is not changed, do nothing
                    continue

            #else if the file is in the list of files to be checked
            elif linked_file.get_path() in files_to_be_checked_paths:
                #Check if the file has strict license
                if file_license in strict_licenses:
                    #Check if the file has linking status of "strong static", "duplicate strong static", "weak static", "dynamic" or file is a header file
                    if file_linking_status == "strong static":
                        recipe_config_object.add_message("Warning: File [%s] has strict license [%s] with strong linking status [%s]. Please help to check and add this file to approved list accordingly." % (linked_file.get_path(), file_license, file_linking_status))

                    elif file_linking_status == "duplicate strong static":
                        recipe_config_object.add_message("Warning: File [%s] has strict license [%s] with duplicate linking status [%s]. Please help to check if file is really linked to the build and add it to approved list accordingly." % (linked_file.get_path(), file_license, file_linking_status))

                    elif file_linking_status == "weak static":
                        recipe_config_object.add_message("Warning: File [%s] has strict license [%s] with weak linking status [%s]. Please help to check if file is really linked to the build and add this file to approved list accordingly." % (linked_file.get_path(), file_license, file_linking_status))

                    elif file_linking_status == "dynamic":
                        recipe_config_object.add_message("Warning: File [%s] has strict license [%s] with linking status [%s]. Please help to check and add this file to approved list accordingly." % (linked_file.get_path(), file_license, file_linking_status))

                    elif file_extension == ".h":
                        recipe_config_object.add_message("Warning: File [%s] has strict license [%s]  and is a header file. Please help to check if this file is included in your build and add this file to approved list accordingly." % (linked_file.get_path(), file_license))
                    
                    else:
                        recipe_config_object.add_message("Warning: File [%s] has strict license [%s] but linking status is unknown. Please help to check and add this file to approved list accordingly." % (linked_file.get_path(), file_license))

                #Check if the file has half-strict license
                elif file_license in half_strict_licenses:
                    #Check if the file has linking status of "strong static", "duplicate strong static", "weak static" or file is a header file
                    if file_linking_status == "strong static":
                        recipe_config_object.add_message("Warning: File [%s] has half strict license [%s] with strong linking status [%s]. Please help to check and add this file to approved list accordingly." % (linked_file.get_path(), file_license, file_linking_status))

                    elif file_linking_status == "duplicate strong static":
                        recipe_config_object.add_message("Warning: File [%s] has half strict license [%s] with duplicate linking status [%s]. Please help to check if file is really linked to the build and add it to approved list accordingly." % (linked_file.get_path(), file_license, file_linking_status))

                    elif file_linking_status == "weak static":
                        recipe_config_object.add_message("Warning: File [%s] has half strict license [%s] with weak linking status [%s]. Please help to check if file is really linked to the build and add this file to approved list accordingly." % (linked_file.get_path(), file_license, file_linking_status))

                    elif file_extension == ".h":
                        recipe_config_object.add_message("Warning: File [%s] has half strict license [%s]  and is a header file. Please help to check if this file is included in your build and add this file to approved list accordingly." % (linked_file.get_path(), file_license))

                    else:
                        recipe_config_object.add_message("Warning: File [%s] has half strict license [%s] but linking status is unknown. Please help to check and add this file to approved list accordingly." % (linked_file.get_path(), file_license))
                else:
                    #Log a warning that the file has unknown license
                    recipe_config_object.add_message("Warning: File [%s] has unknown license [%s]. Please help to define it in the common FOSS configuration file." % (linked_file.get_path(), file_license))

            #else if the file is not yet in the list of files to be checked and not in the list of approved files (normally the first run or new recipe added)
            elif linked_file.get_path() not in approved_file_paths and linked_file.get_path() not in files_to_be_checked_paths:

                #Check if the file has strict license
                if file_license in strict_licenses:
                    #Check if the file has linking status of "strong static", "duplicate strong static", "weak static", "dynamic" or file is a header file
                    if file_linking_status == "strong static":
                        recipe_config_object.add_message("Warning: File [%s] has strict license [%s] with strong linking status [%s]. Please help to check and add this file to approved list accordingly." % (linked_file.get_path(), file_license, file_linking_status))
                        recipe_config_object.add_file_to_be_checked(linked_file)

                    elif file_linking_status == "duplicate strong static":
                        recipe_config_object.add_message("Warning: File [%s] has strict license [%s] with duplicate linking status [%s]. Please help to check if file is really linked to the build and add it to approved list accordingly." % (linked_file.get_path(), file_license, file_linking_status))
                        recipe_config_object.add_file_to_be_checked(linked_file)

                    elif file_linking_status == "weak static":
                        recipe_config_object.add_message("Warning: File [%s] has strict license [%s] with weak linking status [%s]. Please help to check if file is really linked to the build and add this file to approved list accordingly." % (linked_file.get_path(), file_license, file_linking_status))
                        recipe_config_object.add_file_to_be_checked(linked_file)

                    elif file_linking_status == "dynamic":
                        recipe_config_object.add_message("Warning: File [%s] has strict license [%s] with linking status [%s]. Please help to check and add this file to approved list accordingly." % (linked_file.get_path(), file_license, file_linking_status))
                        recipe_config_object.add_file_to_be_checked(linked_file)

                    elif file_extension == ".h":
                        recipe_config_object.add_message("Warning: File [%s] has strict license [%s]  and is a header file. Please help to check if this file is included in your build and add this file to approved list accordingly." % (linked_file.get_path(), file_license))
                        recipe_config_object.add_file_to_be_checked(linked_file)
                    
                    else:
                        recipe_config_object.add_message("Warning: File [%s] has strict license [%s] but linking status is unknown. Please help to check and add this file to approved list accordingly." % (linked_file.get_path(), file_license))
                        recipe_config_object.add_file_to_be_checked(linked_file)

                #Check if the file has half-strict license
                elif file_license in half_strict_licenses:
                    #Check if the file has linking status of "strong static", "duplicate strong static", "weak static" or file is a header file
                    if file_linking_status == "strong static":
                        recipe_config_object.add_message("Warning: File [%s] has half strict license [%s] with strong linking status [%s]. Please help to check and add this file to approved list accordingly." % (linked_file.get_path(), file_license, file_linking_status))
                        recipe_config_object.add_file_to_be_checked(linked_file)

                    elif file_linking_status == "duplicate strong static":
                        recipe_config_object.add_message("Warning: File [%s] has half strict license [%s] with duplicate linking status [%s]. Please help to check if file is really linked to the build and add it to approved list accordingly." % (linked_file.get_path(), file_license, file_linking_status))
                        recipe_config_object.add_file_to_be_checked(linked_file)

                    elif file_linking_status == "weak static":
                        recipe_config_object.add_message("Warning: File [%s] has half strict license [%s] with weak linking status [%s]. Please help to check if file is really linked to the build and add this file to approved list accordingly." % (linked_file.get_path(), file_license, file_linking_status))
                        recipe_config_object.add_file_to_be_checked(linked_file)

                    elif file_extension == ".h":
                        recipe_config_object.add_message("Warning: File [%s] has half strict license [%s]  and is a header file. Please help to check if this file is included in your build and add this file to approved list accordingly." % (linked_file.get_path(), file_license))
                        recipe_config_object.add_file_to_be_checked(linked_file)

                    else:
                        recipe_config_object.add_message("Warning: File [%s] has half strict license [%s] but linking status is unknown. Please help to check and add this file to approved list accordingly." % (linked_file.get_path(), file_license))
                        recipe_config_object.add_file_to_be_checked(linked_file)

                #Check if the file has open license
                elif file_license in open_licenses:
                    #Ignore the file, there is nothing to check
                    pass
                
                else:
                    #Log a warning that the file has unknown license
                    recipe_config_object.add_message("Warning: File [%s] has unknown license [%s]. Please help to define it in the common FOSS configuration file." % (linked_file.get_path(), file_license))
                    recipe_config_object.add_file_to_be_checked(linked_file)
            else:
                #Log fatal error and stop the process
                bb.fatal("FOSS license compliance check failed: File [%s] is not defined. This should not happen." % (linked_file.get_path()))
                pass

        #Check if there are any warning messages in the message buffer of the recipe
        if not recipe_config_object.is_message_buffer_empty():

            #Save messages to the log file and save files to be checked to the recipe config file
            recipe_config_object.save_messages_to_log_file(log_file_path)
            recipe_config_object.save_config_to_yaml_file(recipe_config_file_path)

            #Warn user that there might be risk of compliance break in the recipe
            bb.warn("FOSS license compliance check completed with warnings. Please check the log file: %s" % log_file_path)
            bb.warn("Please help to adjust settings in recipe config file: %s" % recipe_config_file_path)
        else:
            #Write to log file of the build that there is no issue found
            bb.note("FOSS license compliance check completed successfully. No issues found.")

            #Remove log file since it is not needed anymore, leaving it will cause confusion
            if os.path.exists(log_file_path):
                os.remove(log_file_path)
            else:
                #Do nothing, there is nothing to remove
                pass
    else:
        bb.note("FOSS license compliance check completed successfully. No linked files found. Nothing to check.")