import copy
import io
import json
import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import terms
from store import PRODUCTION_ROOT, Store, sha


class TermTests(unittest.TestCase):
    """Disposable sources, projects, runs and stores; the live store and canvas are never touched."""

    def setUp(self):
        temp = tempfile.TemporaryDirectory(dir=PRODUCTION_ROOT / 'knowledge', prefix='.test-terms-')
        self.addCleanup(temp.cleanup)
        self.folder = Path(temp.name)
        self.source = self.folder / 'source.md'
        self.source.write_text('## text/one.xhtml\nNamaz ve fixture bir arada.\nİkinci satır.\n\nBaşka paragraf.\n', encoding='utf-8')
        (PRODUCTION_ROOT / 'translations/ro').mkdir(parents=True, exist_ok=True)
        project = tempfile.TemporaryDirectory(dir=PRODUCTION_ROOT / 'translations/ro', prefix='.test-terms-')
        self.addCleanup(project.cleanup)
        self.manifest = Path(project.name) / 'project.json'
        self.manifest.write_text(json.dumps({'id': 'ro-test', 'target_language': 'ro',
                                             'prepared_source': str(self.folder.relative_to(PRODUCTION_ROOT))}))
        self.store = Store(self.folder / 'data', self.folder / 'results.md',
                           {'engine': 'sqlite', 'path': str(self.folder / 'store.sqlite')})
        self.store.knowledge().init()
        self.at = str(self.source.relative_to(PRODUCTION_ROOT)) + ':2'

    def ask(self, term='fixture', **options):
        return self.store.ask(term, self.at, **options)

    def content(self, **changes):
        value = {'sense': 'Test anlamı', 'route': 'compare', 'reading_form': 'fixture',
                 'arabic': 'نَفْس', 'note': None,
                 'options': [{'label': 'A', 'translation': 'sens', 'footnote': 'Fixture (arab. نَفْس): nota A.', 'paragraph': 'Acest sens apare.'},
                             {'label': 'B', 'translation': 'înțeles', 'footnote': 'Fixture (arab. نَفْس): nota B.', 'paragraph': 'Acest înțeles apare.'}]}
        value.update(changes)
        return value

    def ready(self, choice='A', **changes):
        run = self.ask()['run_id']
        self.store.submit(run, self.content(**changes))
        self.store.review(run, choice, self.packet(run))
        return run

    def packet(self, run):
        return self.store.review_packet(run)['digest']

    def digest(self, run):
        return sha(self.store.proposal(self.store.load(run)))

    def cli(self, *args):
        output = io.StringIO()
        with patch.object(terms, 'Store', lambda: self.store), redirect_stdout(output):
            code = terms.main(list(args))
        return code, json.loads(output.getvalue())

    def test_ask_extracts_paragraph_and_resumes_instead_of_duplicating(self):
        created = self.ask()
        self.assertEqual(created['state'], 'created')
        self.assertEqual(created['paragraph'], 'Namaz ve fixture bir arada.\nİkinci satır.')
        self.assertNotIn('page', created['source'])
        self.assertEqual(created['term_id'], 'term-ro-fixture')
        self.assertIn(f"<!-- run:{created['run_id']} -->", self.store.canvas.read_text())
        again = self.ask()
        self.assertEqual((again['state'], again['run_id']), ('open', created['run_id']))
        self.assertEqual(len(self.store.open_runs()), 1)

    def test_prefix_match_is_a_candidate_until_the_context_decides(self):
        run = self.ready()
        self.store.approve(run, self.digest(run), 'Approved.')
        self.source.write_text('## text/one.xhtml\nFixtureları gördü.\n', encoding='utf-8')
        result = self.store.ask('Fixtureları', self.at)
        self.assertEqual((result['state'], [r['id'] for r in result['records']]), ('candidates', ['term-ro-fixture']))
        self.assertEqual(self.store.open_runs(), [])
        reused = self.store.ask('Fixtureları', self.at, term_id='term-ro-fixture')
        self.assertEqual((reused['state'], reused['records'][0]['id']), ('approved', 'term-ro-fixture'))
        self.assertEqual(self.store.open_runs(), [])
        self.assertEqual(self.store.ask('Fixtureları', self.at, new=True)['term_id'], 'term-ro-fixturelari')

    def test_unrelated_prefix_word_is_not_approved(self):
        self.source.write_text('## text/one.xhtml\nHak ve hakikat.\n', encoding='utf-8')
        run = self.store.ask('hak', self.at)['run_id']
        self.store.submit(run, self.content())
        self.store.review(run, 'A', self.packet(run))
        self.store.approve(run, self.digest(run), 'Approved.')
        self.assertEqual(self.store.ask('hak', self.at)['state'], 'approved')
        result = self.store.ask('hakikat', self.at)
        self.assertEqual((result['state'], [r['source_form'] for r in result['records']]), ('candidates', ['hak']))
        code, output = self.cli('ask', '--term', 'hakikat', '--at', self.at, '--new')
        self.assertEqual((code, output['result']['state'], output['result']['term_id']), (0, 'created', 'term-ro-hakikat'))

    def test_non_latin_terms_get_distinct_stable_ids_and_no_foreign_reuse(self):
        self.source.write_text('## text/one.xhtml\nالصلاة ثم الزكاة\n', encoding='utf-8')
        first, second = self.store.ask('الصلاة', self.at), self.store.ask('الزكاة', self.at)
        self.assertEqual((first['state'], second['state']), ('created', 'created'))
        self.assertNotEqual(first['term_id'], second['term_id'])
        self.assertRegex(first['term_id'], r'^term-ro-u[0-9a-f]{10}$')
        self.assertEqual(self.store.ask('الصلاة', self.at)['run_id'], first['run_id'])
        self.store.submit(first['run_id'], self.content())
        self.store.review(first['run_id'], 'A', self.packet(first['run_id']))
        self.store.approve(first['run_id'], self.digest(first['run_id']), 'Approved.')
        self.assertEqual(self.store.ask('الزكاة', self.at)['state'], 'open')
        self.assertEqual(self.store.ask('الصلاة', self.at)['records'][0]['source_form'], 'الصلاة')

    def test_colliding_slug_never_reuses_another_source_form(self):
        self.source.write_text('## text/one.xhtml\nnefs-i emmare ve nefs i emmare\n', encoding='utf-8')
        run = self.store.ask('nefs-i emmare', self.at)['run_id']
        with self.assertRaisesRegex(ValueError, 'explicit --term-id'):
            self.store.ask('nefs i emmare', self.at)
        self.store.submit(run, self.content())
        self.store.review(run, 'A', self.packet(run))
        self.store.approve(run, self.digest(run), 'Approved.')
        with self.assertRaisesRegex(ValueError, 'explicit --term-id'):
            self.store.ask('nefs i emmare', self.at)
        self.assertEqual(self.store.ask('nefs i emmare', self.at, term_id='term-ro-nefs-i-emmare-2')['state'], 'created')

    def test_inflected_occurrence_counts_as_the_term(self):
        self.source.write_text('## text/one.xhtml\nFixtureları gördü.\n', encoding='utf-8')
        self.assertEqual(self.ask()['state'], 'created')

    def test_bad_locations_and_absent_terms_are_rejected(self):
        for term, at in [('fixture', 'missing.md:1'), ('fixture', self.at[:-1] + '99'), ('absent', self.at), ('', self.at)]:
            with self.assertRaises(ValueError):
                self.store.ask(term, at)
        self.assertEqual(self.store.open_runs(), [])

    def test_structural_validation_rejects_weak_comparisons_without_saving(self):
        run = self.ask()['run_id']
        before = self.store.path(run).read_bytes()
        bad = [self.content(route='single'),
               self.content(options=self.content()['options'][:1]),
               self.content(extra='field'),
               self.content(arabic='رُوح'),
               self.content(queries=['research is not recorded'])]
        same = copy.deepcopy(self.content()); same['options'][1]['translation'] = 'sens'; same['options'][1]['paragraph'] = 'Acest sens apare.'
        other = copy.deepcopy(self.content()); other['options'][1]['paragraph'] = 'Alt context înțeles.'
        for content in bad + [same, other]:
            with self.assertRaises(ValueError):
                self.store.submit(run, content)
        self.assertEqual(self.store.path(run).read_bytes(), before)

    def test_attested_usage_needs_no_review(self):
        run = self.ask()['run_id']
        self.store.submit(run, self.content(route='attested', options=self.content()['options'][:1]))
        self.assertEqual(self.store.status(self.store.load(run)), 'ready_for_approval')
        with self.assertRaises(ValueError):
            self.store.review(run, 'A', 'x')

    def test_review_packet_is_blind_and_none_blocks_approval(self):
        run = self.ask()['run_id']
        self.store.submit(run, self.content())
        packet = self.store.review_packet(run)
        self.assertEqual(set(packet), {'run_id', 'term', 'digest', 'source', 'paragraphs', 'footnotes'})
        self.assertNotIn('Test anlamı', json.dumps(packet, ensure_ascii=False))
        with self.assertRaises(ValueError):
            self.store.review(run, 'tie', packet['digest'])
        self.store.review(run, 'none', packet['digest'])
        self.assertIn('both alternatives rejected', self.store.canvas.read_text())
        with self.assertRaises(ValueError):
            self.store.proposal(self.store.load(run))

    def test_verdict_on_an_older_packet_is_rejected(self):
        run = self.ask()['run_id']
        self.store.submit(run, self.content())
        old = self.packet(run)
        changed = copy.deepcopy(self.content())
        changed['options'][0].update(translation='sensul', paragraph='Acest sensul apare.')
        changed['options'][1]['paragraph'] = 'Acest înțeles apare.'
        self.store.submit(run, changed)
        with self.assertRaisesRegex(ValueError, 'new review packet'):
            self.store.review(run, 'A', old)
        self.assertEqual(self.store.status(self.store.load(run)), 'awaiting_review')
        code, result = self.cli('review', '--run', run, '--choice', 'A', '--digest', self.packet(run))
        self.assertEqual((code, result['result']['status']), (0, 'ready_for_approval'))

    def test_new_submit_clears_previous_review(self):
        run = self.ready()
        self.store.submit(run, self.content(sense='Corrected meaning'))
        self.assertEqual(self.store.status(self.store.load(run)), 'awaiting_review')

    def test_approval_writes_the_exact_choice_and_closes_the_run(self):
        run = self.ready('B')
        digest = self.digest(run)
        with self.assertRaises(ValueError):
            self.store.approve(run, 'wrong-digest', 'Approved.')
        with self.assertRaises(ValueError):
            self.store.approve(run, digest, '  ')
        dry = self.store.approve(run, digest, 'Approved B exactly.', dry_run=True)
        self.assertTrue(dry['dry_run'])
        self.assertEqual(self.store.knowledge().terms_list('ro'), [])
        self.store.approve(run, digest, 'Approved B exactly.')
        record = self.store.approved('term-ro-fixture')
        self.assertEqual((record['translation'], record['footnote'], record['arabic'], record['approval']),
                         ('înțeles', 'Fixture (arab. نَفْس): nota B.', 'نَفْس', 'Approved B exactly.'))
        self.assertEqual((record['source_form'], record['reading_form']), ('fixture', 'fixture'))
        self.assertFalse(self.store.path(run).exists())
        self.assertNotIn(run, self.store.canvas.read_text())
        self.assertEqual(self.ask()['state'], 'approved')

    def test_cli_approval_requires_the_visible_block_to_match(self):
        run = self.ready()
        approval = self.folder / 'approval.txt'
        approval.write_text('Approved A exactly.', encoding='utf-8')
        self.store.canvas.write_text(self.store.canvas.read_text().replace('sens', 'sensul'))
        code, result = self.cli('approve', '--run', run, '--digest', self.digest(run), '--user-text-file', str(approval))
        self.assertEqual(code, 2)
        self.assertIn('results.md differs', result['error'])
        self.assertEqual(self.cli('canvas', '--run', run)[0], 0)
        code, result = self.cli('approve', '--run', run, '--digest', self.digest(run), '--user-text-file', str(approval))
        self.assertEqual(code, 0, result)
        self.assertEqual(self.cli('approved', '--id', 'term-ro-fixture')[1]['result']['translation'], 'sens')

    def test_approved_term_reopens_only_by_reconsideration(self):
        first = self.ready()
        self.store.approve(first, self.digest(first), 'Approved.')
        self.assertEqual(self.ask()['state'], 'approved')
        second = self.ask(reconsider=True)
        self.assertTrue(self.store.load(second['run_id'])['reconsider'])
        self.assertIn('reconsideration', self.store.canvas.read_text())

    def test_reconsideration_replaces_the_wording(self):
        run = self.ready()
        self.store.approve(run, self.digest(run), 'Approved.')
        run = self.ask(reconsider=True)['run_id']
        self.store.submit(run, self.content(sense='Refined'))
        self.store.review(run, 'A', self.packet(run))
        self.store.approve(run, self.digest(run), 'Approved refinement.')
        record = self.store.approved('term-ro-fixture')
        self.assertEqual((record['sense'], record['approval']), ('Refined', 'Approved refinement.'))

    def test_epub_unit_paragraph_and_nearby_section(self):
        self.source.write_text('## OEBPS/text/content0005.xhtml\n\n### Birinci Makam\n\nÖnce.\n\nNamaz ve fixture.[^1]\n\n'
                               '### İkinci Makam\n\nSonra.\n\n[^1]: (Haşiye): Not.\n', encoding='utf-8')
        created = self.store.ask('fixture', self.at[:-1] + '7')
        self.assertEqual(created['paragraph'], 'Namaz ve fixture.[^1]')
        nearby = self.store.context(created['run_id'], nearby=True)
        self.assertEqual(nearby['nearby'], '### Birinci Makam\n\nÖnce.\n\nNamaz ve fixture.[^1]')
        self.assertNotIn('limitation', nearby)

    def test_other_language_term_id_is_rejected(self):
        store = self.store.knowledge()
        with store.write() as c:
            store.put_term(c, {'id': 'term-fr-fixture', 'language': 'fr', 'source_form': 'fixture', 'reading_form': 'fixture', 'translation': 'sens',
                               'footnote': 'Note.', 'sense': 'Test', 'approval': 'TEST', 'approved_at': '2026-10-24'})
        with self.assertRaisesRegex(ValueError, 'another language'):
            self.ask(term_id='term-fr-fixture')

    def test_parallel_runs_keep_every_canvas_block(self):
        self.source.write_text('## text/one.xhtml\n' + ' '.join(f'term{n}' for n in range(8)) + '\n', encoding='utf-8')
        runs = [self.store.ask(f'term{n}', self.at[:-1] + '2')['run_id'] for n in range(8)]
        with ThreadPoolExecutor(8) as pool:
            list(pool.map(lambda run: self.store.canvas_refresh(run), runs))
        text = self.store.canvas.read_text()
        self.assertTrue(all(f'<!-- run:{run} -->' in text for run in runs))

    def test_discard_removes_run_and_block(self):
        run = self.ask()['run_id']
        self.store.discard(run)
        self.assertEqual(self.store.open_runs(), [])
        self.assertNotIn(run, self.store.canvas.read_text())


if __name__ == '__main__':
    unittest.main()
