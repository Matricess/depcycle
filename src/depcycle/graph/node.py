from enum import Enum
from pathlib import Path
from typing import Set, Optional

class ModuleType(Enum):
    """
    categorize a module class as being part of the local project,
    a third party librart or the python standard library
    """
    LOCAL = "local"
    THIRD_PARTY = "third_party"
    STDLIB = "stdlib"

class ModuleNode:
    """
    represents a single Python file (a module) as a node in the dependency graph.
    
    attributes:
        name (str): The fully qualified Python name of the module (e.g., 'my_app.services.users').
        file_path (Optional[Path]): The absolute file system path to the .py file.
                                    This can be None for non-local modules (THIRD_PARTY, STDLIB).
        module_type (ModuleType): The category of the module.
        raw_imports (Set[str]): A set of raw import strings found in the file.
                                This is populated by the ASTParser.
        dependencies (Set['ModuleNode']): A set of other ModuleNode objects that this
                                           module directly depends on.
    """

    def __init__(self, name: str, file_path: Optional[Path], module_type: ModuleType):
        self.name: str = name
        self.file_path: Optional[Path] = file_path
        self.module_type: ModuleType = module_type
        self.raw_imports: Set[str] = set()
        self.dependencies: Set[ModuleNode] = set()

    def __repr__(self) -> str:
        """ provides a developer-friendly representation of the ModuleNode. """
        return (
            f"ModuleNode(name='{self.name}', "
            f"type={self.module_type.name}, "
            f"deps={len(self.dependencies)})"
        )
    
    def __eq__(self, other):
        """ two nodes are considered equal if their names are the same. """
        if not isinstance(other, ModuleNode):
            return NotImplemented
        return self.name == other.name
    
    def __hash__(self):
        """The hash is based on the unique module name."""
        return hash(self.name)
        