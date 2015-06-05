import os
import shutil
from glob import glob
import ConfigParser
import datetime as dt
import logging
from logging.handlers import RotatingFileHandler
from logging import Formatter

import simplejson
import markdown
from flask import Flask, render_template, session, request, jsonify, redirect

from models import Page, Post, Dir
import persistence
from secret_settings import PASSWORD, SECRET_KEY

app = Flask(__name__)
app.config['SECRET_KEY'] = SECRET_KEY

handler = RotatingFileHandler('logs/1000earths.log',
                              maxBytes=10000, 
                              backupCount=3)
handler.setLevel(logging.INFO)
handler.setFormatter(Formatter(
    '%(asctime)s %(levelname)s: %(message)s '
    '[in %(pathname)s:%(lineno)d]'
))
app.logger.addHandler(handler)

cache = persistence.Cache()


def _logged_in(session):
    if 'logged_in' in session:
        if session['logged_in']:
            return True
    return False


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['password'] == PASSWORD:
            session['logged_in'] = True
        return redirect('/')
    elif request.method == 'GET':
        return render_nav_template('login.html', page='login')


@app.route('/logout')
def logout():
    session['logged_in'] = False
    return redirect('/')


@app.route('/admin')
def admin():
    if not _logged_in(session):
        return render_nav_template('auth_error.html')
    pages = get_pages('editable')
    return render_nav_template('admin.html', pages=pages)


@app.route('/')
def home():
    if not _logged_in(session) and cache.contains('/home'):
        return cache.get('/home')
    return render_nav_template('index.html', page='home')


@app.route('/blog')
def blog():
    # if not _logged_in(session) and cache.contains('/blog-page'):
        # return cache.get('/blog-page')

    with open('json/posts.json', 'r') as f:
        posts = simplejson.load(f)
    posts_per_page = 8
    num_pages = len(posts) / posts_per_page
    curr_page = int(request.args.get('page', 0))
    prev_page = curr_page - 1
    next_page = curr_page + 1
    s = slice(curr_page * posts_per_page, next_page * posts_per_page)

    return render_nav_template('blog.html', page='blog', posts=posts[::-1][s],
                               prev_page=prev_page,
                               curr_page=curr_page,
                               next_page=next_page, 
                               num_pages=num_pages, 
                               is_last_page=curr_page == num_pages,
                               is_first_page=curr_page == 0)


@app.route('/<path:path>', methods=['GET', 'POST'])
def page(path):
    if not _logged_in(session) and cache.contains(request.path):
        app.logger.debug('returning cached {}'.format(request.path))
        return cache.get(request.path)

    is_new = path in ['new-page', 'new-post', 'new-dir']

    if is_new:
        page_type = path.split('-')[1].capitalize()
        if page_type == 'Page':
            page = Page(path='', title='', order=0)
        elif page_type == 'Post':
            page = Post(path='', title='', date=dt.datetime.now(), summary='')
        elif page_type == 'Dir':
            page = Dir(path='', title='', order=0, directory='')
    else:
        page_type = persistence.get_model_type(path)
        if page_type == 'Page':
            page = Page.objects.get(path)
        elif page_type == 'Post':
            page = Post.objects.get(path)
        elif page_type == 'Dir':
            page = Dir.objects.get(path)
    app.logger.info('is_new: {0}, page_type: {1}'.format(is_new, page_type))

    if request.method == 'GET':
        markup = request.args.get('edit', False)
        if page_type in ['Page', 'Post'] and markup in ['html', 'md']:
            if not _logged_in(session):
                return render_nav_template('auth_error.html')
            text = getattr(page, markup)

            return render_nav_template('edit_page.html', 
                                       page=page, text=text, markup=markup, post_path=path)
        elif page_type == 'Dir':
            return render_nav_template('edit_dir.html', 
                                       directory=page, post_path=path)


        if page_type == 'Post':
            return render_nav_template('blog_post.html', post=page)
        else:
            return render_nav_template('page.html', page=page)

    elif request.method == 'POST':
        if not _logged_in(session):
            return render_nav_template('auth_error.html')

        if request.args.get('delete', False):
            page.delete()
            return redirect('/admin')

        new_path = request.form['path']
        old_path = request.form['old_path']
        if is_new:
            page.path = new_path
        elif new_path != old_path:
            page.change_path(new_path)

        page.title = request.form['title']

        if page_type in ['Page', 'Dir']:
            page.order = int(request.form['order'])
        elif page_type == 'Post':
            page.date = dt.datetime.now()
            page.summary = request.form['summary']
            if 'published' in request.form:
                page.published = request.form['published'] == 'on'
            else:
                page.published = False

        if page_type in ['Page', 'Post']:
            if request.form['markup'] == 'md':
                page.md = request.form['text']
                page.html_edited = False
            elif request.form['markup'] == 'html':
                page.html = request.form['text']
                page.html_edited = True

        try:
            page.save()
        except Exception as e:
            app.logger.error('Problem saving page {}: {}'.format(page, e))
            raise

        return redirect(page.path)


@app.template_filter('datefmt')
def _jinja2_filter_datetime(date):
    if isinstance(date, str):
        fmt = persistence.DATE_FMT
        date = dt.datetime.strptime(date, fmt)
    native = date.replace(tzinfo=None)
    out_fmt = '%b %-d{0}, %Y'

    stndrd = {1: 'st', 2: 'nd', 3: 'rd'}
    if native.day % 10 in stndrd:
        ending = stndrd[native.day]
    else:
        ending = 'th'

    return native.strftime(out_fmt).format(ending)


def get_pages(page_type='all'):
    with open('json/pages.json', 'r') as f:
        pages = simplejson.load(f)
    if page_type != 'editable':
        pages.insert(0, {'path': '/', 'title': 'Home'})
        if _logged_in(session):
            pages.append({'path': '/admin', 'title': 'Admin'})
    return pages


def render_nav_template(template, **kwargs):
    pages = get_pages()
    html = render_template(template, path=request.path, nav_pages=pages, **kwargs)
    if not _logged_in(session):
        if request.path == '/':
            path = '/home'
        elif request.path == '/blog':
            path = '/blog-page'
        else:
            path = request.path
        cache.set(path, html)
    return html


@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404


if __name__ == '__main__':
    app.debug = True
    app.run(host='0.0.0.0')
