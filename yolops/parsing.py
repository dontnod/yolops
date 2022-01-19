import click
import re

class StorageUnit(click.ParamType):
    name = 'size'

    def convert(self, value, param, ctx):
        if isinstance(value, int):
            return value

        try:
            m = re.match('^([0-9.]+)(|[KMGTPEZY](|B|iB))$', value)
            if m:
                count, prefix, suffix = m.groups(1)
                ret = float(count)
                if prefix:
                    power = 'KMGTPEZY'.index(prefix[0])
                    ret *= pow(1024 if suffix == 'iB' else 1000, power + 1)
                return int(ret)
            else:
                self.fail(f'unknown storage unit {value!r}', param, ctx)
        except ValueError:
            self.fail(f'{value!r} is not a valid storage unit', param, ctx)
