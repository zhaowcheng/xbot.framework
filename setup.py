# Build hook: generate long_description from README files,
# stripping language-switcher headers.
# All other metadata lives in pyproject.toml.

from setuptools import setup


def _build_long_description() -> str:
    desc = ""
    for readme in ("README.md", "README.zh.md"):
        if desc:
            desc += "\n***\n\n"
        with open(readme, encoding="utf8") as f:
            desc += "".join(f.readlines()[6:])
    return desc


setup(
    long_description=_build_long_description(),
    long_description_content_type="text/markdown",
)
