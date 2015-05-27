import os
import sys
import fnmatch
import shutil
import markdown
from collections import defaultdict
import ConfigParser
import datetime as dt
from glob import glob

import simplejson

def build_page_structure(key, dirs):
    pages = []
    cfg_filenames = dirs[key]
    for cfg_filename in cfg_filenames:

        cp = ConfigParser.ConfigParser()
        cp.read(cfg_filename)

        order = cp.get('page', 'order')
        page_type = cp.get('page', 'type')
        title = cp.get('page', 'title')

        filename = os.path.splitext(cfg_filename)[0]
        url = filename[filename.find(os.path.sep) + 1:]

        name = os.path.split(filename)[1]
        md_filename = filename + '.md'
        html_filename = filename + '.html'
        if page_type == 'page':
            if os.path.exists(md_filename) or os.path.exists(html_filename):
                pages.append({'name': name, 'title': title, 'url': url, 'order': order, 'type': page_type})
            else:
                raise Exception('Missing md/html for: {0}'.format(cfg_filename))
        elif page_type == 'dir':
            if not os.path.isdir(os.path.splitext(cfg_filename)[0]):
                raise Exception('Missing dir for: {0}'.format(cfg_filename))
            else:
                new_key = os.path.splitext(cfg_filename)[0]
                url = os.path.join(url, 'index')
                assert new_key in dirs
                pages.append({'name': name, 'title': title, 'url': url, 'order': order, 'type': page_type, 
                    'subpages': build_page_structure(new_key, dirs), 'has_subpages': True})
        elif page_type == 'blog_post':
            pass
        else:
            raise Exception('Unknown type: {0}'.format(page_type))

    return sorted(pages, key=lambda v: v['order'])


def main():
    if os.path.exists('json'):
        shutil.rmtree('json')
    if os.path.exists('templates/site'):
        shutil.rmtree('templates/site')

    md_filenames = []
    cfg_filenames = defaultdict(list)
    path = 'site'
    start_depth = path.count(os.path.sep)
    dirs = defaultdict(list)
    for root, dirnames, filenames in os.walk(path, topdown=False):
        depth = root.count(os.path.sep) - start_depth
        if depth > 1:
            raise Exception('Max depth supported is 2')
        for filename in fnmatch.filter(filenames, '*.cfg'):
            cfg_filename = os.path.join(root, filename)
            md_filename = os.path.splitext(cfg_filename)[0] + '.md'
            if os.path.exists(md_filename):
                md_filenames.append(md_filename)
            dirs[root].append(cfg_filename)

    keys_at_depth_zero = filter(lambda d: d.count(os.path.sep) == start_depth, dirs.keys())
    assert len(keys_at_depth_zero) == 1, 'Should only be one key at depth 0'
    key = keys_at_depth_zero[0]

    pages = build_page_structure(key, dirs)
    os.makedirs('json')
    with open('json/pages.json', 'w') as f:
        simplejson.dump(pages, f)

    for md_filename in md_filenames:
        filename = os.path.splitext(md_filename)[0]
        html_filename = filename + '.html'

        if not os.path.exists(html_filename):
            markdown.markdownFromFile(input=md_filename, output=html_filename)

        output_file = os.path.join('templates', html_filename)
        if not os.path.exists(os.path.dirname(output_file)):
            os.makedirs(os.path.dirname(output_file))

        shutil.copyfile(html_filename, output_file)

    posts = []
    post_cfg_filenames = glob('site/posts/*.cfg')
    fmt = '%d/%M/%Y %H:%m:%S'
    for post_cfg_filename in post_cfg_filenames:
        filename = os.path.splitext(post_cfg_filename)[0]
        post_md_filename = filename + '.md'
        if not os.path.exists(post_md_filename):
            raise Exception('Missing md/html for: {0}'.format(post_cfg_filename))
        cp = ConfigParser.ConfigParser()
        cp.read(post_cfg_filename)
        url = filename[filename.find(os.path.sep) + 1:]

        page_type = cp.get('page', 'type')
        date_str = cp.get('page', 'date')
        title = cp.get('page', 'title')
        published = cp.get('page', 'published')
        date = dt.datetime.strptime(date_str, fmt)
        posts.append({'type': page_type, 'title': title, 'published': published, 'date': date, 'url': url})

    posts = sorted(posts, key=lambda p: p['date'])
    for post in posts:
        post['date'] = dt.datetime.strftime(post['date'], fmt)

    with open('json/posts.json', 'w') as f:
        simplejson.dump(posts, f)

if __name__ == '__main__':
    main()
