# Github Sync NoAdmin

This project contains a script for downloading a Python library from a GitHub repository, installing it into a temporary virtual environment and cleaning up afterwards. It is intended for quick demonstrations or pet projects on a single machine.

## Environment Variables

- `PYTHON_LIB_GITHUB_URL` – **required**. URL to the GitHub repository or a direct link to the zip archive.
- `PYTHON_LIB_BRANCH` – optional. Branch name to use when forming the archive URL if the repository URL does not already point to a zip file. Defaults to `main`.

## Running Tests

Use `python -m pytest` from the repository root to run the automated tests.
