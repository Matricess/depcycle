import sys
import pytest
from depcycle.cli import DepCycleCLI
from unittest.mock import patch, MagicMock

def test_cli_help(capsys):
    """Ensure --help works and displays the description."""
    with pytest.raises(SystemExit):
        DepCycleCLI.main(["--help"])
    
    captured = capsys.readouterr()
    assert "Visualize Python project dependencies" in captured.out

def test_cli_runs_on_valid_project(create_project, capsys):
    """
    Ensure the CLI runs end-to-end on a real directory.
    
    NOTE: We mock the visualizer here. This is a best practice in testing:
    we are testing that the CLI *calls* the visualizer, not that Graphviz 
    (an external tool) is correctly installed on the OS.
    """
    project_dir = create_project({
        "main.py": "import sys",
        "utils.py": "pass"
    })
    output_file = project_dir / "output.png"
    
    # --- MOCKING START ---
    # We intercept the call to _create_visualizer so we don't need actual Graphviz
    with patch("depcycle.cli.DepCycleCLI._create_visualizer") as mock_create:
        # Create a fake visualizer object
        mock_viz = MagicMock()
        
        # Define what happens when .render() is called: create a dummy file
        def fake_render(graph, config):
            config.output_file.parent.mkdir(parents=True, exist_ok=True)
            config.output_file.write_text("fake png content", encoding="utf-8")
        
        mock_viz.render.side_effect = fake_render
        mock_create.return_value = mock_viz
        
        # Run the CLI programmatically
        DepCycleCLI.main([str(project_dir), "-o", str(output_file)])
    # --- MOCKING END ---
    
    captured = capsys.readouterr()
    # Check for success messages
    assert "Analyzing project" in captured.out
    assert "Visualization saved" in captured.out
    # Verify artifact creation (our fake file)
    assert output_file.exists()

def test_cli_fails_on_missing_dir(tmp_path, capsys):
    """Ensure the CLI handles missing directories gracefully."""
    missing_dir = tmp_path / "ghost_directory"
    
    with pytest.raises(SystemExit):
        DepCycleCLI.main([str(missing_dir)])
        
    captured = capsys.readouterr()
    assert "Error: Project path does not exist" in captured.out