import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from git_diff_helper.core import GitDiffHelper, main

@pytest.fixture
def helper():
    return GitDiffHelper(output_dir="./test_output")

@pytest.fixture
def mock_subprocess():
    with patch('subprocess.run') as mock_run:
        yield mock_run

def test_initialization(helper):
    """Test initialization of GitDiffHelper."""
    assert isinstance(helper.allowed_extensions, set)
    assert '.py' in helper.allowed_extensions
    assert isinstance(helper.output_dir, Path)

def test_run_git_command_success(helper, mock_subprocess):
    """Test successful git command execution."""
    mock_process = MagicMock()
    mock_process.returncode = 0
    mock_process.stdout = "test output"
    mock_subprocess.return_value = mock_process
    
    output, error = helper.run_git_command(["git", "status"])
    assert output == "test output"
    assert error is None

def test_run_git_command_failure(helper, mock_subprocess):
    """Test git command failure handling."""
    mock_process = MagicMock()
    mock_process.returncode = 1
    mock_process.stderr = "error message"
    mock_subprocess.return_value = mock_process
    
    output, error = helper.run_git_command(["git", "status"])
    assert output is None
    assert error == "error message"

def test_get_gitignored_files(helper, mock_subprocess):
    """Test fetching gitignored files."""
    mock_process = MagicMock()
    mock_process.returncode = 0
    mock_process.stdout = "ignored1.txt\nignored2.txt"
    mock_subprocess.return_value = mock_process
    
    ignored_files = helper.get_gitignored_files()
    assert isinstance(ignored_files, set)
    assert "ignored1.txt" in ignored_files
    assert "ignored2.txt" in ignored_files

def mock_git_command(command):
    """Helper to create mock git command responses."""
    mock_process = MagicMock()
    mock_process.returncode = 0
    
    if command == ["git", "ls-files", "--others", "--ignored", "--exclude-standard"]:
        mock_process.stdout = "ignored.txt"
    elif command == ["git", "diff", "--name-only"]:
        mock_process.stdout = "modified.py\nmodified.js"
    elif command == ["git", "diff", "--staged", "--name-only"]:
        mock_process.stdout = "staged.py\nstaged.js"
    elif command == ["git", "ls-files", "--others", "--exclude-standard"]:
        mock_process.stdout = "new.py\nnew.js"
    else:
        mock_process.stdout = ""
    
    return mock_process

def test_get_changed_files_unstaged(helper, mock_subprocess):
    """Test getting only unstaged changes (default behavior)."""
    mock_subprocess.side_effect = mock_git_command
    
    files = helper.get_changed_files(scope='unstaged')
    assert "modified.py" in files
    assert "modified.js" in files
    assert "staged.py" not in files
    assert "new.py" not in files

def test_get_changed_files_staged_only(helper, mock_subprocess):
    """Test getting only staged changes."""
    mock_subprocess.side_effect = mock_git_command
    
    files = helper.get_changed_files(scope='staged')
    assert "staged.py" in files
    assert "staged.js" in files
    assert "modified.py" not in files
    assert "new.py" not in files

def test_get_changed_files_all_changes(helper, mock_subprocess):
    """Test getting all changes (staged and unstaged)."""
    mock_subprocess.side_effect = mock_git_command
    
    files = helper.get_changed_files(scope='all')
    assert "modified.py" in files
    assert "modified.js" in files
    assert "staged.py" in files
    assert "staged.js" in files
    assert "new.py" not in files

def test_get_changed_files_untracked_only(helper, mock_subprocess):
    """Test getting only untracked files."""
    mock_subprocess.side_effect = mock_git_command
    
    files = helper.get_changed_files(scope='untracked')
    assert "new.py" in files
    assert "new.js" in files
    assert "modified.py" not in files
    assert "staged.py" not in files

@patch('argparse.ArgumentParser.parse_args')
@patch('git_diff_helper.core.GitDiffHelper')
def test_main_cli_unstaged(mock_helper, mock_parse_args):
    """Test main CLI with default (unstaged) scope."""
    mock_parse_args.return_value = MagicMock(
        scope='unstaged',
        output_dir='.',
        extensions=None,
        verbose=False
    )
    
    main()
    
    # Verify GitDiffHelper was called with correct parameters
    mock_helper.assert_called_once_with(
        allowed_extensions=None,
        output_dir='.',
        verbose=False
    )
    # Verify generate_reports was called with unstaged scope
    mock_helper.return_value.generate_reports.assert_called_once_with(scope='unstaged')

@patch('argparse.ArgumentParser.parse_args')
@patch('git_diff_helper.core.GitDiffHelper')
def test_main_cli_all_changes(mock_helper, mock_parse_args):
    """Test main CLI with --all-changes flag."""
    mock_parse_args.return_value = MagicMock(
        scope='all',
        output_dir='.',
        extensions=None,
        verbose=False
    )
    
    main()
    
    # Verify GitDiffHelper was called with correct parameters
    mock_helper.assert_called_once_with(
        allowed_extensions=None,
        output_dir='.',
        verbose=False
    )
    # Verify generate_reports was called with all scope
    mock_helper.return_value.generate_reports.assert_called_once_with(scope='all')

