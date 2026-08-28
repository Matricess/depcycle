"""Graph node models for DepCycle."""

from __future__ import annotations

from enum import Enum
from pathlib import Path


class ModuleType(Enum):
    """Categorize a module as local, third-party, stdlib, or unknown."""

    LOCAL = "local"
    THIRD_PARTY = "third_party"
    STDLIB = "stdlib"
    UNKNOWN = "unknown"


class ModuleNode:
    """
    Represent a Python module in the dependency graph.

    A module's fully qualified name is its graph identity. Two nodes with
    the same module name therefore represent the same logical module,
    regardless of their file paths or module types.

    Attributes:
        name:
            Fully qualified Python name of the module, for example
            ``my_app.services.users``. This is the unique identity of
            the node within the graph.
        file_path:
            Absolute path to the module's source file. This is ``None``
            for non-local modules and is informational rather than part
            of node identity.
        module_type:
            Category of the module.
        raw_imports:
            Raw import strings extracted from the source file by ASTParser.
        dependencies:
            Other ModuleNode objects that this module directly depends on.
    """

    def __init__(
        self,
        name: str,
        file_path: Path | None,
        module_type: ModuleType,
    ) -> None:
        self.name: str = name
        self.file_path: Path | None = file_path
        self.module_type: ModuleType = module_type
        self.raw_imports: set[str] = set()
        self.dependencies: set[ModuleNode] = set()

    def __repr__(self) -> str:
        """Provide a developer-friendly representation of the module node."""
        return (
            f"ModuleNode("
            f"name={self.name!r}, "
            f"type={self.module_type.name}, "
            f"deps={len(self.dependencies)}"
            ")"
        )

    def __eq__(self, other: object) -> bool:
        """
        Return True when two nodes represent the same module.

        Module name is the sole identity of a graph node. File path and
        module type do not affect equality.
        """
        if not isinstance(other, ModuleNode):
            return NotImplemented

        return self.name == other.name

    def __hash__(self) -> int:
        """Return a hash based on the unique module name."""
        return hash(self.name)
