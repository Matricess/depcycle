from depcycle.config import Config
from depcycle.parsing.project import Project
from depcycle.parsing.ast_parser import ASTParser
from depcycle.graph.module_node import ModuleType
from depcycle.graph.dependency_graph import DependencyGraph

def test_cycle_detection(create_project):
    """Verify DFS algorithm detects circular dependencies."""
    tmp_path = create_project({
        "pkg/a.py": "from . import b",
        "pkg/b.py": "from . import c",
        "pkg/c.py": "from . import a"
    })

    project = Project(tmp_path)
    graph = DependencyGraph()
    config = Config(project_path=tmp_path, output_file=tmp_path/"out.png")

    graph.build(project, ASTParser(), config)
    cycles = graph.find_cycles()

    assert len(graph) == 3
    assert len(cycles) == 1
    assert {node.name for node in cycles[0]} == {"pkg.a", "pkg.b", "pkg.c"}

def test_relative_import_resolution(create_project):
    """Verify '..' relative imports resolve to the correct parent."""
    tmp_path = create_project({
        "x/y/z.py": "from ..u import v",
        "x/u/v.py": "pass"
    })

    project = Project(tmp_path)
    graph = DependencyGraph()
    config = Config(project_path=tmp_path, output_file=tmp_path/"out.png")

    graph.build(project, ASTParser(), config)
    
    node_z = graph.nodes["x.y.z"]
    dep_names = {dep.name for dep in node_z.dependencies}
    assert "x.u.v" in dep_names

def test_classification_and_filtering(create_project):
    """Verify modules are classified correctly and filtering works."""
    tmp_path = create_project({
        "main.py": "import os\nimport requests"
    })
    
    # 1. Build graph showing everything
    project = Project(tmp_path)
    graph = DependencyGraph()
    # Enable showing stdlib and third party
    config = Config(
        project_path=tmp_path, 
        output_file=tmp_path/"out.png",
        show_stdlib=True,
        show_third_party=True
    )
    
    graph.build(project, ASTParser(), config)
    
    assert graph.nodes["os"].module_type == ModuleType.STDLIB
    assert graph.nodes["requests"].module_type == ModuleType.THIRD_PARTY
    
    # 2. Build graph hiding stdlib
    graph_filtered = DependencyGraph()
    config_filtered = Config(
        project_path=tmp_path, 
        output_file=tmp_path/"out.png",
        show_stdlib=False,     
        show_third_party=True
    )
    
    graph_filtered.build(project, ASTParser(), config_filtered)
    
    assert "main" in graph_filtered.nodes
    assert "requests" in graph_filtered.nodes
    assert "os" not in graph_filtered.nodes  