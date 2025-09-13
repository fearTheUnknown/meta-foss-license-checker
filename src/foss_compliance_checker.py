from lib.foss_config import *

class FossComplianceChecker:
    """FOSS Compliance Check Algorithm
    """    
    def __init__(self, linked_files,d):
        self.m_linked_files = linked_files
        self.m_d = d

        #Set up initial directories
        self.m_layer_dir = self.m_d.getVar('LAYERDIR_WS')
        self.m_foss_config_dir = os.path.join(self.m_layer_dir, 'tool-config')
        self.m_recipe_config_dir = os.path.join(self.m_layer_dir, 'recipes-config')
        self.log_dir = os.path.join(self.m_layer_dir, 'logs')
        self.m_recipe_name = self.m_d.getVar('PN')

        #Path to foss config file, recipe config file and log file
        self.m_foss_config_file_path = os.path.join(self.m_foss_config_dir, 'foss.yaml')
        self.m_recipe_config_file_path = os.path.join(self.m_recipe_config_dir, self.m_recipe_name + '.yaml')
        self.m_log_file_path = os.path.join(self.log_dir, self.m_recipe_name + '.log')

        #Create the FOSS config object and recipe config object
        self.m_foss_config_object = FossConfig()
        self.m_recipe_config_object = RecipeConfig()

        #License setting
        self.m_strict_licenses = None
        self.m_half_strict_licenses = None
        self.m_open_licenses = None

        #White list
        self.m_approved_files = None
        self.m_files_to_be_checked = None
        self.m_approved_file_paths = None
        self.m_files_to_be_checked_paths = None

    def run(self):
        """Load all configs and execute the license check algorithm
        """        
        #Check if the list of linked files is not empty
        if self.m_linked_files != []:

            #Load configurations and setup their attributes
            self.__load_config()

            #Perform the FOSS license compliance check on the linked files
            self.__run_license_check()

            #Show result
            self.__show_result()

        else:
            bb.note("FOSS license compliance check completed successfully. No linked files found. Nothing to check.")
    
    def __load_config(self):
        """Load and extract attributes from foss config and recipe config
        """        

        #Check if foss configuration exists and loads it
        if os.path.exists(self.m_foss_config_file_path):
            #Load the foss configuration file if it is created before
            self.m_foss_config_object.load_config_from_yaml_file(self.m_foss_config_file_path)
        else:
            #Create and load the foss configuration file if it is not created before
            self.m_foss_config_object.save_config_to_yaml_file(self.m_foss_config_file_path)
            self.m_foss_config_object.load_config_from_yaml_file(self.m_foss_config_file_path)

        #Check if recipe configuration exists and loads it
        if os.path.exists(self.m_recipe_config_file_path):
            #Load the recipe configuration file if it is created before
            self.m_recipe_config_object.load_config_from_yaml_file(self.m_recipe_config_file_path)
        else:
            #Create and load the recipe configuration file if it is not created before
            self.m_recipe_config_object.save_config_to_yaml_file(self.m_recipe_config_file_path)
            self.m_recipe_config_object.load_config_from_yaml_file(self.m_recipe_config_file_path)
        
        #Extract essential settings from foss configuration
        self.m_strict_licenses = self.m_foss_config_object.get_strict_licenses()
        self.m_half_strict_licenses = self.m_foss_config_object.get_half_strict_licenses()
        self.m_open_licenses = self.m_foss_config_object.get_open_licenses()

        #Extract white list
        self.m_approved_files = self.m_recipe_config_object.get_approved_files()
        self.m_files_to_be_checked = self.m_recipe_config_object.get_files_to_be_checked()
        self.m_approved_file_paths = [file.get_path() for file in self.m_approved_files]
        self.m_files_to_be_checked_paths = [file.get_path() for file in self.m_files_to_be_checked]
    
    def __show_result(self):
        """Write logs and forward warning messages to console
        """        
        #Check if there are any warning messages in the message buffer of the recipe
        if not self.m_recipe_config_object.is_message_buffer_empty():

            #Save messages to the log file and save files to be checked to the recipe config file
            self.m_recipe_config_object.save_messages_to_log_file(self.m_log_file_path)
            self.m_recipe_config_object.save_config_to_yaml_file(self.m_recipe_config_file_path)

            #Warn user that there might be risk of compliance break in the recipe
            bb.warn("FOSS license compliance check completed with warnings. Please check the log file: %s" % self.m_log_file_path)
            bb.warn("Please help to adjust settings in recipe config file: %s" % self.m_recipe_config_file_path)
        else:
            #Write to log file of the build that there is no issue found
            bb.note("FOSS license compliance check completed successfully. No issues found.")

            #Remove log file since it is not needed anymore, leaving it will cause confusion
            if os.path.exists(self.m_log_file_path):
                os.remove(self.m_log_file_path)
            else:
                #Do nothing, there is nothing to remove
                pass
    
    def __run_license_check(self):
        """Execute all license checks on the recipe
        """        

        self.__check_linked_file_change()
        self.__check_previous_concerning_linked_files()
        self.__check_new_linked_files()
    
    def __check_linked_file_change(self):
        """Check if there are changes in approved linked files as compared to the moment when they are approved
        """        

        for linked_file in self.m_linked_files:

            #Check if the file is in list of approved files
            if linked_file.get_path() in self.m_approved_file_paths:

                #Get instance of the correpsonding approved file
                for file in self.m_approved_files:
                    if file.get_path() == linked_file.get_path():
                        target_approved_file = file
                        break

                #Check if the checksum of the file is changed as compared to the previous run
                if target_approved_file.get_checksum() != linked_file.get_checksum():
                    #If the checksum is changed, log a warning and add file to the list of files to be checked again
                    self.m_recipe_config_object.add_message("Warning: File [%s] has changed since last run. Previous checksum: [%s], Current checksum: [%s]. Please help to check and update the approved file list accordingly." % (linked_file.get_path(), target_approved_file.get_checksum(), linked_file.get_checksum()))
                else:
                    #If the checksum is not changed, do nothing
                    continue
            else:
                #Do nothing
                pass
    
    def __check_previous_concerning_linked_files(self):
        """Check if previously reported linked files are properly handled
        """        

        for linked_file in self.m_linked_files:
            #Get the file license
            file_license = linked_file.get_license()

            #Get the file linking status
            file_linking_status = linked_file.get_link_status()

            #Get the file extension
            file_extension = linked_file.get_extension()
            
            #Check if the linked file needs to be checked by the user
            if linked_file.get_path() in self.m_files_to_be_checked_paths:
                #Check if the file has strict license
                if file_license in self.m_strict_licenses:
                    #Check if the file has linking status of "strong static", "duplicate strong static", "weak static", "dynamic" or file is a header file
                    if file_linking_status == "strong static":
                        self.m_recipe_config_object.add_message("Warning: File [%s] has strict license [%s] with strong linking status [%s]. Please help to check and add this file to approved list accordingly." % (linked_file.get_path(), file_license, file_linking_status))

                    elif file_linking_status == "duplicate strong static":
                        self.m_recipe_config_object.add_message("Warning: File [%s] has strict license [%s] with duplicate linking status [%s]. Please help to check if file is really linked to the build and add it to approved list accordingly." % (linked_file.get_path(), file_license, file_linking_status))

                    elif file_linking_status == "weak static":
                        self.m_recipe_config_object.add_message("Warning: File [%s] has strict license [%s] with weak linking status [%s]. Please help to check if file is really linked to the build and add this file to approved list accordingly." % (linked_file.get_path(), file_license, file_linking_status))

                    elif file_linking_status == "dynamic":
                        self.m_recipe_config_object.add_message("Warning: File [%s] has strict license [%s] with linking status [%s]. Please help to check and add this file to approved list accordingly." % (linked_file.get_path(), file_license, file_linking_status))

                    elif file_extension == ".h":
                        self.m_recipe_config_object.add_message("Warning: File [%s] has strict license [%s]  and is a header file. Please help to check if this file is included in your build and add this file to approved list accordingly." % (linked_file.get_path(), file_license))
                    
                    else:
                        self.m_recipe_config_object.add_message("Warning: File [%s] has strict license [%s] but linking status is unknown. Please help to check and add this file to approved list accordingly." % (linked_file.get_path(), file_license))

                #Check if the file has half-strict license
                elif file_license in self.m_half_strict_licenses:
                    #Check if the file has linking status of "strong static", "duplicate strong static", "weak static" or file is a header file
                    if file_linking_status == "strong static":
                        self.m_recipe_config_object.add_message("Warning: File [%s] has half strict license [%s] with strong linking status [%s]. Please help to check and add this file to approved list accordingly." % (linked_file.get_path(), file_license, file_linking_status))

                    elif file_linking_status == "duplicate strong static":
                        self.m_recipe_config_object.add_message("Warning: File [%s] has half strict license [%s] with duplicate linking status [%s]. Please help to check if file is really linked to the build and add it to approved list accordingly." % (linked_file.get_path(), file_license, file_linking_status))

                    elif file_linking_status == "weak static":
                        self.m_recipe_config_object.add_message("Warning: File [%s] has half strict license [%s] with weak linking status [%s]. Please help to check if file is really linked to the build and add this file to approved list accordingly." % (linked_file.get_path(), file_license, file_linking_status))

                    elif file_extension == ".h":
                        self.m_recipe_config_object.add_message("Warning: File [%s] has half strict license [%s]  and is a header file. Please help to check if this file is included in your build and add this file to approved list accordingly." % (linked_file.get_path(), file_license))

                    else:
                        self.m_recipe_config_object.add_message("Warning: File [%s] has half strict license [%s] but linking status is unknown. Please help to check and add this file to approved list accordingly." % (linked_file.get_path(), file_license))
                else:
                    #Log a warning that the file has unknown license
                    self.m_recipe_config_object.add_message("Warning: File [%s] has unknown license [%s]. Please help to define it in the common FOSS configuration file." % (linked_file.get_path(), file_license))
            else:
                #Do nothing
                pass
    
    def __check_new_linked_files(self):
        """Check and report recently created linked files
        """        

        for linked_file in self.m_linked_files:
            #Get the file license
            file_license = linked_file.get_license()

            #Get the file linking status
            file_linking_status = linked_file.get_link_status()

            #Get the file extension
            file_extension = linked_file.get_extension()

            #Check if the linked file is a new one
            if linked_file.get_path() not in self.m_approved_file_paths and linked_file.get_path() not in self.m_files_to_be_checked_paths:

                #Check if the file has strict license
                if file_license in self.m_strict_licenses:
                    #Check if the file has linking status of "strong static", "duplicate strong static", "weak static", "dynamic" or file is a header file
                    if file_linking_status == "strong static":
                        self.m_recipe_config_object.add_message("Warning: File [%s] has strict license [%s] with strong linking status [%s]. Please help to check and add this file to approved list accordingly." % (linked_file.get_path(), file_license, file_linking_status))
                        self.m_recipe_config_object.add_file_to_be_checked(linked_file)

                    elif file_linking_status == "duplicate strong static":
                        self.m_recipe_config_object.add_message("Warning: File [%s] has strict license [%s] with duplicate linking status [%s]. Please help to check if file is really linked to the build and add it to approved list accordingly." % (linked_file.get_path(), file_license, file_linking_status))
                        self.m_recipe_config_object.add_file_to_be_checked(linked_file)

                    elif file_linking_status == "weak static":
                        self.m_recipe_config_object.add_message("Warning: File [%s] has strict license [%s] with weak linking status [%s]. Please help to check if file is really linked to the build and add this file to approved list accordingly." % (linked_file.get_path(), file_license, file_linking_status))
                        self.m_recipe_config_object.add_file_to_be_checked(linked_file)

                    elif file_linking_status == "dynamic":
                        self.m_recipe_config_object.add_message("Warning: File [%s] has strict license [%s] with linking status [%s]. Please help to check and add this file to approved list accordingly." % (linked_file.get_path(), file_license, file_linking_status))
                        self.m_recipe_config_object.add_file_to_be_checked(linked_file)

                    elif file_extension == ".h":
                        self.m_recipe_config_object.add_message("Warning: File [%s] has strict license [%s]  and is a header file. Please help to check if this file is included in your build and add this file to approved list accordingly." % (linked_file.get_path(), file_license))
                        self.m_recipe_config_object.add_file_to_be_checked(linked_file)
                    
                    else:
                        self.m_recipe_config_object.add_message("Warning: File [%s] has strict license [%s] but linking status is unknown. Please help to check and add this file to approved list accordingly." % (linked_file.get_path(), file_license))
                        self.m_recipe_config_object.add_file_to_be_checked(linked_file)

                #Check if the file has half-strict license
                elif file_license in self.m_half_strict_licenses:
                    #Check if the file has linking status of "strong static", "duplicate strong static", "weak static" or file is a header file
                    if file_linking_status == "strong static":
                        self.m_recipe_config_object.add_message("Warning: File [%s] has half strict license [%s] with strong linking status [%s]. Please help to check and add this file to approved list accordingly." % (linked_file.get_path(), file_license, file_linking_status))
                        self.m_recipe_config_object.add_file_to_be_checked(linked_file)

                    elif file_linking_status == "duplicate strong static":
                        self.m_recipe_config_object.add_message("Warning: File [%s] has half strict license [%s] with duplicate linking status [%s]. Please help to check if file is really linked to the build and add it to approved list accordingly." % (linked_file.get_path(), file_license, file_linking_status))
                        self.m_recipe_config_object.add_file_to_be_checked(linked_file)

                    elif file_linking_status == "weak static":
                        self.m_recipe_config_object.add_message("Warning: File [%s] has half strict license [%s] with weak linking status [%s]. Please help to check if file is really linked to the build and add this file to approved list accordingly." % (linked_file.get_path(), file_license, file_linking_status))
                        self.m_recipe_config_object.add_file_to_be_checked(linked_file)

                    elif file_extension == ".h":
                        self.m_recipe_config_object.add_message("Warning: File [%s] has half strict license [%s]  and is a header file. Please help to check if this file is included in your build and add this file to approved list accordingly." % (linked_file.get_path(), file_license))
                        self.m_recipe_config_object.add_file_to_be_checked(linked_file)

                    else:
                        self.m_recipe_config_object.add_message("Warning: File [%s] has half strict license [%s] but linking status is unknown. Please help to check and add this file to approved list accordingly." % (linked_file.get_path(), file_license))
                        self.m_recipe_config_object.add_file_to_be_checked(linked_file)

                #Check if the file has open license
                elif file_license in self.m_open_licenses:
                    #Ignore the file, there is nothing to check
                    pass
                
                else:
                    #Log a warning that the file has unknown license
                    self.m_recipe_config_object.add_message("Warning: File [%s] has unknown license [%s]. Please help to define it in the common FOSS configuration file." % (linked_file.get_path(), file_license))
                    self.m_recipe_config_object.add_file_to_be_checked(linked_file)
            else:
                #Do nothing
                pass