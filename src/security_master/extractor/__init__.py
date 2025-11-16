"""
Extractor package for parsing institution-specific transaction files.

This package contains parsers for:
- Portfolio Performance XML backups
- Wells Fargo CSV exports
- Interactive Brokers Flex Query XML/CSV
- AltoIRA PDF statements
"""

from .pp_xml_parser import PPXMLImporter

__all__ = ["PPXMLImporter"]
