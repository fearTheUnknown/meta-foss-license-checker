from abc import ABC, abstractmethod

class File(ABC):
    def __init__(self, path='', name='', extension='', fromPackage='', fromRecipe='',license='', linkStatus = '', symbolTable={}):
        self.m_path = path
        self.m_name = name
        self.m_extension = extension
        self.m_fromPackage = fromPackage
        self.m_fromRecipe = fromRecipe
        self.m_license = license
        self.m_linkStatus = linkStatus
        self.m_symbolTable = symbolTable
    
    @abstractmethod
    def get_path(self):
        pass
    
    @abstractmethod
    def get_name(self):
        pass
    
    @abstractmethod
    def get_extension(self):
        pass
    
    @abstractmethod
    def get_from_package(self):
        pass
    
    @abstractmethod
    def get_from_recipe(self):
        pass
    
    @abstractmethod
    def get_license(self):
        pass
    
    @abstractmethod
    def get_link_status(self):
        pass

    @abstractmethod
    def get_symbol_table(self):
        pass





    @abstractmethod
    def set_path(self):
        pass
    
    @abstractmethod
    def set_name(self):
        pass
    
    @abstractmethod
    def set_extension(self):
        pass
    
    @abstractmethod
    def set_from_package(self):
        pass
    
    @abstractmethod
    def set_from_recipe(self):
        pass
    
    @abstractmethod
    def set_license(self):
        pass
    
    @abstractmethod
    def set_link_status(self):
        pass

    @abstractmethod
    def set_symbol_table(self):
        pass

class HeaderFile(File):
    def __init__(self, path='', name='', extension='', fromPackage='', fromRecipe='',license='', linkStatus = '', symbolTable={}):
        super().__init__(path=path, name=name, extension=extension, fromPackage=fromPackage, fromRecipe=fromRecipe, license=license, linkStatus=linkStatus, symbolTable=symbolTable)
    
    def get_path(self):
        return self.m_path
    
    def get_name(self):
        return self.m_name
    
    def get_extension(self):
        return self.m_extension
    
    def get_from_package(self):
        return self.m_fromPackage
    
    def get_from_recipe(self):
        return self.m_fromRecipe
    
    def get_license(self):
        return self.m_license
    
    def get_link_status(self):
        return self.m_linkStatus
    
    def get_symbol_table(self):
        return self.m_symbolTable

    def set_path(self, path):
        self.m_path = path
    
    def set_name(self, name):
        self.m_name = name
    
    def set_extension(self, extension):
        self.m_extension = extension
    
    def set_from_package(self, fromPackage):
        self.m_fromPackage = fromPackage
    
    def set_from_recipe(self, fromRecipe):
        self.m_fromRecipe = fromRecipe
    
    def set_license(self, license):
        self.m_license = license

    def set_link_status(self, linkStatus):
        self.m_linkStatus = linkStatus
    
    def set_symbol_table(self, symbolTable):
        self.m_symbolTable = symbolTable


class StaticLib(File):
    def __init__(self, path='', name='', extension='', fromPackage='', fromRecipe='',license='', linkStatus = '', symbolTable={}):
        super().__init__(path=path, name=name, extension=extension, fromPackage=fromPackage, fromRecipe=fromRecipe, license=license, linkStatus=linkStatus, symbolTable=symbolTable)
    
    def get_path(self):
        return self.m_path
    
    def get_name(self):
        return self.m_name
    
    def get_extension(self):
        return self.m_extension
    
    def get_from_package(self):
        return self.m_fromPackage
    
    def get_from_recipe(self):
        return self.m_fromRecipe
    
    def get_license(self):
        return self.m_license
    
    def get_link_status(self):
        return self.m_linkStatus
    
    def get_symbol_table(self):
        return self.m_symbolTable
    
    def set_path(self, path):
        self.m_path = path
    
    def set_name(self, name):
        self.m_name = name
    
    def set_extension(self, extension):
        self.m_extension = extension
    
    def set_from_package(self, fromPackage):
        self.m_fromPackage = fromPackage
    
    def set_from_recipe(self, fromRecipe):
        self.m_fromRecipe = fromRecipe
    
    def set_license(self, license):
        self.m_license = license

    def set_link_status(self, linkStatus):
        self.m_linkStatus = linkStatus
    
    def set_symbol_table(self, symbolTable):
        self.m_symbolTable = symbolTable

