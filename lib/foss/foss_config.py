import yaml

class FossConfig:
    def __init__(self):
        self.m_strict_licenses = [] # Very strict with both static and dynamic linking
        self.m_half_strict_licenses = [] # Strict with static linking, but not with dynamic linking
        self.m_open_licenses = [] # No issues with any kinds of linking at all

    def load_config_from_yaml_file(self, file_path):
        #Get file path of the config file
        config_file_path = file_path

        #Read config from yaml file
        with open(config_file_path, 'r') as config_fd:
            config_data = yaml.load(config_fd, Loader=yaml.Loader)

        #Extract the config data
        self.m_strict_licenses = config_data.m_strict_licenses
        self.m_half_strict_licenses = config_data.m_half_strict_licenses
        self.m_open_licenses = config_data.m_open_licenses

    def save_config_to_yaml_file(self, file_path):
        #Get file path of the config file
        config_file_path = file_path

        #Pack data to be saved
        config_data = FossConfig()
        config_data.m_strict_licenses = self.m_strict_licenses
        config_data.m_half_strict_licenses = self.m_half_strict_licenses
        config_data.m_open_licenses = self.m_open_licenses

        #Write config to yaml file
        with open(config_file_path, 'w') as config_fd:
            yaml.dump(config_data, config_fd, sort_keys=False)

    def get_strict_licenses(self):
        return self.m_strict_licenses
    
    def get_half_strict_licenses(self):
        return self.m_half_strict_licenses
    
    def get_open_licenses(self):
        return self.m_open_licenses

class RecipeConfig:

    def __init__(self):
        self.m_approved_files = []
        self.m_files_to_be_checked = []
        self.m_messages = []

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
