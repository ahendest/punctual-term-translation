"""Term research runs as JSON files under data/runs; approved terms go into the shared SQLite store."""
import contextlib
import datetime
import fcntl
import hashlib
import importlib.util
import json
import os
import re
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / 'config/workflow.json').read_text())
PRODUCTION_ROOT = (ROOT / CONFIG['production_root']).resolve()
CHOICES = ('A', 'B', 'none')
HEADING = re.compile(r'^#{1,6}\s')
CANVAS_HEADER = """# Results

This file is the human-readable canvas of the terminology work in progress. The tool rewrites
one block per run: the source paragraph, the A/B alternatives with their footnotes, the
reviewer's choice. Give your approval in the conversation; after the translator writes it into
the shared SQLite store, the tool removes the block. Add your own notes outside the marked blocks.

## Results Under Here
"""


def knowledge_module():
    name = 'risalero_knowledge'
    if name not in sys.modules:
        spec = importlib.util.spec_from_file_location(name, PRODUCTION_ROOT / 'tools/knowledge.py')
        module = importlib.util.module_from_spec(spec)
        sys.modules[name] = module
        spec.loader.exec_module(module)
    return sys.modules[name]


def encode(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def sha(value):
    return hashlib.sha256(encode(value).encode()).hexdigest()


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')


def require(condition, message):
    if not condition:
        raise ValueError(message)


def fields(value, required, optional=()):
    require(isinstance(value, dict), 'Expected object')
    require(set(required) <= value.keys(), 'Missing fields: ' + str(sorted(set(required) - value.keys())))
    require(value.keys() <= set(required) | set(optional), 'Unexpected fields: ' + str(sorted(value.keys() - set(required) - set(optional))))


def text_or_null(value, name):
    require(value is None or (isinstance(value, str) and value.strip()), f'{name} must be text or null')


def validate(content):
    """Structural check of a resolve result; meaning and Arabic completeness need the final check."""
    fields(content, ['sense', 'route', 'reading_form', 'arabic', 'options'], ['note', 'later_use'])
    require(isinstance(content['sense'], str) and content['sense'].strip(), 'Empty sense')
    for key in ('reading_form', 'arabic', 'note'):
        text_or_null(content.get(key), key)
    require(content.get('later_use', 'equivalent') in ('equivalent', 'original'), 'later_use must be equivalent or original')
    # directed: the user dictated the treatment; it needs neither research alternatives nor review.
    require(content['route'] in ('attested', 'compare', 'directed'), 'Route must be attested, compare or directed')
    options = content['options']
    require(isinstance(options, list) and len(options) == (2 if content['route'] == 'compare' else 1), 'Invalid option count')
    for label, option in zip(('A', 'B'), options):
        fields(option, ['label', 'translation', 'footnote', 'paragraph'])
        require(option['label'] == label, 'Options must be ordered A then B')
        # A missing reading form, translation or footnote is a decision, not an error.
        for key in ('translation', 'footnote', 'paragraph'):
            text_or_null(option[key], key)
        require(content['reading_form'] or option['translation'] or content.get('note'), 'A term needs a reading form, a translation or a note')
        require(not option['footnote'] or content['reading_form'], 'A footnote is called after the retained term; it needs a reading form')
        require(option['paragraph'] or content['route'] == 'directed', 'Each option needs its paragraph')
        require(not (option['paragraph'] and option['translation']) or option['translation'] in option['paragraph'],
                'Each paragraph must contain its translation')
        require(option['footnote'] is None or content['arabic'] is None or content['arabic'] in option['footnote'],
                'The footnote must contain the complete Arabic expression')
    if len(options) == 2:
        a, b = options
        require(a['translation'] and b['translation'] and a['translation'] != b['translation'], 'Comparison needs two distinct translations')
        require(a['paragraph'].replace(a['translation'], '{{TERM}}') == b['paragraph'].replace(b['translation'], '{{TERM}}'),
                'Comparison paragraphs may differ only in the proposed translation')


def section_text(text, line):
    """The heading section around a one-based line: from the heading above it to the next heading."""
    lines = text.splitlines()
    start = next((i for i in range(line - 1, -1, -1) if HEADING.match(lines[i])), 0)
    end = next((i for i in range(line, len(lines)) if HEADING.match(lines[i])), len(lines))
    return '\n'.join(lines[start:end]).strip()


def locate(root, location):
    """Read the paragraph around segment.md:line."""
    filename, separator, number = location.rpartition(':')
    require(separator and number.isdecimal(), 'Use a source-segment.md:line location')
    path = (root / filename).resolve()
    require(path.is_relative_to(root) and path.is_file(), 'Segment must be a file inside the source repository')
    lines = path.read_text(encoding='utf-8').splitlines()
    line = int(number)
    require(1 <= line <= len(lines) and lines[line - 1].strip(), 'Location must point to a nonempty source line')
    start, end = line - 1, line
    while start > 0 and lines[start - 1].strip() and not HEADING.match(lines[start - 1]):
        start -= 1
    while end < len(lines) and lines[end].strip() and not HEADING.match(lines[end]):
        end += 1
    return {'path': str(path.relative_to(root)), 'line': line, 'paragraph': '\n'.join(lines[start:end])}


def project_for(root, source_path):
    source = (root / source_path).resolve()
    matches = []
    for path in (root / 'translations').glob('*/*/project.json'):
        manifest = json.loads(path.read_text())
        prepared = (root / manifest.get('prepared_source', '__missing__')).resolve()
        if source == prepared or source.is_relative_to(prepared):
            matches.append(path)
    require(len(matches) == 1, 'Source project is ambiguous or unknown; supply --project using the active manifest')
    return str(matches[0].relative_to(root))


def quote(text):
    return '\n'.join('> ' + line if line.strip() else '>' for line in text.strip().splitlines())


class Store:
    def __init__(self, data_root=None, canvas=None, knowledge_config=None):
        # Run files stay outside Git (data/); the human canvas is results/results.md.
        self.data = Path(data_root or ROOT / 'data').resolve()
        self.runs = self.data / 'runs'
        self.canvas = Path(canvas or ROOT / 'results/results.md')
        self.knowledge_config = knowledge_config or PRODUCTION_ROOT / CONFIG['production_config']

    def knowledge(self):
        return knowledge_module().Knowledge(self.knowledge_config)

    @contextlib.contextmanager
    def lock(self):
        """Serialize run files and the shared canvas between parallel agents."""
        self.data.mkdir(parents=True, exist_ok=True)
        with open(self.data / '.lock', 'w') as handle:
            fcntl.flock(handle, fcntl.LOCK_EX)
            yield

    def path(self, run_id):
        require(re.fullmatch(r'[\w-]+', run_id or ''), 'Invalid run ID')
        return self.runs / f'{run_id}.json'

    def load(self, run_id):
        path = self.path(run_id)
        require(path.is_file(), f'Unknown run: {run_id}')
        return json.loads(path.read_text(encoding='utf-8'))

    def _save(self, run):
        self.runs.mkdir(parents=True, exist_ok=True)
        path = self.path(run['id'])
        temporary = path.with_name(path.name + '.tmp')
        temporary.write_text(json.dumps(run, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        os.replace(temporary, path)

    def open_runs(self):
        runs = [json.loads(p.read_text(encoding='utf-8')) for p in sorted(self.runs.glob('*.json'))] if self.runs.is_dir() else []
        return [{'run_id': r['id'], 'term': r['source']['term'], 'term_id': r['term_id'], 'status': self.status(r)} for r in runs]

    def approved(self, ident):
        return self.knowledge().term_get(ident)

    def ask(self, term, location, project=None, term_id=None, reconsider=False, new=False):
        k = knowledge_module()
        folded = ' '.join(k.key(term).split())
        require(term.strip(), 'Term must not be empty')
        source = locate(PRODUCTION_ROOT, location)
        project = project or project_for(PRODUCTION_ROOT, source['path'])
        manifest_path = (PRODUCTION_ROOT / project).resolve()
        require(manifest_path.is_relative_to(PRODUCTION_ROOT) and manifest_path.is_file(), 'Project manifest must exist inside the production repository')
        manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
        language = manifest['target_language']
        prepared = (PRODUCTION_ROOT / manifest['prepared_source']).resolve()
        located = (PRODUCTION_ROOT / source['path']).resolve()
        require(located == prepared or located.is_relative_to(prepared), 'Source does not belong to the routed project')
        require(re.search(k.stem_pattern(term), k.fold(source['paragraph'])), 'Term is absent from the located paragraph')
        # An ASCII slug keeps existing IDs; a term without Latin letters or digits gets a hash of its folded form.
        slug = re.sub('[^a-z0-9]+', '-', k.key(term)).strip('-')
        ident = term_id or slug or 'u' + hashlib.sha256(folded.encode()).hexdigest()[:10]
        same = lambda form: term_id or ' '.join(k.key(form).split()) == folded
        try:
            existing = self.knowledge().term_get(ident)
        except k.KnowledgeError as error:
            if error.code != 'not_found':
                raise
            existing = None
        require(not existing or existing['language'] == language, 'The selected term belongs to another language')
        require(not existing or same(existing['source_form']),
                f"{ident} holds the approved term {existing and existing['source_form']!r}; pass an explicit --term-id for this term")
        if not reconsider:
            if existing:
                return {'state': 'approved', 'records': [existing]}
            found = [] if term_id else self.knowledge().find(term, language)
            exact = [r for r in found if r['match_type'] == 'exact']
            if exact:
                return {'state': 'approved', 'records': exact}
            if found and not new:
                # A prefix match is not proof of the same concept: decide by the paragraph.
                return {'state': 'candidates', 'records': found, 'paragraph': source['paragraph'],
                        'decision': 'Same concept: ask again with --term-id ID. Different concept: ask again with --new.'}
        with self.lock():
            for current in self.open_runs():
                if current['term_id'] == ident:
                    require(same(current['term']), f"{ident} is open for {current['term']!r}; pass an explicit --term-id for this term")
                    return dict(current, state='open', paragraph=self.load(current['run_id'])['source']['paragraph'])
            run = {'id': 'run-' + uuid.uuid4().hex[:12], 'created': now(), 'project': project, 'language': language,
                   'term_id': ident, 'reconsider': bool(existing),
                   'source': dict(source, term=term), 'resolve': None, 'review': None}
            self._save(run)
            self._canvas_write(run['id'], self.canvas_block(run))
        return {'state': 'created', 'run_id': run['id'], 'term_id': ident, 'source': {k2: v for k2, v in source.items() if k2 != 'paragraph'},
                'paragraph': source['paragraph'], 'canvas': str(self.canvas)}

    def context(self, run_id, nearby=False):
        run = self.load(run_id)
        result = {'source': {k: v for k, v in run['source'].items() if k != 'paragraph'}, 'paragraph': run['source']['paragraph']}
        if nearby:
            text = (PRODUCTION_ROOT / run['source']['path']).read_text(encoding='utf-8')
            result['nearby'] = section_text(text, run['source']['line'])
            if result['nearby'] == result['paragraph']:
                result['limitation'] = 'The section holds only this paragraph; open the adjacent unit only if needed'
        return result

    def submit(self, run_id, content):
        validate(content)
        with self.lock():
            run = self.load(run_id)
            run['resolve'] = dict(content, saved=now())
            run['review'] = None
            self._save(run)
            self._canvas_write(run_id, self.canvas_block(run))
        return {'run_id': run_id, 'status': self.status(run), 'canvas': str(self.canvas)}

    def review_packet(self, run_id):
        run = self.load(run_id)
        require(run['resolve'] and run['resolve']['route'] == 'compare', 'Review needs a saved A/B comparison')
        options = run['resolve']['options']
        return {'run_id': run_id, 'term': run['source']['term'], 'digest': self.packet_digest(run),
                'source': {k: run['source'][k] for k in ('path', 'line', 'paragraph')},
                'paragraphs': {o['label']: o['paragraph'] for o in options},
                'footnotes': {o['label']: o['footnote'] for o in options}}

    @staticmethod
    def packet_digest(run):
        """Version of the reviewed content; a verdict applies only to this version."""
        return sha({'term': run['source']['term'], 'options': run['resolve']['options']})

    def review(self, run_id, choice, digest):
        require(choice in CHOICES, 'Review must be A, B or none; no rationale')
        with self.lock():
            run = self.load(run_id)
            require(run['resolve'] and run['resolve']['route'] == 'compare', 'Review needs a saved A/B comparison')
            require(digest == self.packet_digest(run), 'The proposal changed after this packet; get a new review packet and compare again')
            run['review'] = {'choice': choice, 'digest': digest, 'saved': now()}
            self._save(run)
            self._canvas_write(run_id, self.canvas_block(run))
        return {'run_id': run_id, 'choice': choice, 'status': self.status(run)}

    @staticmethod
    def status(run):
        if not run['resolve']:
            return 'research'
        if run['resolve']['route'] == 'compare' and not run['review']:
            return 'awaiting_review'
        if run['review'] and run['review']['choice'] == 'none':
            return 'rejected'
        return 'ready_for_approval'

    def proposal(self, run, choice=None):
        content = run['resolve']
        if choice:
            # The user's choice is final and needs no review.
            require(content and choice in [o['label'] for o in content['options']], f'No option {choice} to approve')
        else:
            require(self.status(run) == 'ready_for_approval', 'No publishable proposal: ' + self.status(run))
            choice = run['review']['choice'] if content['route'] == 'compare' else 'A'
        option = next(o for o in content['options'] if o['label'] == choice)
        return {'id': run['term_id'], 'language': run['language'], 'source_form': run['source']['term'],
                'reading_form': content['reading_form'], 'translation': option['translation'], 'arabic': content['arabic'],
                'footnote': option['footnote'], 'later_use': content.get('later_use', 'equivalent'),
                'sense': content['sense'], 'note': content.get('note')}

    def approval_digests(self, run):
        """Digests the translator passes to approve: the reviewer's or the single option, then each label."""
        content = run['resolve']
        if not content:
            return {}
        result = {o['label']: sha(self.proposal(run, o['label'])) for o in content['options']}
        if self.status(run) == 'ready_for_approval':
            result['default'] = sha(self.proposal(run))
        return result

    def approve(self, run_id, digest, user_text, dry_run=False, choice=None):
        require(user_text.strip(), 'Exact user approval text is required')
        k = knowledge_module()
        with self.lock():
            run = self.load(run_id)
            proposal = self.proposal(run, choice)
            require(sha(proposal) == digest, 'The proposal changed; read results.md again before approving')
            store = self.knowledge()
            with store.write(dry_run) as connection:
                old = store._record(connection, proposal['id'])
                if old and not run['reconsider']:
                    k.fail('already_approved', f"{proposal['id']} was approved while this run was open")
                record = dict(proposal, approval=user_text.strip(), approved_at=datetime.date.today().isoformat())
                store.put_term(connection, record)
            if not dry_run:
                self.path(run_id).unlink()
                self._canvas_write(run_id, None)
        return {'term_id': record['id'], 'dry_run': dry_run, 'record': record}

    def discard(self, run_id):
        with self.lock():
            path = self.path(run_id)
            require(path.is_file(), f'Unknown run: {run_id}')
            path.unlink()
            self._canvas_write(run_id, None)
        return {'discarded_run': run_id, 'canvas': str(self.canvas)}

    def canvas_block(self, run):
        source = run['source']
        lines = [f"## {source['term']} — {source['path']}:{source['line']}", '',
                 f"Run `{run['id']}` · term `{run['term_id']}` · language `{run['language']}`" +
                 (' · reconsideration of an approved term' if run['reconsider'] else ''), '',
                 '**Source paragraph**', '', quote(source['paragraph']), '']
        content = run['resolve']
        if not content:
            return '\n'.join(lines + ['**Status:** research in progress; no proposal recorded yet.'])
        later = 'the term alone' if content.get('later_use') == 'original' else 'the term followed by its equivalent'
        lines += [f"**Meaning:** {content['sense']}", '',
                  f"**Reading form:** {content['reading_form'] or '(none: write the equivalent only)'} · "
                  f"**Arabic:** {content['arabic'] or '(none)'} · **Route:** {content['route']} · **Later uses:** {later}", '']
        if content.get('note'):
            lines += [f"**Note for translators:** {content['note']}", '']
        first = content['options'][0]
        for option in content['options']:
            label = option['label']
            lines += [f"**{label} — translation:** {option['translation'] or '(none: the original stays alone)'}", '']
            if option['paragraph']:
                lines += [quote(option['paragraph']), '']
            # B repeats nothing that A already shows.
            if option is first or option['footnote'] != first['footnote']:
                lines += [f"**Footnote {label}:** {option['footnote'] or '(none)'}", '']
        status = self.status(run)
        if content['route'] == 'compare':
            if run['review']:
                choice = run['review']['choice']
                verdict = f'`{choice}`' if choice in ('A', 'B') else '`none` — both alternatives rejected; this term needs a new proposal'
                lines += [f'**Reviewer:** {verdict}', '']
            else:
                lines += ['**Reviewer:** awaiting independent comparison.', '']
        if status in ('ready_for_approval', 'rejected') or content['route'] == 'compare':
            lines += ['**Approval:** tell the translator in the conversation which option you approve, '
                      'or write your own wording there.', '']
        return '\n'.join(lines).rstrip('\n')

    def canvas_current(self, run_id):
        """The run's block as it stands in results.md, or None."""
        text = self.canvas.read_text(encoding='utf-8') if self.canvas.is_file() else ''
        match = re.search(re.escape(f'<!-- run:{run_id} -->') + r'\n(.*?)\n' + re.escape(f'<!-- /run:{run_id} -->'), text, re.S)
        return match[1] if match else None

    def canvas_refresh(self, run_id):
        with self.lock():
            return self._canvas_write(run_id, self.canvas_block(self.load(run_id)))

    def _canvas_write(self, run_id, block):
        """Replace or remove this run's block; text outside the markers is kept. Call under lock()."""
        text = self.canvas.read_text(encoding='utf-8') if self.canvas.is_file() else CANVAS_HEADER
        start, end = f'<!-- run:{run_id} -->', f'<!-- /run:{run_id} -->'
        text = re.sub(r'\n*' + re.escape(start) + r'.*?' + re.escape(end) + r'\n*', '\n', text, flags=re.S)
        if block:
            text = text.rstrip('\n') + f'\n\n{start}\n{block}\n{end}\n'
        self.canvas.parent.mkdir(parents=True, exist_ok=True)
        self.canvas.write_text(text.rstrip('\n') + '\n', encoding='utf-8')
        return str(self.canvas)
