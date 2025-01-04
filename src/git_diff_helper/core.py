# src/git_diff_helper/core.py

import subprocess
import sys
import os
import argparse
import logging
from typing import Set, List, Tuple, Optional
from pathlib import Path

class GitDiffHelper:
    """A helper class to analyze and extract Git differences for AI code review workflows."""
    
    def __init__(self, 
                 allowed_extensions: Set[str] = None,
                 output_dir: str = ".",
                 verbose: bool = False):
        """
        Initialize the GitDiffHelper.
        
        Args:
            allowed_extensions: Set of file extensions to process. If None, processes all text files.
            output_dir: Directory to save output files.
            verbose: Enable verbose logging.
        """
        self.allowed_extensions = allowed_extensions or {
            '.php', '.js', '.html', '.css', '.ts', '.vue', '.py', 
            '.jsx', '.tsx', '.json', '.yml', '.yaml', '.md', '.txt'
        }
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        log_level = logging.DEBUG if verbose else logging.INFO
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def run_git_command(self, cmd: List[str]) -> Tuple[Optional[str], Optional[str]]:
        """
        Run a git command and return its output.
        
        Args:
            cmd: List of command components.
            
        Returns:
            Tuple of (stdout, stderr) where either may be None.
        """
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                return None, result.stderr.strip()
            return result.stdout.strip(), None
        except subprocess.SubprocessError as e:
            self.logger.error(f"Error running git command {' '.join(cmd)}: {e}")
            return None, str(e)

    def get_gitignored_files(self) -> Set[str]:
        """Get set of files that are git ignored."""
        output, error = self.run_git_command(["git", "ls-files", "--others", "--ignored", "--exclude-standard"])
        if error:
            self.logger.warning(f"Error detecting gitignored files: {error}")
            return set()
        return set(output.split('\n') if output else [])

    def get_changed_files(self, scope: str = 'unstaged') -> List[str]:
        """
        Get list of changed files based on specified scope.
        
        Args:
            scope: One of 'unstaged' (default), 'staged', 'untracked', or 'all'
            
        Returns:
            List of changed file paths.
        """
        changed_files = set()
        gitignored_files = self.get_gitignored_files()

        # Get staged changes if requested
        if scope in ['all', 'staged']:
            output, error = self.run_git_command(["git", "diff", "--staged", "--name-only"])
            if error:
                self.logger.error(f"Error detecting staged files: {error}")
            else:
                changed_files.update(output.split('\n') if output else [])

        # Get unstaged changes if requested
        if scope in ['all', 'unstaged']:
            output, error = self.run_git_command(["git", "diff", "--name-only"])
            if error:
                self.logger.error(f"Error detecting unstaged files: {error}")
            else:
                changed_files.update(output.split('\n') if output else [])

        # Get untracked files if requested
        if scope in ['all', 'untracked']:
            output, error = self.run_git_command(["git", "ls-files", "--others", "--exclude-standard"])
            if error:
                self.logger.error(f"Error detecting untracked files: {error}")
            else:
                new_files = set(output.split('\n') if output else [])
                if new_files:
                    self.logger.info(f"Found {len(new_files)} untracked files")
                    changed_files.update(new_files)
        elif len(changed_files) > 0:  # Only check if we found other changes
            # Check for untracked files and notify if any exist
            output, error = self.run_git_command(["git", "ls-files", "--others", "--exclude-standard"])
            if output and output.strip():
                new_files = set(output.split('\n'))
                self.logger.info(f"Note: {len(new_files)} untracked files were detected. Use --all-changes to include them.")
        
        # Filter files
        return [
            f for f in changed_files
            if f.strip() and 
            f not in gitignored_files and 
            not f.startswith("diff_file_") and
            not Path(f).name.startswith("diff_file_") and
            (self.allowed_extensions is None or 
             Path(f).suffix in self.allowed_extensions)
        ]

    def is_binary_file(self, filename: str) -> bool:
        """Check if a file is binary."""
        output, error = self.run_git_command(["git", "check-attr", "binary", filename])
        if error or not output:
            return False
        return "binary: set" in output

    def file_exists_in_git(self, filename: str) -> bool:
        """Check if a file exists in git."""
        _, error = self.run_git_command(["git", "ls-files", "--error-unmatch", filename])
        return error is None

    def get_file_diff(self, filename: str, scope: str = 'unstaged') -> str:
        """Get the diff for a specific file."""
        self.logger.debug(f"Processing diff for: {filename}")

        if self.file_exists_in_git(filename):
            # For tracked files, get appropriate diff
            cmd = ["git", "diff"]
            if scope == 'staged':
                cmd.append("--staged")
            cmd.append(filename)
            
            output, error = self.run_git_command(cmd)
            if error:
                return f"# Unable to fetch diff for {filename}.\n{error}"
            return output
        else:
            # For untracked files, show entire content as addition
            try:
                content = Path(filename).read_text(encoding='utf-8', errors='replace')
                return f"diff --git a/{filename} b/{filename}\n" + \
                       f"new file mode 100644\n" + \
                       f"--- /dev/null\n" + \
                       f"+++ b/{filename}\n" + \
                       f"@@ -0,0 +1,{len(content.splitlines())} @@\n" + \
                       "".join(f"+{line}\n" for line in content.splitlines())
            except Exception as e:
                return f"# Unable to read untracked file {filename}.\n{e}"

    def get_original_file_content(self, filename: str) -> str:
        """Get the original content of a file from HEAD."""
        self.logger.debug(f"Fetching original content for: {filename}")
        if not self.file_exists_in_git(filename):
            return f"# File {filename} does not exist in HEAD.\n"
        if self.is_binary_file(filename):
            return f"# File {filename} is binary.\n"
            
        output, error = self.run_git_command(["git", "show", f"HEAD:{filename}"])
        if error:
            return f"# Unable to fetch original content for {filename}.\n{error}"
        return output

    def get_updated_file_content(self, filename: str) -> str:
        """Get the current content of a file from working directory."""
        self.logger.debug(f"Fetching updated content for: {filename}")
        filepath = Path(filename)
        if not filepath.exists():
            return f"# File {filename} has been deleted.\n"
        if self.is_binary_file(filename):
            return f"# File {filename} is binary.\n"
            
        try:
            return filepath.read_text(encoding='utf-8', errors='replace')
        except Exception as e:
            return f"# Unable to read file {filename}.\nError: {e}"

    def generate_reports(self, scope: str = 'unstaged') -> None:
        """Generate comprehensive diff reports."""
        changed_files = self.get_changed_files(scope)
        if not changed_files:
            self.logger.info("No changed files found.")
            return

        # Create output files
        diffs_file = self.output_dir / "diff_file_diffs.md"
        originals_file = self.output_dir / "diff_file_originals.md"
        updated_file = self.output_dir / "diff_file_updated.md"

        self.logger.info(f"\nProcessing {len(changed_files)} changed files.")

        # Write diffs
        with open(diffs_file, 'w', encoding='utf-8') as diff_out:
            diff_out.write("# Diffs of Changed Files\n\n")
            for cf in changed_files:
                try:
                    diff_content = self.get_file_diff(cf, scope=scope)
                    diff_out.write(f"## {cf}\n\n```diff\n{diff_content}\n```\n\n")
                except Exception as e:
                    self.logger.error(f"Error processing diff for {cf}: {e}")

        # Write originals and updates
        with open(originals_file, 'w', encoding='utf-8') as orig_out, \
             open(updated_file, 'w', encoding='utf-8') as upd_out:
            
            orig_out.write("# Original Files (HEAD)\n\n")
            upd_out.write("# Updated Files (Working Directory)\n\n")
            
            for cf in changed_files:
                try:
                    original = self.get_original_file_content(cf)
                    updated = self.get_updated_file_content(cf)

                    # Write original
                    orig_out.write(f"## {cf}\n\n```\n{original}\n```\n\n")
                    
                    # Write updated
                    upd_out.write(f"## {cf}\n\n```\n{updated}\n```\n\n")
                except Exception as e:
                    self.logger.error(f"Error processing file {cf}: {e}")

        self.logger.info(
            f"\nDone. Created:\n"
            f"- {diffs_file}\n"
            f"- {originals_file}\n"
            f"- {updated_file}\n"
        )

