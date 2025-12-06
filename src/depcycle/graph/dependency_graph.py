"""DependencyGraph class representing the core graph data structure."""
from pathlib import Path
from ..config import Config
from ..parsing.project import Project
from ..parsing.ast_parser import ASTParser
from typing import Dict, List, Set, Optional
from .module_node import ModuleNode, ModuleType

class DependencyGraph:
    """
    The Blueprint: The central data structure holding the dependency graph.
    
    This class orchestrates the process of building a dependency graph from
    a Python project, resolving import relationships, and detecting cycles.
    """
    
    def __init__(self):
        """Initialize an empty dependency graph."""
        self.nodes: Dict[str, ModuleNode] = {}
        self._project_root: Optional[Path] = None
        self._analysis_root: Optional[Path] = None
    
    def build(self, project: Project, parser: ASTParser, config: Config):
        """
        Build the dependency graph by scanning the project.
        
        This is the main orchestration method that:
        1. Discovers all Python files in the project
        2. Creates ModuleNode objects for each file
        3. Extracts imports using the AST parser
        4. Resolves dependencies between nodes
        5. Classifies modules by type
        
        Args:
            project: The Project instance containing the files to analyze.
            parser: The ASTParser for extracting imports.
            config: Configuration settings for filtering.
        """
        self._project_root = project.root_path
        self._analysis_root = project.root_path
        
        # Step 1: Discover all Python files
        python_files = project.get_python_files(
            config.exclude_patterns, 
            not config.include_all
        )
        
        # Step 2: Create nodes for each Python file
        for file_path in python_files:
            node = self._create_module_node(file_path, project.root_path)
            self.nodes[node.name] = node
            
            # Extract imports using AST
            raw_imports = parser.get_imports_from_file(file_path)
            node.raw_imports = raw_imports
        
        # Step 3: Resolve dependencies
        self._resolve_dependencies()
        
        # Step 4: Classify modules
        self._classify_modules()
        
        # Step 5: Filter based on config
        self._apply_filters(config)
    
    def _create_module_node(self, file_path: Path, project_root: Path) -> ModuleNode:
        """
        Create a ModuleNode from a file path.
        
        Args:
            file_path: Absolute path to the Python file.
            project_root: Root directory of the project.
        
        Returns:
            A new ModuleNode instance.
        """
        # Convert absolute path to module name
        # e.g., /project/src/app/models/user.py -> app.models.user
        relative_path = file_path.relative_to(project_root)
        
        # Remove .py extension and convert path separators to dots
        module_name = str(relative_path.with_suffix('')).replace('/', '.').replace('\\', '.')
        
        return ModuleNode(name=module_name, file_path=file_path, module_type=ModuleType.LOCAL)
    
    def _resolve_dependencies(self):
        """
        Resolve raw import strings to actual ModuleNode dependencies.
        
        For each node, this method matches raw_imports to other nodes.
        If a local match isn't found, it creates a new node representing
        an external dependency (Standard Lib or Third Party).
        """
        # Iterate over a copy because we might add new nodes during the loop
        current_nodes = list(self.nodes.values())
        
        for node in current_nodes:
            # We only resolve dependencies for LOCAL nodes (source files we scanned)
            if node.module_type != ModuleType.LOCAL:
                continue

            node.dependencies = set()
            
            for import_str in node.raw_imports:
                # 1. Try to resolve to an existing local module
                dependency_node = self._resolve_import(import_str, node.name)
                
                # 2. If not found locally, treat as External (Stdlib/Third-Party)
                if dependency_node is None:
                    # Ignore relative imports that failed to resolve (broken local code)
                    if import_str.startswith('.'):
                        continue

                    # Check if we already created a node for this external lib
                    if import_str in self.nodes:
                        dependency_node = self.nodes[import_str]
                    else:
                        # Create a new placeholder node
                        # We default to THIRD_PARTY; _classify_modules will correct this later
                        dependency_node = ModuleNode(
                            name=import_str, 
                            file_path=None, 
                            module_type=ModuleType.THIRD_PARTY
                        )
                        self.add_node(dependency_node)
                
                # 3. Link the dependency
                if dependency_node:
                    node.dependencies.add(dependency_node)
    
    def _resolve_import(self, import_str: str, current_module: str) -> Optional[ModuleNode]:
        """
        Resolve an import string to a ModuleNode if it exists in the graph.
        
        Handles various import patterns:
        - Absolute imports: 'os' -> looks for 'os' in graph
        - Relative imports: '.utils' -> resolves relative to current_module
        - Dotted imports: 'app.models' -> tries to find exact or parent module
        - Absolute imports with project prefix when analyzing subdirectories
        
        Args:
            import_str: The raw import string.
            current_module: The module where this import appears.
        
        Returns:
            The matching ModuleNode, or None if not found.
        """
        # Handle relative imports
        if import_str.startswith('.'):
            absolute_name = self._resolve_relative_import(import_str, current_module)
            if absolute_name in self.nodes:
                return self.nodes[absolute_name]
            return None
        
        # Handle absolute imports - try exact match first
        if import_str in self.nodes:
            return self.nodes[import_str]
        
        # NEW: Handle absolute imports that reference parent package
        # When analyzing subdirectory, imports like "app.models" might actually mean "models"
        if self._project_root and '.' in import_str:
            # Get the project root name (last part of the path)
            project_root_name = self._project_root.name
            
            # Check if import starts with project root name
            if import_str.startswith(project_root_name + '.'):
                # Strip the project root prefix and try again
                stripped_import = import_str[len(project_root_name) + 1:]
                if stripped_import in self.nodes:
                    return self.nodes[stripped_import]
                
                # Also try variants of the stripped import
                for variant in self._get_import_variants(stripped_import):
                    if variant in self.nodes:
                        return self.nodes[variant]
        
        # Try to find the parent module of the import
        for potential_module in self._get_import_variants(import_str):
            if potential_module in self.nodes:
                return self.nodes[potential_module]
            
            # NEW: Also try stripping project root from variants
            if self._project_root and '.' in potential_module:
                project_root_name = self._project_root.name
                if potential_module.startswith(project_root_name + '.'):
                    stripped_variant = potential_module[len(project_root_name) + 1:]
                    if stripped_variant in self.nodes:
                        return self.nodes[stripped_variant]
        
        return None
    
    def _get_import_variants(self, import_str: str) -> List[str]:
        """
        Generate potential module names from an import string.
        
        When you have an import like 'os.path.join', we should try to match
        against the full path, but also against parent modules like 'os.path' and 'os'.
        However, we should NOT match partial strings incorrectly.
        
        Examples:
            'config.Config' -> ['config.Config', 'config']
            'os.path.join' -> ['os.path.join', 'os.path', 'os']
            'sys' -> ['sys']
        
        Args:
            import_str: The import string to generate variants for.
        
        Returns:
            List of potential module names to try, in order of specificity.
        """
        variants = [import_str]  # Try the full import first
        
        # For dotted names, try progressively shorter prefixes
        # Split on dots and build up variants
        parts = import_str.split('.')
        
        # Generate variants: full -> parts[0].parts[1] -> parts[0]
        for i in range(len(parts) - 1, 0, -1):
            variant = '.'.join(parts[:i])
            if variant not in variants:
                variants.append(variant)
        
        return variants
    
    def _resolve_relative_import(self, relative_str: str, current_module: str) -> str:
        """
        Convert a relative import to an absolute module name.
        
        Args:
            relative_str: The relative import (e.g., '.utils', '..models', '.TimeAccount.TimeAccount').
            current_module: The module where this import appears.
        
        Returns:
            The absolute module name.
        """
        # Count the number of leading dots
        dots = 0
        for char in relative_str:
            if char == '.':
                dots += 1
            else:
                break
        
        # Remove the dots to get the remaining path
        remaining = relative_str[dots:]
        
        # Navigate up the module hierarchy
        parts = current_module.split('.')
        target_depth = len(parts) - dots
        
        if target_depth < 0:
            return relative_str  # Can't resolve, return as-is
        
        # Build the absolute module name
        result_parts = parts[:target_depth]
        if remaining:
            # Append the remaining path
            result_parts.append(remaining)
        
        return '.'.join(result_parts)
    
    def _classify_modules(self):
        """
        Classify each module as LOCAL, THIRD_PARTY, or STDLIB.
        
        This is currently simplified - in a full implementation, you'd want
        to check against standard library and installed packages.
        """
        # Python standard library modules (partial list)
        stdlib_modules = {
            'os', 'sys', 'pathlib', 'json', 'xml', 'csv', 'datetime',
            'time', 'random', 'hashlib', 'uuid', 'collections', 'itertools',
            'functools', 'operator', 'math', 'statistics', 're', 'string',
            'io', 'pickle', 'copy', 'abc', 'enum', 'dataclasses', 'typing',
            'inspect', 'ast', 'traceback', 'logging', 'argparse', 'getopt',
            'socket', 'http', 'urllib', 'email', 'html', 'textwrap', 'pprint',
            'subprocess', 'threading', 'multiprocessing', 'asyncio', 'queue',
            'weakref', 'gc', 'contextlib', 'decorator', 'profile', 'cProfile',
            'doctest', 'unittest', 'pdb', 'dis', 'compileall', 'py_compile',
            'cmd', 'shlex', 'configparser', 'fileinput', 'locale', 'gettext',
            'argparse', 'calendar', 'codecs', 'difflib', 'fnmatch', 'glob',
            'linecache', 'shutil', 'tempfile', 'mmap', 'readline', 'rlcompleter',
            'sqlite3', 'zlib', 'gzip', 'bz2', 'lzma', 'zipfile', 'tarfile',
            'csv', 'configparser', 'netrc', 'xdrlib', 'plistlib', 'hashlib',
            'hmac', 'secrets', 'base64', 'binascii', 'struct', 'codecs',
            'unicodedata', 'stringprep', 'readline', 'rlcompleter', 'lib2to3'
        }
        
        for node in self.nodes.values():
            # Skip if already classified as LOCAL (from file path)
            if node.module_type == ModuleType.LOCAL:
                continue
            
            # Check if it's a standard library module
            module_base = node.name.split('.')[0]
            if module_base in stdlib_modules:
                node.module_type = ModuleType.STDLIB
            else:
                # Assume third-party for now
                # In production, you might check installed packages
                node.module_type = ModuleType.THIRD_PARTY
    
    def _apply_filters(self, config: Config):
        """
        Apply filtering based on configuration options.
        
        Args:
            config: Configuration settings.
        """
        if config.show_third_party and config.show_stdlib:
            return  # Nothing to filter
        
        # Build set of modules to keep
        keep_modules = set()
        for node in self.nodes.values():
            if node.module_type == ModuleType.LOCAL:
                keep_modules.add(node.name)
            elif node.module_type == ModuleType.THIRD_PARTY and config.show_third_party:
                keep_modules.add(node.name)
            elif node.module_type == ModuleType.STDLIB and config.show_stdlib:
                keep_modules.add(node.name)
        
        # Remove filtered nodes
        filtered_out = set(self.nodes.keys()) - keep_modules
        for module_name in filtered_out:
            del self.nodes[module_name]
        
        # Clean up dependencies pointing to removed nodes
        for node in self.nodes.values():
            node.dependencies = {
                dep for dep in node.dependencies 
                if dep.name in self.nodes
            }
    
    def add_node(self, node: ModuleNode):
        """
        Add a node to the graph.
        
        Args:
            node: The ModuleNode to add.
        """
        self.nodes[node.name] = node
    
    def find_cycles(self) -> List[List[ModuleNode]]:
        """
        Detect all cycles in the dependency graph.
        
        Uses Depth-First Search (DFS) to find strongly connected components
        or cycles. Returns all circular dependencies found.
        
        Returns:
            List of cycles, where each cycle is a list of ModuleNodes.
        """
        cycles = []
        visited = set()
        rec_stack = set()
        path = []
        
        def dfs(node: ModuleNode):
            """Recursive DFS helper for cycle detection."""
            visited.add(node.name)
            rec_stack.add(node.name)
            path.append(node)
            
            for dependency in node.dependencies:
                if dependency.name not in visited:
                    if dfs(dependency):
                        return True
                elif dependency.name in rec_stack:
                    # Found a cycle! Extract the cycle path
                    cycle_start = path.index(dependency)
                    cycles.append(path[cycle_start:] + [dependency])
                    return True
            
            rec_stack.remove(node.name)
            path.pop()
            return False
        
        # Run DFS on all nodes
        for node in self.nodes.values():
            if node.name not in visited:
                dfs(node)
        
        return cycles
    
    def __repr__(self) -> str:
        """Provide a developer-friendly representation."""
        return f"DependencyGraph(nodes={len(self.nodes)})"
    
    def __len__(self) -> int:
        """Return the number of nodes in the graph."""
        return len(self.nodes)
    
    def __iter__(self):
        """Allow iteration over nodes."""
        return iter(self.nodes.values())