class SharedLib(File):
    def __init__(self, path='', name='', extension='', fromPackage='', fromRecipe='',license='', linkStatus = '', symbolTable={}):
        super().__init__(path=path, name=name, extension=extension, fromPackage=fromPackage, fromRecipe=fromRecipe, license=license, linkStatus=linkStatus, symbolTable=symbolTable)
    
    def get_path(self):
        return self.m_path
    
    def get_name(self):
        return self.m_name
    
    def get_extension(self):
        return self.m_extension
    
    def get_from_package(self):
        return self.m_fromPackage
    
    def get_from_recipe(self):
        return self.m_fromRecipe
    
    def get_license(self):
        return self.m_license
    
    def get_link_status(self):
        return self.m_linkStatus
    
    def get_symbol_table(self):
        return self.m_symbolTable
    
    def set_path(self, path):
        self.m_path = path
    
    def set_name(self, name):
        self.m_name = name
    
    def set_extension(self, extension):
        self.m_extension = extension
    
    def set_from_package(self, fromPackage):
        self.m_fromPackage = fromPackage
    
    def set_from_recipe(self, fromRecipe):
        self.m_fromRecipe = fromRecipe
    
    def set_license(self, license):
        self.m_license = license

    def set_link_status(self, linkStatus):
        self.m_linkStatus = linkStatus
    
    def set_symbol_table(self, symbolTable):
        self.m_symbolTable = symbolTable

class Executable(File):
    def __init__(self, path='', name='', extension='', fromPackage='', fromRecipe='',license='', linkStatus = '', symbolTable={}):
        super().__init__(path=path, name=name, extension=extension, fromPackage=fromPackage, fromRecipe=fromRecipe, license=license, linkStatus=linkStatus, symbolTable=symbolTable)
    
    def get_path(self):
        return self.m_path
    
    def get_name(self):
        return self.m_name
    
    def get_extension(self):
        return self.m_extension
    
    def get_from_package(self):
        return self.m_fromPackage
    
    def get_from_recipe(self):
        return self.m_fromRecipe
    
    def get_license(self):
        return self.m_license
    
    def get_link_status(self):
        return self.m_linkStatus
    
    def get_symbol_table(self):
        return self.m_symbolTable
    
    def set_path(self, path):
        self.m_path = path
    
    def set_name(self, name):
        self.m_name = name
    
    def set_extension(self, extension):
        self.m_extension = extension
    
    def set_from_package(self, fromPackage):
        self.m_fromPackage = fromPackage
    
    def set_from_recipe(self, fromRecipe):
        self.m_fromRecipe = fromRecipe
    
    def set_license(self, license):
        self.m_license = license

    def set_link_status(self, linkStatus):
        self.m_linkStatus = linkStatus
    
    def set_symbol_table(self, symbolTable):
        self.m_symbolTable = symbolTable


class ObjectFile(File):
    def __init__(self, path='', name='', extension='', fromPackage='', fromRecipe='',license='', linkStatus = '', symbolTable={}):
        super().__init__(path=path, name=name, extension=extension, fromPackage=fromPackage, fromRecipe=fromRecipe, license=license, linkStatus=linkStatus, symbolTable=symbolTable)
    
    def get_path(self):
        return self.m_path
    
    def get_name(self):
        return self.m_name
    
    def get_extension(self):
        return self.m_extension
    
    def get_from_package(self):
        return self.m_fromPackage
    
    def get_from_recipe(self):
        return self.m_fromRecipe
    
    def get_license(self):
        return self.m_license
    
    def get_link_status(self):
        return self.m_linkStatus
    
    def get_symbol_table(self):
        return self.m_symbolTable

    def set_path(self, path):
        self.m_path = path
    
    def set_name(self, name):
        self.m_name = name
    
    def set_extension(self, extension):
        self.m_extension = extension
    
    def set_from_package(self, fromPackage):
        self.m_fromPackage = fromPackage
    
    def set_from_recipe(self, fromRecipe):
        self.m_fromRecipe = fromRecipe
    
    def set_license(self, license):
        self.m_license = license

    def set_link_status(self, linkStatus):
        self.m_linkStatus = linkStatus
    
    def set_symbol_table(self, symbolTable):
        self.m_symbolTable = symbolTable