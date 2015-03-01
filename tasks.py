import sys

from invoke import run, task


@task
def docs(watch=False, warn=False):
    if watch:
        return watcher(docs)
    run('make -C docs/ html', warn=warn)


@task
def test(path=None, coverage=False, watch=False, warn=False):
    if watch:
        return watcher(test, path=path, coverage=coverage)
    path = path or 'tests/'
    cmd = 'nosetests'
    if coverage:
        cmd += (
            ' --with-coverage --cover-package=mopidy'
            ' --cover-branches --cover-html')
    cmd += ' %s' % path
    run(cmd, pty=True, warn=warn)


@task
def lint(watch=False, warn=False):
    if watch:
        return watcher(lint)
    run('flake8 mopidy tests', warn=warn)


@task
def update_authors():
    # Keep authors in the order of appearance and use awk to filter out dupes
    run("git log --format='- %aN <%aE>' --reverse | awk '!x[$0]++' > AUTHORS")


def watcher(task, *args, **kwargs):
    while True:
        run('clear')
        kwargs['warn'] = True
        task(*args, **kwargs)
        try:
            run(
                'inotifywait -q -e create -e modify -e delete '
                '--exclude ".*\.(pyc|sw.)" -r docs/ mopidy/ tests/')
        except KeyboardInterrupt:
            sys.exit()
