import os
import shutil
from glob import glob
from flask import Flask, render_template, session, request, jsonify, redirect
import markdown

app = Flask(__name__)

PASSWORD = 'bob'

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
    if not session['logged_in']:
        return render_nav_template('auth_error.html')
    pages = get_pages('editable')
    return render_nav_template('admin.html', pages=pages)


@app.route('/new-page', methods=['GET', 'POST'])
def new_page():
    if not session['logged_in']:
        return render_nav_template('auth_error.html')

    if request.method == 'GET':
        return render_nav_template('edit_page.html', post_url='new-page', url='', md_text='')
    elif request.method == 'POST':
        print('POST')
        path = request.form['path']
        md_text = request.form['md_text']
        filename = 'site/{0}'.format(path)
        if os.path.exists(filename + '.md'):
            raise Exception('Page {0} already exists'.format(path))

        # Create:
        with open(filename + '.md', 'w') as f:
            f.write(md_text)
        markdown.markdownFromFile(input=filename + '.md', output=filename + '.html')
        shutil.copyfile(filename + '.html', os.path.join('templates', filename + '.html'))
        return redirect(path)


@app.route('/')
def home():
    return render_nav_template('index.html', page='home')


@app.route('/<path:path>', methods=['GET', 'POST'])
def dispatch(path):
    print(path)
    print(request.method)
    if request.method == 'GET':
        if request.args.get('edit', False):
            if not session['logged_in']:
                return render_nav_template('auth_error.html')
            filename = 'site/{0}.md'.format(path)
            md_text = open(filename, 'r').read()
            return render_nav_template('edit_page.html', post_url=path, url=path, md_text=md_text)
        elif request.args.get('delete', False):
            if not session['logged_in']:
                return render_nav_template('auth_error.html')
            md_filename = 'site/{0}.md'.format(path)
            html_filename = 'site/{0}.html'.format(path)
            template_html_filename = 'templates/site/{0}.html'.format(path)
            for filename in [md_filename, html_filename, template_html_filename]:
                os.remove(filename)

            return redirect('/admin')

        return render_nav_template('page.html', url=path)
    elif request.method == 'POST':
        if not session['logged_in']:
            return render_nav_template('auth_error.html')

        print('POST')
        new_path = request.form['path']
        old_path = request.form['old_path']
        assert old_path == path, '{0} not equal to {1}'.format(old_path, path)
        md_text = request.form['md_text']
        filename = 'site/{0}'.format(new_path)
        if new_path != old_path and os.new_path.exists(filename + '.md'):
            raise Exception('Page {0} already exists'.format(new_path))

        # Overwrite:
        with open(filename + '.md', 'w') as f:
            f.write(md_text)
        markdown.markdownFromFile(input=filename + '.md', output=filename + '.html')
        shutil.copyfile(filename + '.html', os.path.join('templates', filename + '.html'))
        return redirect(new_path)


def get_pages(page_type='all'):
    filenames = glob('templates/site/*.html')
    print(filenames)
    pages = []
    if page_type != 'editable':
        pages.append({'url': '', 'title': 'Home'})
    for filename in filenames:
        url = os.path.splitext(os.path.relpath(filename, 'templates/site'))[0]
        title = ' '.join(url.split('-')).capitalize()
        pages.append({'url': url, 'title': title})
    if page_type != 'editable' and session['logged_in']:
        pages.append({'url': 'admin', 'title': 'Admin'})
    print(pages)
    return pages


def render_nav_template(template, **kwargs):
    pages = get_pages()
    return render_template(template, nav_pages=pages, **kwargs)

# @app.route('/blog/', methods=['GET', 'POST'])
# def blog():
#     if request.method == 'POST':
#         print('POST')
#         title = request.form['title']
#         md_text = request.form['md_text']
#         filename = 'templates/posts/{0}'.format(title)
#         if os.path.exists(filename + '.md'):
#             raise Exception('Post {0} already exists'.format(title))
#         with open(filename + '.md', 'w') as f:
#             f.write(md_text)
#         markdown.markdownFromFile(input=filename + '.md', output=filename + '.html')
#         return redirect('/blog/')
# 
#     # if request.method == 'GET':
#     post_htmls = glob('templates/posts/*.html')
#     posts = [os.path.splitext(os.path.split(p)[-1])[0] for p in post_htmls]
#     print(posts)
#     return render_template('blog.html', page='blog', posts=posts)
# 
# 
# 
# @app.route('/blog/new')
# def new_blog_post():
#     return render_template('new_blog_post.html', page='blog')
# 
# @app.route('/blog/<post>')
# def blog_post(post):
#     if request.args.get('edit', False):
#         filename = 'templates/posts/{0}.md'.format(post)
#         md_text = open(filename, 'r').read()
#         return render_template('edit_blog_post.html', page='blog', post=post, md_text=md_text)
#     else:
#         return render_template('blog_post.html', page='blog', post=post)
# 
# 
# @app.route('/projects/')
# def projects():
#     return render_template('index.html', page='projects')
# 
# 
@app.errorhandler(404)
def page_not_found(error):
        return render_template('404.html'), 404


if __name__ == '__main__':
    app.config['SECRET_KEY'] = 'no-one will guess this!!!!'

    app.debug = True
    app.run()
