import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
import requests as term_requests
from store import Store


class RequestTests(unittest.TestCase):
    """Disposable request, job and run files; the real results and data folders are never touched."""

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        root = Path(self.directory.name)
        self.requests = root / 'requested-terms.md'
        self.job = root / 'current-job.md'
        self.store = Store(data_root=root / 'data')

    def tearDown(self):
        self.directory.cleanup()

    def next_job(self, finished):
        return term_requests.next_job(finished, self.requests, self.job, self.store)

    def test_moves_requests_into_job_and_clears_requests(self):
        self.requests.write_text('zekat (a.md:3)\n\nDeccal (b.md:9)\n', encoding='utf-8')
        self.assertEqual(self.next_job(False), ('new', ['zekat (a.md:3)', 'Deccal (b.md:9)']))
        self.assertEqual(self.job.read_text(encoding='utf-8'), 'zekat (a.md:3)\n\nDeccal (b.md:9)\n')
        self.assertEqual(self.requests.read_text(encoding='utf-8'), '')

    def test_unfinished_job_resumes_without_taking_requests(self):
        self.job.write_text('zekat (a.md:3)\n', encoding='utf-8')
        self.requests.write_text('Deccal (b.md:9)\n', encoding='utf-8')
        self.assertEqual(self.next_job(False), ('resume', ['zekat (a.md:3)']))
        self.assertEqual(self.requests.read_text(encoding='utf-8'), 'Deccal (b.md:9)\n')

    def test_finished_job_is_replaced(self):
        self.job.write_text('zekat (a.md:3)\n', encoding='utf-8')
        self.requests.write_text('Deccal (b.md:9)\n', encoding='utf-8')
        self.assertEqual(self.next_job(True), ('new', ['Deccal (b.md:9)']))
        self.assertEqual(self.job.read_text(encoding='utf-8'), 'Deccal (b.md:9)\n')

    def test_no_new_requests_empties_finished_job(self):
        self.job.write_text('zekat (a.md:3)\n', encoding='utf-8')
        self.assertEqual(self.next_job(True), ('new', []))
        self.assertEqual(self.job.read_text(encoding='utf-8'), '')

    def test_open_run_keeps_the_job(self):
        self.job.write_text('zekat (a.md:3)\n', encoding='utf-8')
        self.requests.write_text('Deccal (b.md:9)\n', encoding='utf-8')
        self.store.runs.mkdir(parents=True)
        run = {'id': 'run-1', 'term_id': 'zekat', 'source': {'term': 'zekat'}, 'resolve': None, 'review': None}
        (self.store.runs / 'run-1.json').write_text(json.dumps(run), encoding='utf-8')
        with self.assertRaises(ValueError):
            self.next_job(True)
        self.assertEqual(self.job.read_text(encoding='utf-8'), 'zekat (a.md:3)\n')
        self.assertEqual(self.requests.read_text(encoding='utf-8'), 'Deccal (b.md:9)\n')


if __name__ == '__main__':
    unittest.main()
