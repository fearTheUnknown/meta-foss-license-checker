from abc import ABC, abstractmethod

class File(ABC):
    def __init__(self, path='', name='', extension='', fromPackage='', fromRecipe='',license='', linkStatus = '', symbolTable={}, strongLinkedSymbols={}, weakLinkedSymbols={}, duplicateLinkedSymbols={}, checksum=''):
        self.m_path = path
        self.m_name = name
        self.m_extension = extension
        self.m_fromPackage = fromPackage
        self.m_fromRecipe = fromRecipe
        self.m_license = license
        self.m_linkStatus = linkStatus
        self.m_symbolTable = symbolTable
        self.m_strongLinkedSymbols = strongLinkedSymbols
        self.m_weakLinkedSymbols = weakLinkedSymbols
        self.m_duplicateLinkedSymbols = duplicateLinkedSymbols
        self.m_checksum = checksum
    
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
    def get_strong_linked_symbols(self):
        pass

    @abstractmethod
    def get_weak_linked_symbols(self):
        pass

    @abstractmethod
    def get_duplicate_linked_symbols(self):
        pass

    @abstractmethod
    def get_checksum(self):
        pass
    
    @abstractmethod
    def set_path(self):
        pass
    
    @abstractmethod
    def set_name(self, name):
        pass
    
    @abstractmethod
    def set_extension(self, extension):
        pass
    
    @abstractmethod
    def set_from_package(self, fromPackage):
        pass
    
    @abstractmethod
    def set_from_recipe(self, fromRecipe):
        pass
    
    @abstractmethod
    def set_license(self, license):
        pass
    
    @abstractmethod
    def set_link_status(self, linkStatus):
        pass

    @abstractmethod
    def set_symbol_table(self, symbolTable):
        pass

    @abstractmethod
    def set_strong_linked_symbols(self, strongLinkedSymbols):
        pass

    @abstractmethod
    def set_weak_linked_symbols(self, weakLinkedSymbols):
        pass

    @abstractmethod
    def set_duplicate_linked_symbols(self, duplicateLinkedSymbols):
        pass

    @abstractmethod
    def set_checksum(self, checksum):
        pass

class HeaderFile(File):
    def __init__(self, path='', name='', extension='', fromPackage='', fromRecipe='',license='', linkStatus = '', symbolTable={}, strongLinkedSymbols={}, weakLinkedSymbols={}, duplicateLinkedSymbols={}, checksum=''):
        super().__init__(path=path, name=name, extension=extension, fromPackage=fromPackage, fromRecipe=fromRecipe, license=license, linkStatus=linkStatus, symbolTable=symbolTable, strongLinkedSymbols=strongLinkedSymbols, weakLinkedSymbols=weakLinkedSymbols, duplicateLinkedSymbols=duplicateLinkedSymbols, checksum=checksum)

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
    
    def get_strong_linked_symbols(self):
        return self.m_strongLinkedSymbols

    def get_weak_linked_symbols(self):
        return self.m_weakLinkedSymbols
    
    def get_duplicate_linked_symbols(self):
        return self.m_duplicateLinkedSymbols
    
    def get_checksum(self):
        return self.m_checksum

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
    
    def set_strong_linked_symbols(self, strongLinkedSymbols):
        self.m_strongLinkedSymbols = strongLinkedSymbols

    def set_weak_linked_symbols(self, weakLinkedSymbols):
        self.m_weakLinkedSymbols = weakLinkedSymbols

    def set_duplicate_linked_symbols(self, duplicateLinkedSymbols):
        self.m_duplicateLinkedSymbols = duplicateLinkedSymbols

    def set_checksum(self, checksum):
        self.m_checksum = checksum

class StaticLib(File):
    def __init__(self, path='', name='', extension='', fromPackage='', fromRecipe='',license='', linkStatus = '', symbolTable={}, strongLinkedSymbols={}, weakLinkedSymbols={}, duplicateLinkedSymbols={}, checksum=''):
        super().__init__(path=path, name=name, extension=extension, fromPackage=fromPackage, fromRecipe=fromRecipe, license=license, linkStatus=linkStatus, symbolTable=symbolTable, strongLinkedSymbols=strongLinkedSymbols, weakLinkedSymbols=weakLinkedSymbols, duplicateLinkedSymbols=duplicateLinkedSymbols, checksum=checksum)

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

    def get_strong_linked_symbols(self):
        return self.m_strongLinkedSymbols

    def get_weak_linked_symbols(self):
        return self.m_weakLinkedSymbols
    
    def get_duplicate_linked_symbols(self):
        return self.m_duplicateLinkedSymbols
    
    def get_checksum(self):
        return self.m_checksum
    
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
    
    def set_strong_linked_symbols(self, strongLinkedSymbols):
        self.m_strongLinkedSymbols = strongLinkedSymbols

    def set_weak_linked_symbols(self, weakLinkedSymbols):
        self.m_weakLinkedSymbols = weakLinkedSymbols
    
    def set_duplicate_linked_symbols(self, duplicateLinkedSymbols):
        self.m_duplicateLinkedSymbols = duplicateLinkedSymbols
    
    def set_checksum(self, checksum):
        self.m_checksum = checksum

