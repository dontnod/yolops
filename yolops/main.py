#!/usr/bin/env python

import click

from yolops.log import verbosity_params
from yolops.commands.expire_cache import expire_cache
from yolops.commands.p4 import p4_group


_commands = {
    'expire-cache': expire_cache,
    'p4': p4_group,
}


class Yolops(click.MultiCommand):

    def list_commands(self, ctx):
        return sorted(_commands.keys())

    def get_command(self, ctx, name):
        return _commands[name]

    
@click.command(cls=Yolops)
@verbosity_params
def main():
    pass


if __name__ == '__main__':
    main()