@patch('argparse.ArgumentParser.parse_args')
@patch('git_diff_helper.core.GitDiffHelper')
def test_main_cli_staged_only(mock_helper, mock_parse_args):
    """Test main CLI with --staged-only flag."""
    mock_parse_args.return_value = MagicMock(
        scope='staged',
        output_dir='.',
        extensions=None,
        verbose=False
    )
    
    main()
    
    # Verify GitDiffHelper was called with correct parameters
    mock_helper.assert_called_once_with(
        allowed_extensions=None,
        output_dir='.',
        verbose=False
    )
    # Verify generate_reports was called with staged scope
    mock_helper.return_value.generate_reports.assert_called_once_with(scope='staged')

@patch('argparse.ArgumentParser.parse_args')
@patch('git_diff_helper.core.GitDiffHelper')
def test_main_cli_untracked_only(mock_helper, mock_parse_args):
    """Test main CLI with --untracked-only flag."""
    mock_parse_args.return_value = MagicMock(
        scope='untracked',
        output_dir='.',
        extensions=None,
        verbose=False
    )
    
    main()
    
    # Verify GitDiffHelper was called with correct parameters
    mock_helper.assert_called_once_with(
        allowed_extensions=None,
        output_dir='.',
        verbose=False
    )
    # Verify generate_reports was called with untracked scope
    mock_helper.return_value.generate_reports.assert_called_once_with(scope='untracked')

def test_allowed_extensions(helper):
    """Test setting allowed extensions."""
    custom_helper = GitDiffHelper(
        allowed_extensions={'.txt', '.md'},
        output_dir="./test_output"
    )
    assert custom_helper.allowed_extensions == {'.txt', '.md'}

def test_is_binary_file(helper, mock_subprocess):
    """Test binary file detection."""
    mock_process = MagicMock()
    mock_process.returncode = 0
    mock_process.stdout = "test.bin: binary: set"
    mock_subprocess.return_value = mock_process
    
    assert helper.is_binary_file("test.bin") is True

def test_file_exists_in_git(helper, mock_subprocess):
    """Test git file existence check."""
    mock_process = MagicMock()
    mock_process.returncode = 0
    mock_subprocess.return_value = mock_process
    
    assert helper.file_exists_in_git("existing.txt") is True

def test_get_file_diff_tracked(helper, mock_subprocess):
    """Test getting diff for tracked files."""
    mock_process = MagicMock()
    mock_process.returncode = 0
    mock_process.stdout = "@@ -1,1 +1,1 @@\n-old\n+new"
    mock_subprocess.return_value = mock_process
    
    diff = helper.get_file_diff("test.py")
    assert "@@ -1,1 +1,1 @@" in diff
    assert "-old" in diff
    assert "+new" in diff

@patch('pathlib.Path.read_text')
@patch('pathlib.Path.exists')
def test_get_file_diff_new(mock_exists, mock_read_text, helper, mock_subprocess):
    """Test getting diff for new files."""
    # Setup mocks
    mock_exists.return_value = True
    mock_read_text.return_value = "new content\nsecond line"
    
    # Mock git command to indicate file doesn't exist in git
    def mock_git_error(*args, **kwargs):
        mock = MagicMock()
        mock.returncode = 1
        return mock
    mock_subprocess.side_effect = mock_git_error
    
    # Get diff for new file
    diff = helper.get_file_diff("new.py")
    
    # Verify diff format
    assert "new file" in diff
    assert "+new content" in diff
    assert "+second line" in diff

def test_get_original_file_content_tracked(helper, mock_subprocess):
    """Test getting original content for tracked files."""
    mock_process = MagicMock()
    mock_process.returncode = 0
    mock_process.stdout = "original content"
    mock_subprocess.return_value = mock_process
    
    content = helper.get_original_file_content("test.py")
    assert content == "original content"

def test_get_original_file_content_new(helper, mock_subprocess):
    """Test getting original content for new files."""
    # Mock file not existing in git
    mock_process = MagicMock()
    mock_process.returncode = 1
    mock_subprocess.return_value = mock_process
    
    content = helper.get_original_file_content("new.py")
    assert "does not exist in HEAD" in content

@patch('pathlib.Path.read_text')
def test_get_updated_file_content_existing(mock_read_text, helper):
    """Test getting current content for existing files."""
    mock_read_text.return_value = "updated content"
    
    content = helper.get_updated_file_content("test.py")
    assert content == "updated content"

@patch('pathlib.Path.exists')
def test_get_updated_file_content_deleted(mock_exists, helper):
    """Test getting current content for deleted files."""
    mock_exists.return_value = False
    
    content = helper.get_updated_file_content("deleted.py")
    assert "has been deleted" in content

@pytest.mark.integration
def test_generate_reports(helper, tmp_path, mock_subprocess):
    """Test report generation (integration test)."""
    # Setup mocks for git commands
    mock_subprocess.side_effect = mock_git_command
    
    # Set output directory to temp path
    helper.output_dir = tmp_path
    
    # Generate reports
    helper.generate_reports(scope='all')
    
    # Verify files were created
    assert (tmp_path / "diff_file_diffs.md").exists()
    assert (tmp_path / "diff_file_originals.md").exists()
    assert (tmp_path / "diff_file_updated.md").exists()