import datetime as dt
from collections import defaultdict

import simplejson
import markdown

import persistence as p
from settings import SITE, USE_GIT, CACHE

class DisableUpdates(object):
    def __init__(self):
        pass

    def __enter__(self):
        print('enter')
        updater.disable()

    def __exit__(self, type, value, traceback):
        print('exit')
        updater.enable()
        updater.apply_pending_updates()


class Page(p.Model):
    title = p.Field(str)
    order = p.Field(int)
    html_edited = p.Field(bool, default=False)
    html = p.ContentField('html', default='')
    md = p.ContentField('md', default='')

    def save(self):
        if not self.html_edited:
            self.html = markdown.markdown(self.md)
        super(Page, self).save()
        updater.update_site('save page:{0}'.format(self.path))

    def delete(self):
        super(Page, self).delete()
        updater.update_site('delete page:{0}'.format(self.path))

    def change_path(self, new_path):
        super(Page, self).change_path(new_path)
        self.path = new_path
        updater.update_site('change_path page:{0}'.format(self.path))

    def __repr__(self):
        return '<{0}: {1}>'.format(type(self).__name__, self.path)


class Post(p.Model):
    title = p.Field(str)
    summary = p.Field(str)
    date = p.Field(dt.datetime, default=dt.datetime.now())
    published = p.Field(bool, default=False)
    html_edited = p.Field(bool, default=False)
    html = p.ContentField('html', default='')
    md = p.ContentField('md', default='')

    def save(self):
        if not self.html_edited:
            self.html = markdown.markdown(self.md)
        super(Post, self).save()
        updater.update_posts('save post:{0}'.format(self.path))

    def delete(self):
        super(Post, self).delete()
        updater.update_posts('delete post:{0}'.format(self.path))

    def change_path(self, new_path):
        super(Post, self).change_path(new_path)
        self.path = new_path
        updater.update_posts('change_path post:{0}'.format(self.path))

    def __repr__(self):
        return '<{0}: {1}>'.format(type(self).__name__, self.path)

class Dir(p.Model):
    title = p.Field(str)
    order = p.Field(int)
    directory = p.DirField()

    def save(self):
        super(Dir, self).save()
        updater.update_site('save dir:{0}'.format(self.path))

    def delete(self):
        super(Dir, self).delete()
        updater.update_site('delete dir:{0}'.format(self.path))

    def change_path(self, new_path):
        super(Dir, self).change_path(new_path)
        self.path = new_path
        updater.update_posts('change_path dir:{0}'.format(self.path))

    def __repr__(self):
        return '<{0}: {1}>'.format(type(self).__name__, self.path)

class Updater(object):
    def __init__(self):
        self.pending_updates = defaultdict(list)
        self.enabled = True

    def disable(self):
        self.enabled = False

    def enable(self):
        self.enabled = True

    def apply_pending_updates(self):
        if 'site' in self.pending_updates:
            self.update_posts('\n'.join(self.pending_updates.pop('site')))
        if 'posts' in self.pending_updates:
            self.update_posts('\n'.join(self.pending_updates.pop('posts')))

    def update_site(self, message=''):
        if not self.enabled:
            self.pending_updates['site'].append(message)
            return
        print('update_site:{0}'.format(message))
        all_pages_dirs = Page.objects.filter(path__not__contains='/')
        dirs = Dir.objects.all()
        all_pages_dirs.extend(dirs)
        all_pages_dirs.sort(key=lambda p: p.order)

        json_pages = []
        for pd in all_pages_dirs:
            if isinstance(pd, Page):
                json_pages.append({'title': pd.title, 
                                   'path': '/' + pd.path,
                                   'order': pd.order,
                                   'type': 'Page'})
            elif isinstance(pd, Dir):
                dir_pages = Page.objects.filter(path__contains=pd.path)
                dir_pages.sort(key=lambda p: p.order)
                subpages = []
                for d in dir_pages:
                    subpages.append({'title': d.title, 
                                     'path': '/' + d.path,
                                     'order': d.order,
                                     'type': 'Page'})
                json_pages.append({'title': pd.title, 
                                   'path': '/' + pd.path,
                                   'order': pd.order,
                                   'has_subpages': True,
                                   'subpages': subpages,
                                   'type': 'Dir'})

        with open('json/pages.json', 'w') as f:
            simplejson.dump(json_pages, f)

        if USE_GIT:
            import git
            repo = git.Repo(SITE)
            repo.git.add('-A')
            if repo.git.status('--porcelain') != '':
                repo.git.add('-A')
                repo.git.commit(m=message)

        cache = p.Cache()
        cache.clear()


    def update_posts(self, message=''):
        if not self.enabled:
            self.pending_updates['posts'].append(message)
            return
        print('update_posts:{0}'.format(message))
        posts = Post.objects.all(order_by='date')
        json_posts = []
        for post in posts:
            date = dt.datetime.strftime(post.date, p.DATE_FMT)
            json_posts.append({'type': 'Post', 
                               'title': post.title,
                               'published': post.published,
                               'date': date,
                               'summary': post.summary,
                               'path': '/' + post.path})
        with open('json/posts.json', 'w') as f:
            simplejson.dump(json_posts, f)

        if USE_GIT:
            import git
            repo = git.Repo(SITE)
            if repo.git.status('--porcelain') != '':
                repo.git.add('-A')
                repo.git.commit(m=message)

        cache = p.Cache()
        cache.clear()

updater = Updater()
