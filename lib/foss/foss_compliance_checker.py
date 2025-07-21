from foss.foss_config import *


def foss_license_compliance_check(linked_files, d):
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
        foss_config_object.load_config_from_yaml_file(foss_config_file_path)
    else:
        foss_config_object.save_config_to_yaml_file(foss_config_file_path)
        foss_config_object.load_config_from_yaml_file(foss_config_file_path)

    #Check if recipe configuration exists and loads it
    if os.path.exists(recipe_config_file_path):
        recipe_config_object.load_config_from_yaml_file(recipe_config_file_path)
    else:
        recipe_config_object.save_config_to_yaml_file(recipe_config_file_path)
        recipe_config_object.load_config_from_yaml_file(recipe_config_file_path)

    #Extract essential settings from foss configuration

    #Perform the FOSS license compliance check on the linked files

    #Save the warnings of compliance break into a log file

    #Warn user that there might be risk of compliance break in the recipe