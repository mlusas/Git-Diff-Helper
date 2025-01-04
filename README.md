# Git Diff Helper

A Python utility for generating comprehensive Git diff reports optimized for AI code review workflows. This tool helps you prepare code changes for AI review by creating structured, readable reports of Git changes.

## Quick Start
```bash
# Install from PyPI
pip install git-diff-helper

# Show unstaged changes (default)
git-diff-helper

# Show all changes (staged, unstaged, and untracked)
git-diff-helper --all-changes

# Show only staged changes
git-diff-helper --staged-only

# Show only untracked files
git-diff-helper --untracked-only
```

## Features

- Generates three detailed reports:
  - Complete diffs in a unified format
  - Original file contents from HEAD
  - Updated file contents from working directory
- Shows changes in different scopes:
  - Unstaged, tracked changes (what you're working on)
  - Untracked files (new files not tracked in Git)
  - Staged changes (what you're about to commit)
  - All changes (Untracked + Unstaged + Staged)
- Supports customizable file extension filtering
- Handles binary files and gitignored files appropriately
- Provides verbose logging option
- Configurable output directory

## Installation Options

### From PyPI (Recommended)
```bash
pip install git-diff-helper
```

### From GitHub
```bash
pip install git+https://github.com/mlusas/git-diff-helper.git
```

### For Development
```bash
git clone https://github.com/mlusas/git-diff-helper.git
cd git-diff-helper
pip install -e .
```

## Usage

Basic usage shows unstaged changes (your work in progress):
```bash
git-diff-helper
```

Common workflows:
```bash
# Show everything (staged, unstaged, and untracked)
git-diff-helper --all-changes

# Show only staged changes (what you're about to commit)
git-diff-helper --staged-only

# Show only untracked files (new files)
git-diff-helper --untracked-only

# Filter by file extensions and output directory
git-diff-helper --extensions ".py,.js,.ts" --output-dir ./diffs
```

### Command Line Options

File Selection (mutually exclusive):
- Default: Show unstaged, tracked changes (work in progress)
- `--all-changes`, `-a`: Show everything (staged, unstaged, and untracked)
- `--staged-only`, `-s`: Show only staged changes
- `--untracked-only`, `-u`: Show only untracked files

Output Options:
- `--output-dir`, `-o`: Directory to save output files (default: current directory)
- `--extensions`: Comma-separated list of file extensions to process (e.g., '.py,.js,.ts')
- `--verbose`, `-v`: Enable verbose logging

### Output Files

The tool generates three Markdown files:

1. `diff_file_diffs.md`: Contains the actual diffs showing what changed
2. `diff_file_originals.md`: Contains the original content of changed files
3. `diff_file_updated.md`: Contains the current content of changed files

## AI Code Review Workflows

### Using with ChatGPT/Claude

1. Generate diff reports:
```bash
# For a comprehensive review of everything
git-diff-helper --all-changes --output-dir ./review

# For reviewing what you're about to commit
git-diff-helper --staged-only --output-dir ./review

# For reviewing work in progress
git-diff-helper --output-dir ./review
```

2. Share the generated files with the AI:
   - `diff_file_diffs.md` for a quick overview of changes
   - `diff_file_originals.md` and `diff_file_updated.md` for deeper context
   - Use the AI's context window efficiently by sharing only relevant parts

3. Suggested prompts for AI review:
   - "Please review these changes for potential bugs and improvements"
   - "What are the security implications of these changes?"
   - "How could this code be made more maintainable?"
   - "Suggest optimizations for performance"

### Using with GitHub Copilot

1. Generate focused diffs for specific files:
```bash
# Review all Python changes
git-diff-helper --all-changes --extensions ".py"

# Review staged JavaScript changes
git-diff-helper --staged-only --extensions ".js"
```

2. Open the diff files alongside your code
3. Use Copilot suggestions while reviewing the changes

## Advanced Usage

### As a Python Module

You can import and use the `GitDiffHelper` class in your own Python scripts:

```python
from git_diff_helper import GitDiffHelper

# Initialize with custom settings
helper = GitDiffHelper(
    allowed_extensions={'.py', '.js'},
    output_dir='./reports',
    verbose=True
)

# Generate reports with different scopes
helper.generate_reports(scope='all')  # Show everything
helper.generate_reports(scope='staged')  # Show staged changes
helper.generate_reports(scope='unstaged')  # Show unstaged changes
helper.generate_reports(scope='untracked')  # Show untracked files

# Or use individual methods
changed_files = helper.get_changed_files(scope='all')
for file in changed_files:
    diff = helper.get_file_diff(file, scope='all')
    print(f"Changes in {file}:\n{diff}")
```

### Integration Examples

Pre-commit hook:
```bash
# .git/hooks/pre-commit
git-diff-helper --staged-only --output-dir ./review
git add ./review/*.md
```

CI/CD pipeline:
```bash
# In your CI/CD config
git-diff-helper --all-changes --output-dir $CI_PROJECT_DIR/code-review
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

### Development Setup
```bash
# Clone the repository
git clone https://github.com/mlusas/git-diff-helper.git
cd git-diff-helper

# Install development dependencies
pip install -r requirements-dev.txt

# Install in editable mode
pip install -e .

# Run tests
pytest
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Inspired by the need for better AI code review workflows
- Built with Python's excellent subprocess and pathlib libraries