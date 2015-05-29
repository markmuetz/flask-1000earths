import os
import shutil
from glob import glob
import ConfigParser
import datetime as dt

import simplejson
import markdown
from flask import Flask, render_template, session, request, jsonify, redirect

from models import Page, Post, Dir
import persistence

app = Flask(__name__)

PASSWORD = 'bob'


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


@app.route('/new-page', methods=['GET', 'POST'])
def new_page():
    if not _logged_in(session):
        return render_nav_template('auth_error.html')

    if request.method == 'GET':
        return render_nav_template('edit_page.html', post_path='new-page', md_text='')
    elif request.method == 'POST':
        path = request.form['path']
        md_text = request.form['md_text']

        return redirect(path)


@app.route('/')
def home():
    return render_nav_template('index.html', page='home')


@app.route('/blog')
def blog():
    with open('json/posts.json', 'r') as f:
        posts = simplejson.load(f)
    return render_nav_template('blog.html', page='blog', posts=posts)


@app.route('/<path:path>', methods=['GET', 'POST'])
def page(path):
    is_blog_post = os.path.split(path)[0] == 'blog'

    if is_blog_post:
        page = Post.objects.get(path)
    else:
        page = Page.objects.get(path)

    if request.method == 'GET':
        markup = request.args.get('edit', False)
        if markup in ['html', 'md']:
            if not _logged_in(session):
                return render_nav_template('auth_error.html')
            text = getattr(page, markup)
            return render_nav_template('edit_page.html', page_type='post',
                                       page=page, text=text, markup=markup, post_path=path)

        if is_blog_post:
            return render_nav_template('blog_post.html', post=page)
        else:
            return render_nav_template('page.html', page=page)

    elif request.method == 'POST':
        if not _logged_in(session):
            return render_nav_template('auth_error.html')

        if request.args.get('delete', False):
            if not _logged_in(session):
                return render_nav_template('auth_error.html')

            page.delete()

            return redirect('/admin')

        new_path = request.form['path']
        old_path = request.form['old_path']
        if new_path != old_path:
            # page_args['path'] = new_name
            # !
            pass

        if request.form['markup'] == 'md':
            page.md = request.form['text']
            page.html_edited = False

        elif request.form['markup'] == 'html':
            page.html = request.form['text']
            page.html_edited = True

        page.save()

        return redirect(page.path)


@app.template_filter('datefmt')
def _jinja2_filter_datetime(date):
    if isinstance(date, str):
        fmt = persistence.DATE_FMT
        date = dt.datetime.strptime(date, fmt)
    native = date.replace(tzinfo=None)
    out_fmt = '%b %d, %Y'
    return native.strftime(out_fmt) 


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
    return render_template(template, path=request.path, nav_pages=pages, **kwargs)


@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404


if __name__ == '__main__':
    app.config['SECRET_KEY'] = 'no-one will guess this!!!!'

    app.debug = True
    app.run(host='0.0.0.0')
