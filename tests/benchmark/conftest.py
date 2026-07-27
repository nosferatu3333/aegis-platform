from pathlib import Path
from tempfile import TemporaryDirectory

import pytest


@pytest.fixture
def workspace_tmp():
    with TemporaryDirectory(
        prefix=".benchmark-test-",
        dir=Path.cwd(),
    ) as directory:
        yield Path(directory)
