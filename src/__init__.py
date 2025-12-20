"""Captain's Log - Automatically aggregate git commit messages daily into markdown logs."""

try:
    from importlib.metadata import PackageNotFoundError, version
except ImportError:
    # Python < 3.8 fallback
    from importlib_metadata import PackageNotFoundError, version  # type: ignore

try:
    __version__ = version("git-captains-log")
except PackageNotFoundError:
    # Package is not installed, try to get version from _version.py
    try:
        from ._version import version as __version__  # type: ignore
    except ImportError:
        # Fallback version for development
        __version__ = "0.0.0.dev0+unknown"

__all__ = ["__version__"]
