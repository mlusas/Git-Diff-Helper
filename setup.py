from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

# Explicitly define the packages
packages = find_packages(where="src")
print(f"Found packages: {packages}")
if not packages:
    packages = ["git_diff_helper"]

setup(
    name="git-diff-helper",
    version="0.1.6",
    author="Mitch Lusas",
    author_email="git@mitchlusas.com",
    description="A tool for generating Git diff reports optimized for AI code review",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/mlusas/git-diff-helper",
    package_dir={"": "src"},
    packages=packages,
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Version Control :: Git",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
    python_requires=">=3.6",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "git-diff-helper=git_diff_helper.__main__:run",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)