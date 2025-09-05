"""
Random polynomial function generator for R1CS circuit optimization.

Main entry point for generating random polynomial instances.
"""

from .instance_generator import generate_random_instance
from .chooser import choose_m_n

__version__ = "0.1.0"
__all__ = ["generate_random_instance", "choose_m_n"]