class SharedLib(File):
    def __init__(self, path='', name='', extension='', fromPackage='', fromRecipe='',license='', linkStatus = '', symbolTable={}, strongLinkedSymbols={}, weakLinkedSymbols={}, duplicateLinkedSymbols={}, checksum=''):
        super().__init__(path=path, name=name, extension=extension, fromPackage=fromPackage, fromRecipe=fromRecipe, license=license, linkStatus=linkStatus, symbolTable=symbolTable, strongLinkedSymbols=strongLinkedSymbols, weakLinkedSymbols=weakLinkedSymbols, duplicateLinkedSymbols=duplicateLinkedSymbols, checksum=checksum)

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
    
    def get_strong_linked_symbols(self):
        return self.m_strongLinkedSymbols

    def get_weak_linked_symbols(self):
        return self.m_weakLinkedSymbols

    def get_duplicate_linked_symbols(self):
        return self.m_duplicateLinkedSymbols
    
    def get_checksum(self):
        return self.m_checksum
    
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
    
    def set_strong_linked_symbols(self, strongLinkedSymbols):
        self.m_strongLinkedSymbols = strongLinkedSymbols

    def set_weak_linked_symbols(self, weakLinkedSymbols):
        self.m_weakLinkedSymbols = weakLinkedSymbols
    
    def set_duplicate_linked_symbols(self, duplicateLinkedSymbols):
        self.m_duplicateLinkedSymbols = duplicateLinkedSymbols
    
    def set_checksum(self, checksum):
        self.m_checksum = checksum

class Executable(File):
    def __init__(self, path='', name='', extension='', fromPackage='', fromRecipe='',license='', linkStatus = '', symbolTable={}, strongLinkedSymbols={}, weakLinkedSymbols={}, duplicateLinkedSymbols={}, checksum=''):
        super().__init__(path=path, name=name, extension=extension, fromPackage=fromPackage, fromRecipe=fromRecipe, license=license, linkStatus=linkStatus, symbolTable=symbolTable, strongLinkedSymbols=strongLinkedSymbols, weakLinkedSymbols=weakLinkedSymbols, duplicateLinkedSymbols=duplicateLinkedSymbols, checksum=checksum)

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
    
    def get_strong_linked_symbols(self):
        return self.m_strongLinkedSymbols

    def get_weak_linked_symbols(self):
        return self.m_weakLinkedSymbols
    
    def get_duplicate_linked_symbols(self):
        return self.m_duplicateLinkedSymbols
    
    def get_checksum(self):
        return self.m_checksum
    
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
    
    def set_strong_linked_symbols(self, strongLinkedSymbols):
        self.m_strongLinkedSymbols = strongLinkedSymbols

    def set_weak_linked_symbols(self, weakLinkedSymbols):
        self.m_weakLinkedSymbols = weakLinkedSymbols
    
    def set_duplicate_linked_symbols(self, duplicateLinkedSymbols):
        self.m_duplicateLinkedSymbols = duplicateLinkedSymbols

    def set_checksum(self, checksum):
        self.m_checksum = checksum

class ObjectFile(File):
    def __init__(self, path='', name='', extension='', fromPackage='', fromRecipe='',license='', linkStatus = '', symbolTable={}, strongLinkedSymbols={}, weakLinkedSymbols={}, duplicateLinkedSymbols={}, checksum=''):
        super().__init__(path=path, name=name, extension=extension, fromPackage=fromPackage, fromRecipe=fromRecipe, license=license, linkStatus=linkStatus, symbolTable=symbolTable, strongLinkedSymbols=strongLinkedSymbols, weakLinkedSymbols=weakLinkedSymbols, duplicateLinkedSymbols=duplicateLinkedSymbols, checksum=checksum)

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
    
    def get_strong_linked_symbols(self):
        return self.m_strongLinkedSymbols

    def get_weak_linked_symbols(self):
        return self.m_weakLinkedSymbols
    
    def get_duplicate_linked_symbols(self):
        return self.m_duplicateLinkedSymbols
    
    def get_checksum(self):
        return self.m_checksum

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
    
    def set_strong_linked_symbols(self, strongLinkedSymbols):
        self.m_strongLinkedSymbols = strongLinkedSymbols

    def set_weak_linked_symbols(self, weakLinkedSymbols):
        self.m_weakLinkedSymbols = weakLinkedSymbols
    
    def set_duplicate_linked_symbols(self, duplicateLinkedSymbols):
        self.m_duplicateLinkedSymbols = duplicateLinkedSymbols
    
    def set_checksum(self, checksum):
        self.m_checksum = checksum