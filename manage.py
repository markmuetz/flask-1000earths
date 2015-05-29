#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK
from commandify import commandify, command, main_command
import models


@command
def update_posts():
    models.update_posts('manual')


@command
def update_site():
    models.update_site('manual')


@command
def update_all():
    models.update_posts('manual')
    models.update_site('manual')


@main_command
def main():
    pass


if __name__ == '__main__':
    commandify(use_argcomplete=True)
