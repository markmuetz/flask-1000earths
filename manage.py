#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK
from commandify import commandify, command, main_command
import models


@command
def update_posts():
    models.update_posts()


@command
def update_site():
    models.update_site()


@command
def update_all():
    models.update_posts()
    models.update_site()


@main_command
def main():
    pass


if __name__ == '__main__':
    commandify(use_argcomplete=True)
