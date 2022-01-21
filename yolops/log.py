import click
import functools

verbosity = 1


# Allow multiple click commands to use the same parameters. This lets us use --verbose in both
# the main executable and the subcommands. See https://github.com/pallets/click/issues/108
def verbosity_params(f):
    @click.option('-v', '--verbose', 'verbosity', flag_value=2, help='Verbose output.')
    @click.option('-q', '--quiet',   'verbosity', flag_value=0, help='Quiet output.')
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        v = kwargs.get('verbosity')
        if v is not None:
            global verbosity
            verbosity = v
        del kwargs['verbosity']
        return f(*args, **kwargs)
    return wrapper


def info(*args, **kwargs):
    if verbosity >= 1:
        return click.echo(*args, **kwargs)


def debug(*args, **kwargs):
    if verbosity >= 2:
        return click.echo(*args, **kwargs)
