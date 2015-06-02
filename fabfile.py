from __future__ import print_function
from fabric.api import env, run, cd, settings, sudo, put, execute, task, prefix, get


@task
def initial_setup():
    with cd('Projects'):
        run('git clone https://github.com/markmuetz/flask-1000earths.git')
        with cd('flask-1000earths'):
            run('virtualenv .env')
            with prefix('source .env/bin/activate'):
                run('pip install -U pip')
                run('pip install -r requirements_deployment.txt')
    setup_supervisor()
    setup_nginx()


@task 
def setup_supervisor():
    sudo('ln -s Projects/flask-1000earths/supervisor_1000earths.ini /etc/supervisor/conf.d/')
    sudo('service supervisor restart')

@task 
def setup_nginx():
    sudo('ln -s Projects/flask-1000earths/nginx_1000earths.conf /etc/nginx/sites-enabled/')
    sudo('service nginx restart')


def deploy():
    with cd('Projects/flask-1000earths'):
        run('git fetch')
        run('git merge origin/master')
        with prefix('source .env/bin/activate'):
            run('pip install -r requirements_deployment.txt')
    sudo('supervisorctl restart 1000earths')

