from setuptools import setup

setup(
    name="framediff",
    version="1.0.0",
    description="Compliance document diff tool — framework-aware comparison for FedRAMP, NIST, CMMC, ISO 27001, SOC 2",
    long_description=open("README.md").read() if __import__("os").path.exists("README.md") else "",
    long_description_content_type="text/markdown",
    author="FrameDiff Contributors",
    license="MIT",
    python_requires=">=3.10",
    py_modules=[
        "__init__",
        "main",
        "framediff",
        "helpers",
        "control_models",
        "control_parser",
        "diff_engine",
        "terminal_report",
        "json_report",
        "markdown_report",
        "html_report",
    ],
    install_requires=[
        "python-docx>=1.0",
        "PyYAML>=6.0",
    ],
    extras_require={
        "pdf": ["pypdf>=3.0"],
        "rich": ["rich>=13.0"],
    },
    entry_points={
        "console_scripts": [
            "framediff=main:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: MIT License",
        "Topic :: Security",
        "Topic :: Utilities",
    ],
)
