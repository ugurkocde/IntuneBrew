"""Exercise the real HTTP adapter against temporary upstream outages."""
import importlib.util
import pathlib
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

SPEC = importlib.util.spec_from_file_location('collector_retries', pathlib.Path(__file__).parents[1] / '.github/scripts/collect_app_info.py')
COLLECTOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(COLLECTOR)


class CaskRetryTests(unittest.TestCase):
    def fetch(self, statuses):
        calls = []

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                status = statuses[min(len(calls), len(statuses) - 1)]
                calls.append(status)
                self.send_response(status)
                self.send_header('Content-Type', 'application/json')
                # An upstream outage must not stall a worker for an hour.
                self.send_header('Retry-After', '3600')
                self.end_headers()
                self.wfile.write(b'{"version":"2"}')

            def log_message(self, *args):
                pass

        server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        try:
            with COLLECTOR.build_cask_session() as session:
                result = session.get(f'http://127.0.0.1:{server.server_port}/cask.json')
            return result, calls
        finally:
            server.shutdown()
            server.server_close()
            worker.join()

    def test_transient_server_failure_and_rate_limit_recover(self):
        for status in (429, 500, 502, 503, 504):
            with self.subTest(status=status):
                result, calls = self.fetch([status, 200])
                self.assertEqual(result.json()['version'], '2')
                self.assertEqual(result.status_code, 200)
                self.assertEqual(calls, [status, 200])

    def test_persistent_outage_stops_after_three_attempts(self):
        result, calls = self.fetch([503])
        self.assertEqual(calls, [503, 503, 503])
        with self.assertRaises(COLLECTOR.requests.HTTPError):
            result.raise_for_status()

    def test_removed_or_forbidden_cask_is_not_retried(self):
        for status in (403, 404):
            result, calls = self.fetch([status])
            self.assertEqual(result.status_code, status)
            self.assertEqual(calls, [status])

    def test_stalled_connections_and_reads_are_not_retried(self):
        with COLLECTOR.build_cask_session() as session:
            retry = session.get_adapter('https://').max_retries
            self.assertEqual((retry.connect, retry.read, retry.other), (0, 0, 0))
            self.assertEqual(retry.allowed_methods, {'GET'})
