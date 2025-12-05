#!/usr/bin/env python
"""
Simple CLI wrapper for running database audits
Usage: python audit.py [config_file] [options]

This file provides backward compatibility for users running the script directly.
The actual implementation is in dw_auditor.cli.main
"""

from dw_auditor.cli.main import main

if __name__ == '__main__':
    main()
