"""Salla — Market basket analysis desktop application.

The package initializer stays free of Qt imports on purpose: packaging tools
import this module in an isolated subprocess, and loading Qt there is
unnecessary (and fragile on Windows).
"""

__version__ = "1.0.0"

__all__ = ["__version__"]
