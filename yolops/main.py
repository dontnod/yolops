#!/usr/bin/env python

import click

from yolops.commands.expire_cache import expire_cache

class Yolops(click.MultiCommand):
    def __init__(self):
        super(Yolops, self).__init__(self)
        self._commands = {
            'expire-cache': expire_cache,
        }

    def list_commands(self, ctx):
        return sorted(self._commands.keys())

    def get_command(self, ctx, name):
        return self._commands[name]
    
main = Yolops()

if __name__ == '__main__':
    main()
