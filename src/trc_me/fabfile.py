from fabric.api import cd, env, local, put, run

env.hosts = [
    'foo@trc.me',
]


def test():
    local('./manage.py test accounts', capture=False)
    local('./manage.py test core', capture=False)
    local('./manage.py test web', capture=False)


def pack():
    local('cd ../../ && git archive --format=tar HEAD | gzip > ~/tmp/trc_me.tar.gz')


def prepare_deploy():
    test()
    pack()


def upload():
    put('~/tmp/trc_me.tar.gz', '~/tmp/')


def stage():
    upload()
    with cd('~/src/staging_trc_me/'):
        # Untar version-controlled files
        run('tar -xzf ~/tmp/trc_me.tar.gz')
        # Synchronise media/{css,js,img}
        run('rsync -a --delete src/trc_me/media/* ~/public_html/media.trc.me/staging_trc_me/')
        # Delete media under src
        run('rm -rf src/trc_me/media')


def deploy():
    upload()
    with cd('~/src/trc_me/'):
        run('tar -xzf ~/tmp/trc_me.tar.gz')
        run('rsync -a --delete src/trc_me/media/* ~/public_html/media.trc.me/trc_me/')
        run('rm -rf src/trc_me/media')


#def stage_clean_db():
#    stage()
#    with cd('~/src/staging_trc_me/src/trc_me/'):
#        run('source ~/python_virtualenv/bin/activate && PYTHONPATH=~/src/staging_trc_me/src/ ./manage.py syncdb')
#    with cd('~/public_html/media.trc.me/staging_trc_me/'):
#        run('rm -rf {flag,profile,tag}/*')


#def deploy_clean_db():
#    deploy()
#    with cd('~/src/trc_me/src/trc_me/'):
#        run('source ~/python_virtualenv/bin/activate && PYTHONPATH=~/src/trc_me/src/ ./manage.py syncdb')
#    with cd('~/public_html/media.trc.me/trc_me/'):
#        run('rm -rf {flag,profile,tag}/*')
