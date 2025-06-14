# Deploy Library Utility

`deploy_library.py` automates the process of downloading and installing a Python library from a GitHub repository into an isolated virtual environment. It is designed for Windows systems and relies only on the Python standard library and the widely used `requests` package.

## Required Environment Variable

- `PYTHON_LIB_GITHUB_URL` – HTTPS link to the GitHub repository. It can point directly to a `.zip` archive or to the repository root. If the URL is not a zip link, the script appends `/archive/refs/heads/main.zip` by default.

## Installing Dependencies

This project requires Python 3. The only third‑party dependency is `requests`.

```cmd
python -m pip install requests
```

(Optional) Create a virtual environment:

```cmd
python -m venv venv
venv\Scripts\pip install requests
```

## Deploying a Library

1. Set `PYTHON_LIB_GITHUB_URL` to the target repository URL.
2. Run the deployment script:

```cmd
set PYTHON_LIB_GITHUB_URL=https://github.com/user/repo
python deploy_library.py
```

The script downloads the repository, installs it in a temporary virtual environment, and performs a small demonstration run.

## Running Tests

Execute the built‑in unit tests using the standard library `unittest` module:

```cmd
python -m unittest discover -v
```

The tests mock network and subprocess calls, so they run without additional setup.
