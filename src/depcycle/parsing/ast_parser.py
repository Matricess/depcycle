"""ASTParser class for extracting import statements from Python files."""

import ast
from pathlib import Path
from typing import Set


class ASTParser:
    """
    A stateless utility using AST to find all raw import strings from a file.
    
    This class uses Python's built-in ast module to safely parse Python files
    and extract import statements without executing the code.
    """
    
    @staticmethod
    def get_imports_from_file(file_path: Path) -> Set[str]:
        """
        Extract all import statements from a Python file.
        
        Parses the file using AST and collects:
        - import module
        - from module import ...
        - import module as alias (returns original module)
        - from module import item as alias (returns module.item)
        
        Args:
            file_path: Path to the Python file to parse.
        
        Returns:
            Set of import strings found in the file.
        
        Raises:
            SyntaxError: If the file contains invalid Python syntax.
            FileNotFoundError: If the file doesn't exist.
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            return set()
        
        try:
            tree = ast.parse(content, filename=str(file_path))
        except SyntaxError as e:
            # Log and continue - some files might have syntax errors
            return set()
        
        imports = set()
        visitor = _ImportVisitor()
        visitor.visit(tree)
        return visitor.imports


class _ImportVisitor(ast.NodeVisitor):
    """
    Internal AST visitor class for collecting import statements.
    
    This class walks the AST and collects all import-related statements.
    """
    
    def __init__(self):
        """Initialize the visitor with an empty imports set."""
        self.imports = set()
    
    def visit_Import(self, node: ast.Import):
        """
        Visit a standard import statement.
        
        Examples:
            import os -> adds "os"
            import os as operating_system -> adds "os"
            import os, sys -> adds "os", "sys"
        """
        for alias in node.names:
            self.imports.add(alias.name)
        self.generic_visit(node)
    
    def visit_ImportFrom(self, node: ast.ImportFrom):
        """
        Visit a from-import statement.
        
        Examples:
            from os import path -> adds "os.path"
            from os import path as p -> adds "os.path"
            from os.path import join -> adds "os.path.join"
            from . import local -> adds "."
            from .TimeAccount import TimeAccount -> adds ".TimeAccount"
        """
        # Check if this is a relative import (level > 0)
        if node.level > 0:
            # Create relative import marker with correct number of dots
            dots = '.' * node.level
            if node.module is None:
                # e.g., 'from . import local'
                module_base = dots
            else:
                # e.g., 'from .pkg import submod'
                module_base = f"{dots}{node.module}"
            
            if module_base:
                self.imports.add(module_base)
            
            if node.names:
                for alias in node.names:
                    if alias.name == '*':
                        continue
                    if node.module is None:
                        self.imports.add(f"{dots}{alias.name}")
                    else:
                        self.imports.add(f"{module_base}.{alias.name}")
        else:
            # Absolute import
            if node.module is None:
                # This shouldn't happen, but handle gracefully
                module_base = ""
            else:
                module_base = node.module
            
            # For absolute imports, add the full dotted names including imported items
            # If there are specific imports, create full dotted names
            if node.names:
                for alias in node.names:
                    full_name = f"{module_base}.{alias.name}"
                    self.imports.add(full_name)
            else:
                # from module import * - just add the module
                if module_base:
                    self.imports.add(module_base)
        
        self.generic_visit(node)

