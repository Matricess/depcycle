# Design Commentary & Project Evaluation

## 1. Project Status: Deployed & In Use 
**Status:** Deployed, Hosted, and Distributed.

* **Deployment:** The project is published to the **Python Package Index (PyPI)** as `depcycle`. It is installable via the standard industry command `pip install depcycle`.
* **Hosting:** The source and release pipeline are hosted on GitHub, utilizing **GitHub Actions** for Trusted Publishing.
* **External Usage:** We track usage via **PePy.tech analytics**. The project has gathered downloads from users outside the development team, validating its utility as a real-world tool.
    * *Live Stats:* [![Downloads](https://static.pepy.tech/badge/depcycle)](https://pepy.tech/project/depcycle)

---

## 2. Design Docs (Synchronized with Code)
**Criteria: "Design docs up to date with the code"**

The following class diagram represents the actual implemented architecture, matching the codebase (e.g., `DepCycleCLI` entry point, `IGraphVisualizer` interface).

```mermaid
classDiagram
    class DepCycleCLI {
        +main()
        +run(config)
    }

    class Config {
        +project_path: Path
        +output_format: str
        +exclude_patterns: List
    }

    class Project {
        +root_path: Path
        +get_python_files(): List[Path]
    }

    class ASTParser {
        +get_imports_from_file(): Set[str]
    }

    class DependencyGraph {
        +nodes: Dict
        +build(project, parser, config)
        +find_cycles(): List[List]
    }

    class IGraphVisualizer {
        <<interface>>
        +render(graph, config)
    }

    class GraphvizVisualizer {
        +render(graph, config)
    }

    class HtmlVisualizer {
        +render(graph, config)
    }

    DepCycleCLI ..> Config : creates
    DepCycleCLI ..> Project : uses
    DepCycleCLI ..> DependencyGraph : orchestrates
    DepCycleCLI ..> IGraphVisualizer : uses
    DependencyGraph ..> ASTParser : uses
    IGraphVisualizer <|-- GraphvizVisualizer
    IGraphVisualizer <|-- HtmlVisualizer
````

-----

## 3. Design Decisions Commentary

### Design Of Software?

We evolved the software from a simple script into a modular **Layered Architecture**:

1. **Facade Layer (`depcycle.cli`)**: We centralized all user interaction and workflow orchestration into `DepCycleCLI`. This decoupled the argument parsing from the core logic, allowing the tool to be invoked programmatically or via CLI.
2. **Abstraction of IO (`parsing.project`)**: Instead of hardcoding file paths, we created a `Project` abstraction. This handles the complexity of file discovery and exclusion patterns, keeping the graph logic pure.
3. **Visualization Strategy**: By extracting rendering into `IGraphVisualizer`, we improved the design's extensibility. We can now add JSON or Mermaid outputs without touching the core dependency analysis algorithms.

### Design Principles

* **Single Responsibility Principle (SRP):**
  * `ASTParser`: Responsible *only* for parsing syntax trees and extracting string imports. It knows nothing about nodes or graphs.
  * `DependencyGraph`: Responsible *only* for connecting nodes and detecting cycles. It delegates parsing to `ASTParser`.
* **Open/Closed Principle (OCP):**
  * We applied OCP to the visualization layer. The `IGraphVisualizer` interface is closed for modification, but the system is open to extension (e.g., adding `HtmlVisualizer`) without changing existing code.
* **Dependency Inversion Principle (DIP):**
  * The `DependencyGraph` depends on the abstraction of a `parser` rather than a concrete implementation, making it easier to mock data during complex cycle detection tests.

### Key refactoring done to improve the design

1. **Performance Optimization via Default Exclusions:**
   * *Problem:* The tool was freezing on large projects by parsing `venv` and `node_modules`.
   * *Refactoring:* We refactored `Project.get_python_files` to include a smart default exclusion list. This reduced graph noise and improved execution time by orders of magnitude for standard projects.
2. **Static Analysis via AST:**
   * *Problem:* Originally, we considered importing modules to inspect `__dict__`, which is dangerous (executes code) and slow.
   * *Refactoring:* We switched to `ast.NodeVisitor`. This allows us to analyze code statically without running it, ensuring safety and allowing analysis of broken/incomplete environments.