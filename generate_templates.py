import os
import sys
import fnmatch
import markdown
from collections import defaultdict
import ConfigParser
import datetime as dt
from glob import glob

import simplejson

PAGE_FIELDS = ['type', 'order', 'title']
POST_FIELDS = ['type', 'title', 'date', 'published']

def read_page(page_name, content=True):
    return _read(page_name, 'page', PAGE_FIELDS, content)

def save_page(page):
    _save(page, 'page', PAGE_FIELDS)

def delete_page(page_name):
    _delete(page_name, 'page')

def read_post(post_name, content=True):
    return _read(post_name, 'post', POST_FIELDS, content)

def save_post(post):
    _save(post, 'post', POST_FIELDS)

def delete_post(post_name):
    _delete(post_name, 'post')

def _read(name, page_type, fields, content):
    cfg_filename = 'site/{0}.cfg'.format(name)
    html_filename = 'site/{0}.html'.format(name)
    md_filename = 'site/{0}.md'.format(name)
    page = {'name': name, 'path': '/' + name}
    cp = ConfigParser.ConfigParser()
    cp.read(cfg_filename)

    for field in fields:
        page[field] = cp.get(page_type, field)

    if content:
        with open(html_filename, 'r') as f:
            page['html'] = f.read()
        with open(md_filename, 'r') as f:
            page['md'] = f.read()
    return page


def _save(page, page_type, fields):
    cfg_filename = 'site/{0}.cfg'.format(page['name'])
    html_filename = 'site/{0}.html'.format(page['name'])
    md_filename = 'site/{0}.md'.format(page['name'])

    cp = ConfigParser.ConfigParser()
    cp.read(cfg_filename)

    if 'new_name' in page:
        # Handle name changes
        raise NotImplemented()

    for field in fields:
        cp.set(page_type, field, page[field])
    if 'html_edited' in page:
        cp.set(page_type, 'html_edited', True)
        with open(html_filename, 'w') as f:
            f.write(page['html'])
    else:
        with open(md_filename, 'w') as f:
            f.write(page['md'])
        markdown.markdownFromFile(input=md_filename, output=html_filename)

    with open(cfg_filename, 'w') as f:
        cp.write(f)

    if page_type == 'post':
        posts()
    elif page_type == 'page':
        site()


def _delete(name, page_type):
    cfg_filename = 'site/{0}.cfg'.format(name)
    md_filename = 'site/{0}.md'.format(name)
    html_filename = 'site/{0}.html'.format(name)
    for filename in [cfg_filename, md_filename, html_filename]:
        os.remove(filename)
    if page_type == 'page':
        site()
    elif page_type == 'post':
        posts()

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
        path = filename[filename.find(os.path.sep) + 1:]

        name = os.path.split(filename)[1]
        md_filename = filename + '.md'
        html_filename = filename + '.html'
        if page_type == 'page':
            if os.path.exists(md_filename) or os.path.exists(html_filename):
                pages.append({'name': name, 'title': title, 'path': '/' + path, 'order': order, 'type': page_type})
            else:
                raise Exception('Missing md/html for: {0}'.format(cfg_filename))
        elif page_type == 'dir':
            if not os.path.isdir(os.path.splitext(cfg_filename)[0]):
                raise Exception('Missing dir for: {0}'.format(cfg_filename))
            else:
                new_key = os.path.splitext(cfg_filename)[0]
                path = os.path.join(path, 'index')
                assert new_key in dirs
                pages.append({'name': name, 'title': title, 'path': '/' + path, 'order': order, 'type': page_type, 
                    'subpages': build_page_structure(new_key, dirs), 'has_subpages': True})
        elif page_type == 'blog_post':
            pass
        else:
            raise Exception('Unknown type: {0}'.format(page_type))

    return sorted(pages, key=lambda v: v['order'])


def main():
    if not os.path.exists('json'):
        os.makedirs('json')
    posts(clean=False)
    site(clean=False)


def site(clean=True):
    if clean:
        if os.path.exists('json/pages.json'):
            os.remove('json/pages.json')

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
    with open('json/pages.json', 'w') as f:
        simplejson.dump(pages, f)

    for md_filename in md_filenames:
        filename = os.path.splitext(md_filename)[0]
        html_filename = filename + '.html'

        if not os.path.exists(html_filename):
            markdown.markdownFromFile(input=md_filename, output=html_filename)

def posts(clean=True):
    if clean:
        if os.path.exists('json/posts.json'):
            os.remove('json/posts.json')
    posts = []
    post_cfg_filenames = glob('site/posts/*.cfg')
    fmt = '%d/%m/%Y %H:%M:%S'
    for post_cfg_filename in post_cfg_filenames:
        filename = os.path.splitext(post_cfg_filename)[0]
        post_md_filename = filename + '.md'
        if not os.path.exists(post_md_filename):
            raise Exception('Missing md/html for: {0}'.format(post_cfg_filename))
        cp = ConfigParser.ConfigParser()
        cp.read(post_cfg_filename)
        path = filename[filename.find(os.path.sep) + 1:]

        # post = read_post(filename
        page_type = cp.get('post', 'type')
        date_str = cp.get('post', 'date')
        title = cp.get('post', 'title')
        published = cp.get('post', 'published')
        date = dt.datetime.strptime(date_str, fmt)
        posts.append({'type': page_type, 'title': title, 'published': published, 'date': date, 'path': '/' + path})

    posts = sorted(posts, key=lambda p: p['date'])
    for post in posts:
        post['date'] = dt.datetime.strftime(post['date'], fmt)

    with open('json/posts.json', 'w') as f:
        simplejson.dump(posts, f)

if __name__ == '__main__':
    main()
