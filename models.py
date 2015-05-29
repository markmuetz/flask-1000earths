import datetime as dt

import simplejson
import markdown

import persistence as p


class Page(p.Model):
    title = p.Field(str)
    order = p.Field(int)
    html_edited = p.Field(bool)
    html = p.ContentField('html')
    md = p.ContentField('md')

    def save(self):
        if not self.html_edited:
            self.html = markdown.markdown(self.md)
        super(Page, self).save()
        update_site()

    def delete(self):
        super(Page, self).delete()
        update_site()

    def __repr__(self):
        return '<{0}: {1}>'.format(type(self).__name__, self.path)


class Post(p.Model):
    title = p.Field(str)
    date = p.Field(dt.datetime)
    published = p.Field(bool)
    html_edited = p.Field(bool)
    html = p.ContentField('html')
    md = p.ContentField('md')

    def save(self):
        if not self.html_edited:
            self.html = markdown.markdown(self.md)
        super(Post, self).save()
        update_posts()

    def delete(self):
        super(Post, self).delete()
        update_post()

    def __repr__(self):
        return '<{0}: {1}>'.format(type(self).__name__, self.path)

class Dir(p.Model):
    title = p.Field(str)
    order = p.Field(int)
    directory = p.DirField()

    def save(self):
        super(Dir, self).save()
        update_site()

    def delete(self):
        super(Dir, self).delete()
        update_site()

    def __repr__(self):
        return '<{0}: {1}>'.format(type(self).__name__, self.path)

def update_site():
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



def update_posts():
    posts = Post.objects.all(order_by='date')
    json_posts = []
    for post in posts:
        date = dt.datetime.strftime(post.date, p.DATE_FMT)
        json_posts.append({'type': 'Post', 
                           'title': post.title,
                           'published': post.published,
                           'date': date,
                           'path': '/' + post.path})
    with open('json/posts.json', 'w') as f:
        simplejson.dump(json_posts, f)

