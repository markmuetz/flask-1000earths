#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK
import os
import shutil
import ConfigParser

import generate_templates
from commandify import command, main_command, commandify

@command
def new(path, title, order, content=None):
    os.chdir('site')

    cp = ConfigParser.ConfigParser()
    cp.add_section('page')
    cp.set('page', 'type', 'page')
    cp.set('page', 'title', title)
    cp.set('page', 'order', order)
    with open(path + '.cfg', 'w') as f:
        cp.write(f)

    with open(path + '.md', 'w') as f:
        if content:
            f.write(content)
        else:
            f.write('# {0}'.format(title))

    os.chdir('..')

    generate_templates.main()


@command
def new_dir(dir_path, dir_title, path, title, order, content=None):
    os.chdir('site')

    cp = ConfigParser.ConfigParser()
    cp.add_section('page')
    cp.set('page', 'type', 'dir')
    cp.set('page', 'title', dir_title)
    cp.set('page', 'order', order)
    with open(dir_path + '.cfg', 'w') as f:
        cp.write(f)

    os.makedirs(dir_path)

    os.chdir('..')

    new(path, title, order, content)


@command
def rm(path, is_dir=False):
    cmd = raw_input('Are you sure you want to remove {0} [y/n]: '.format(path))
    if cmd == 'y':
        os.chdir('site')
        if os.path.exists(path + '.md'):
            os.remove(path + '.md')
        if os.path.exists(path + '.html'):
            os.remove(path + '.html')
        if os.path.exists(path + '.cfg'):
            os.remove(path + '.cfg')
        os.chdir('..')
        generate_templates.main()


@command
def rm_dir(path):
    cmd = raw_input('Are you sure you want to remove {0} [y/n]: '.format(path))
    if cmd == 'y':
        if os.path.exists(path + '.cfg'):
            os.remove(path + '.cfg')
        if os.path.exists(path):
            shutil.rmtree(path)

        os.chdir('..')
        generate_templates.main()


@main_command
def main():
    pass


if __name__ == '__main__':
    commandify(use_argcomplete=True)
