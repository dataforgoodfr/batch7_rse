#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys
import enum
import argparse


def module_name(value):
    base_settings_module = 'batch7rse.settings'
    return '.'.join((base_settings_module, value))


def main():
    # parser = argparse.ArgumentParser()
    # parser.add_argument('--settings-file',
    #                     dest="settings",
    #                     default="prod",
    #                     choices=["dev", "prod"])
    # parser.parse_args()
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', "batch7rse.settings.prod")  # parser.settings)
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
