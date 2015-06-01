#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK
from commandify import commandify, command, main_command
import models


@command
def update_posts():
    updater = models.Updater()
    updater.update_posts('manual')


@command
def update_site():
    updater = models.Updater()
    updater.update_site('manual')


@command
def update_all():
    updater = models.Updater()
    updater.update_site('manual')
    updater.update_posts('manual')


@main_command
def main():
    pass


if __name__ == '__main__':
    commandify(use_argcomplete=True)
