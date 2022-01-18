import re
import logging
import tqdm
from logbasecommand.base import LogBaseCommand, CommandError

from olympus.base import collectors


class Command(LogBaseCommand):
    help = 'Push data to Olympus (ElasticSearch).'

    def add_arguments(self, parser):
        parser.add_argument('app_class', type=str, nargs='*', help='App or specific class to process')
        parser.add_argument('--no-progress', action='store_true', help='Disable progress-bar')

    def handle(self, *args, **options):
        cols = options['app_class']

        # do not allow running all collectors (unless explicitly enumerated)
        # some might not be supposed to run "wild"
        if not cols:
            for _, _, collector in collectors():
                self.stdout.write(f'{collector.name()} ({collector().get_index_name()})')
            return

        matches = []
        for c in cols:
            if 0 <= c.find('*') < len(c) - 1:
                raise CommandError('wildcard only supported at the end', c)
            if c[-1] == '*':
                matches.append(re.compile(re.escape(c[:-1]) + r'.*'))
            elif '.' not in c:
                matches.append(re.compile(re.escape(c) + r'\..*'))
            else:
                matches.append(re.compile(re.escape(c) + r'$'))

        chosen = []
        for _, cname, cclass in collectors():
            for _m in matches:
                if _m.match(cname):
                    chosen.append((cname, cclass))

        if not chosen:
            raise CommandError('no valid collectors specified')

        if options['no_progress']:
            self.log(f'Matched {len(chosen)} collectors')

        if self.verbosity == 2:
            logging.getLogger('elasticsearch').setLevel(logging.INFO)
        elif self.verbosity > 2:
            logging.getLogger('elasticsearch').setLevel(logging.DEBUG)

        errors = []
        ind = 0

        for cname, cclass in chosen:
            self.log_debug(f'Running {cclass.name()}...')
            col = cclass()
            col.logger.setLevel(self.logger.getEffectiveLevel())
            estimated_count = None if options['no_progress'] else col.estimated_count()
            ind += 1

            with tqdm.tqdm(
                desc=f'{cclass.name()} {ind}/{len(chosen)}', disable=options['no_progress'], total=estimated_count
            ) as pbar:

                def update_pbar(ok, _):
                    pbar.update(1)  # NOSONAR python:S1515
                    if not ok:
                        update_pbar.err += 1  # NOSONAR python:S1515
                        pbar.set_postfix(err=update_pbar.err)

                update_pbar.err = 0

                try:
                    stats = col.push(stats_cb=update_pbar)
                    if options['no_progress']:
                        self.log(f'{cname} pushed {stats[0]} records')
                    if stats[1]:
                        errors.append(cname)
                        self.log_error('%s failed: %s', cname, stats[1])
                except Exception:
                    errors.append(cname)
                    self.log_exception('%s failed', cname)

        if errors:
            raise CommandError('These collectors failed', errors)
