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
        parser.add_argument(
            '--test',
            action='store_true',
            help='Run collector without pushing results to ES, use verbosity to view data',
        )

    def print_collectors(self):
        for _, _, collector in collectors():
            self.stdout.write(f'{collector.name()} ({collector().get_index_name()})')

    def find_chosen(self, cols):
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
        return chosen

    def _set_es_logger_level(self):
        if self.verbosity == 2:
            logging.getLogger('elasticsearch').setLevel(logging.INFO)
        elif self.verbosity > 2:
            logging.getLogger('elasticsearch').setLevel(logging.DEBUG)

    def handle(self, *args, **options):
        cols = options['app_class']

        # do not allow running all collectors (unless explicitly enumerated)
        # some might not be supposed to run "wild"
        if not cols:
            return self.print_collectors()

        chosen = self.find_chosen(cols)

        self._set_es_logger_level()

        if options['no_progress']:
            self.log(f'Matched {len(chosen)} collectors')

        errors = []
        ind = 0

        for cname, cclass in chosen:
            self.log_debug(f'Running {cclass.name()}...')
            col = cclass()
            col.logger.setLevel(self.logger.getEffectiveLevel())
            estimated_count = None if options['no_progress'] else col.estimated_count()
            push = col.fake_push if options['test'] else col.push
            ind += 1

            with tqdm.tqdm(
                desc=f'{cclass.name()} {ind}/{len(chosen)}', disable=options['no_progress'], total=estimated_count
            ) as pbar:
                error_bar = ErrorBar(pbar)
                try:
                    stats = push(stats_cb=error_bar.update)
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


class ErrorBar:
    def __init__(self, pbar):
        self.err = 0
        self.pbar = pbar

    def update(self, ok, _):
        self.pbar.update(1)  # NOSONAR python:S1515
        if not ok:
            self.err += 1  # NOSONAR python:S1515
            self.pbar.set_postfix(err=self.err)