def main():
    """Main entry point with argument parsing."""
    parser = argparse.ArgumentParser(
        description="Generate comprehensive Git diff reports for AI code review workflows."
    )
    
    # File selection options
    scope_group = parser.add_mutually_exclusive_group()
    scope_group.add_argument(
        "--all-changes", "-a",
        action="store_const",
        const="all",
        dest="scope",
        help="Show all changes (staged, unstaged, and untracked)"
    )
    scope_group.add_argument(
        "--staged-only", "-s",
        action="store_const",
        const="staged",
        dest="scope",
        help="Show only staged changes"
    )
    scope_group.add_argument(
        "--untracked-only", "-u",
        action="store_const",
        const="untracked",
        dest="scope",
        help="Show only untracked files"
    )
    parser.set_defaults(scope="unstaged")
    
    # Output options
    parser.add_argument(
        "--output-dir", "-o",
        default=".",
        help="Directory to save output files (default: current directory)"
    )
    parser.add_argument(
        "--extensions",
        help="Comma-separated list of file extensions to process (e.g., '.py,.js,.ts')"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    # Process extensions if provided
    allowed_extensions = None
    if args.extensions:
        allowed_extensions = set(ext.strip() for ext in args.extensions.split(','))

    # Create helper and generate reports
    helper = GitDiffHelper(
        allowed_extensions=allowed_extensions,
        output_dir=args.output_dir,
        verbose=args.verbose
    )
    helper.generate_reports(scope=args.scope)

if __name__ == "__main__":
    main()