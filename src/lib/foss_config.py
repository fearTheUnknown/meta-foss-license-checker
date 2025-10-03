import yaml

class FossConfig:
    """Class to create project level configuration for FOSS Compliance Check Algorithm
    """    
    def __init__(self):
        self.m_strong_copyleft_licenses = [] # Very strict with both static and dynamic linking
        self.m_weak_copylef_licenses = [] # Strict with static linking, but not with dynamic linking
        self.m_non_copylef_licenses = [] # No issues with any kinds of linking at all

    def load_config_from_yaml_file(self, file_path):
        #Get file path of the config file
        config_file_path = file_path

        #Read config from yaml file
        with open(config_file_path, 'r') as config_fd:
            config_data = yaml.load(config_fd, Loader=yaml.Loader)

        #Extract the config data
        self.m_strong_copyleft_licenses = config_data.m_strong_copyleft_licenses
        self.m_weak_copylef_licenses = config_data.m_weak_copylef_licenses
        self.m_non_copylef_licenses = config_data.m_non_copylef_licenses

    def save_config_to_yaml_file(self, file_path):
        #Get file path of the config file
        config_file_path = file_path

        #Pack data to be saved
        config_data = FossConfig()
        config_data.m_strong_copyleft_licenses = self.m_strong_copyleft_licenses
        config_data.m_weak_copylef_licenses = self.m_weak_copylef_licenses
        config_data.m_non_copylef_licenses = self.m_non_copylef_licenses

        #Write config to yaml file
        with open(config_file_path, 'w') as config_fd:
            yaml.dump(config_data, config_fd, sort_keys=False)

    def get_strict_licenses(self):
        return self.m_strong_copyleft_licenses
    
    def get_half_strict_licenses(self):
        return self.m_weak_copylef_licenses
    
    def get_open_licenses(self):
        return self.m_non_copylef_licenses

class RecipeConfig:
    """Class to create a recipe configuration in FOSS Compliance Check Algorithm
    """    
    def __init__(self):
        self.m_approved_files = []
        self.m_files_to_be_checked = []
        self.m_messages = []
    
    def __getstate__(self):
        """Override the serializer to exclude serialization of "m_messages" attribute. Code copy from https://stackoverflow.com/questions/49905287/how-to-ignore-attributes-when-using-yaml-dump
        """        
        state = self.__dict__.copy()
        del state['m_messages']
        return state

    def load_config_from_yaml_file(self, file_path):
        #Get file path of the config file
        config_file_path = file_path

        #Read config from yaml file
        with open(config_file_path, 'r') as config_fd:
            config_data = yaml.load(config_fd, Loader=yaml.Loader)

        #Extract the config data
        self.m_approved_files = config_data.m_approved_files
        self.m_files_to_be_checked = config_data.m_files_to_be_checked

    def save_config_to_yaml_file(self, file_path):
        #Get file path of the config file
        config_file_path = file_path

        #Pack data to be saved
        config_data = RecipeConfig()
        config_data.m_approved_files = self.m_approved_files
        config_data.m_files_to_be_checked = self.m_files_to_be_checked

        #Write config to yaml file
        with open(config_file_path, 'w') as config_fd:
            yaml.dump(config_data, config_fd, sort_keys=False)

    def save_messages_to_log_file(self, file_path):
        #Get the log file path
        log_file_path = file_path

        #Write all messages to the log file
        with open(log_file_path, 'w') as log_fd:
            for message in self.m_messages:
                log_fd.write(message + '\n')
    
    def flush_messages(self):
        #Clear the list of messages
        self.m_messages.clear()
    
    def add_message(self, message):
        #Add a message to the list of messages
        self.m_messages.append(message)
    
    def add_file_to_be_checked(self, file):
        #Add file that need to be checked further
        self.m_files_to_be_checked.append(file)
    
    def get_approved_files(self):
        return self.m_approved_files
    
    def get_files_to_be_checked(self):
        return self.m_files_to_be_checked
    
    def set_approved_files(self, approved_files):
        self.m_approved_files = approved_files
    
    def set_files_to_be_checked(self, files_to_be_checked):
        self.m_files_to_be_checked = files_to_be_checked
    
    def is_message_buffer_empty(self):
        #Check if the message buffer is empty
        if self.m_messages == []:
            return True
        else:
            return False
