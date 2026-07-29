# Repository validation

AEGIS Platform uses Python 3.11 as its authoritative CI baseline. The package
declares Python 3.11 or newer, and CI validates the minimum supported version.

## Mandatory local setup

Create an isolated environment from the repository root and install the
declared test extra:

```powershell
python -m venv env
.\env\Scripts\python.exe -m pip install --upgrade pip
.\env\Scripts\python.exe -m pip install -e ".[test]"
```

On POSIX systems, replace the interpreter path with `env/bin/python`.
Dependencies are declared in `pyproject.toml`; no requirements or lock file is
currently part of the repository contract.

## Mandatory validation

Windows:

```powershell
.\env\Scripts\python.exe scripts\validate.py
```

POSIX:

```shell
env/bin/python scripts/validate.py
```

The script prints the selected interpreter and stops on the first failure. It
runs dependency integrity, pre-commit configuration validation, Ruff lint,
Ruff format verification, the complete pytest suite, and Git whitespace
validation. It does not format, stage, commit, push, or run external product
actions.

If a repository environment exists, the script rejects a `python` executable
from another project. `--allow-external-interpreter` is reserved for an
explicitly isolated CI or temporary validation environment.

To inspect interpreter selection manually:

```powershell
Get-Command python
python -c "import sys; print(sys.executable)"
.\env\Scripts\python.exe -c "import sys; print(sys.executable)"
```

## Optional pre-commit convenience

After installing the test extra:

```powershell
.\env\Scripts\python.exe -m pre_commit install
.\env\Scripts\python.exe -m pre_commit run --all-files
```

The repository validation script remains the authoritative local command.
Pre-commit hooks use the same Ruff configuration from `pyproject.toml`.

## Continuous integration

The `Repository validation` GitHub Actions workflow runs for every push and
pull request. It uses Ubuntu, Python 3.11, a read-only repository permission,
and no secrets, deployment, external execution, or dependency cache. It
installs `.[test]`, runs the canonical validation script, and confirms that
validation changed no tracked files.

## Windows troubleshooting

The current workstation's bare `python` may resolve to another AEGIS
repository even when this repository appears active. Invoke
`.\env\Scripts\python.exe` explicitly; the validation script will reject the
wrong interpreter.

The local `.pytest_cache` directory may produce `WinError 183` or access-denied
warnings because its filesystem permissions are invalid. It is ignored by Git.
The canonical validation disables only pytest's optional cache provider, so
test collection and results are unaffected. To restore local caching, close
processes using the repository and remove/recreate only `.pytest_cache` using
an account with permission to that directory.

## Line endings and generated artifacts

`.gitattributes` stores text as LF by default, keeps shell scripts on LF, and
uses CRLF only for PowerShell and Windows command files. This policy applies to
future Git operations and is not a request for bulk renormalization.

Do not commit these local or generated artifacts:

- virtual environments and `.env` files;
- `*.egg-info/`, `build/`, and `dist/`;
- `.pytest_cache/`, `.ruff_cache/`, `__pycache__/`, and `*.pyc`;
- `.coverage`, `.coverage.*`, and `htmlcov/`;
- `aegis_state.json`, logs, or benchmark report output.
