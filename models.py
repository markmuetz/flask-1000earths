import datetime as dt

import persistence as p


class Page(p.Model):
    title = p.Field(str)
    order = p.Field(int)
    html = p.ContentField('html')
    md = p.ContentField('md')

    def __repr__(self):
        return '<{0}: {1}>'.format(type(self).__name__, self.path)


class Post(p.Model):
    title = p.Field(str)
    date = p.Field(dt.datetime)
    published = p.Field(bool)
    html = p.ContentField('html')
    md = p.ContentField('md')

    def __repr__(self):
        return '<{0}: {1}>'.format(type(self).__name__, self.path)
