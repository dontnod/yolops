from subprocess import Popen, PIPE, DEVNULL
import click
import re

from yolops.log import verbosity_params, info, debug

class P4Server():
    def __init__(self, t: str, name: str, config: dict):
        self.type = t
        self.name = name
        self.config = {}
        for item in config:
            k, v = item.split('=')[0:2]
            self.config[k] = v
        self._read_config()

    def _read_config(self):
        """
        Parse the output of ‘p4d -cshow’ to populate the Perforce server configuration
        """
        try:
            parse = re.compile(f'(any|{self.name}): ([^=]*) = (.*)')
            process = Popen(['p4d', '-r', self.config['root'], '-cshow'],
                            stdout=PIPE, stderr=DEVNULL, text=True, close_fds=True)
            for line in iter(process.stdout.readline, ''):
                m = parse.match(line)
                if m:
                    _, k, v = m.groups(1)
                    self.config[k] = v
            process.wait()
        except:
            raise

    @staticmethod
    def Enumerate():
        """
        Parse the output of ‘p4dctl list’ for a list of all Perforce servers
        """
        try:
            process = Popen(['p4dctl', 'list'],
                            stdout=PIPE, stderr=DEVNULL, text=True, close_fds=True)
            for line in iter(process.stdout.readline, ''):
                data = re.split(' +', line.strip())
                yield P4Server(data[0], data[2], data[3:])

            process.wait()
            if process.returncode != 0:
                raise RuntimeError
        except:
            raise

    def Journals(self):
        """
        List all server journals present on the filesystem, from newest to oldest
        """
        from glob import glob
        from os import path

        jprefix = self.config.get('journalPrefix')
        if jprefix:
            if jprefix[0] != '/':
                jprefix = path.join(self.config['root'], jprefix)
            jlist = [path.realpath(jnl) for jnl in glob(f'{jprefix}.jnl*')]
            # This sorting key ensures that jnl.900.gz < jnl.3000.gz < jnl.10000.gz
            yield from sorted(jlist, key=lambda x: [-int(s) if s.isnumeric() else 0 for s in x.split('.')])


@click.command()
@click.option('-s', '--server', type=str, default='all',
              help='Server to process')
@click.option('--skip-journals', type=int, default=1, help='Number of journals that are not compressed (default: 1)')
@click.option('--keep-journals', type=int, default=-1, help='Number of journals to keep (default: all)')
@click.option('-n', '--dry-run', is_flag=True, help='Perform a trial run with no changes made')
@verbosity_params
def p4_maintenance(server: str, skip_journals: -1, keep_journals: -1, dry_run: bool):

    from os import unlink
    from yolops.fsutils import gzip_file

    # Check argument consistency
    # TODO

    server_list = list(P4Server.Enumerate())
    if server != 'all':
        server_list = [x for x in server_list if x.name == server]
        if not server_list:
            raise click.UsageError(f'Server {server} not found by p4dctl')

    for s in server_list:
        info(f'Journal maintenance for {s.type} server "{s.name}"')
        skipped, kept, compressed, deleted = 0, 0, 0, 0
        for n, journal in enumerate(s.Journals()):
            if skip_journals < 0 or n < skip_journals:
                skipped += 1
                pass
            elif keep_journals < 0 or n < keep_journals:
                kept += 1
                if journal[-3:] != '.gz':
                    debug(f'Compressing journal: {journal}')
                    if not dry_run:
                        gzip_file(journal, f'{journal}.gz')
                    compressed += 1
            else:
                debug(f'Deleting journal: {journal}')
                if not dry_run:
                    unlink(journal)
                deleted += 1

        info(f'Compressed {compressed} journals ({skipped} left uncompressed), ' +
             f'deleted {deleted} journals ({skipped + kept} remaining on disk)')
