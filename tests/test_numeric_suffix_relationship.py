"""Numeric release/build fixtures use synthetic hashes and bundle identities."""
from dataclasses import replace
import http.client
import io
import json
import signal
import time
import unittest
from unittest.mock import Mock, patch

import urllib3.response

import test_dmg_reconciliation as integration
import test_version_relation as original

policy = original.policy
c = integration.c
SHA = original.SHA


def request(raw='26.8.2', short='26.8.2.2', prior='26.8.1'):
    i = original.request(raw, short, prior)
    return replace(i, vendor_sha256=SHA,
                   observation=replace(i.observation, bundle_version=short))


class NumericSuffixTests(unittest.TestCase):
    def test_vendor_checked_extra_numeric_components_publish_exact_bundle_text(self):
        for raw, short in [('26.8.2', '26.8.2.2'), ('12.11.12', '12.11.12.2'),
                           ('4.5', '4.5.102000'), ('1.2', '1.2.0.3')]:
            with self.subTest(raw=raw, short=short):
                d = policy.reconcile(request(raw, short, '1.0'))
                self.assertEqual((d.action, d.version, d.sha, d.relation, d.verified),
                                 ('WRITE', short, SHA, 'VENDOR_CHECKED_NUMERIC_SUFFIX', True))

    def test_trae_meetingbar_and_non_numeric_or_non_component_changes_stay_held(self):
        for raw, short in [('2.3.99397', '3.6.13'), ('5.0.0', '5.0.1'),
                           ('26.8.2', '26.8.20.2'), ('26.8.2', '26.8.2.2rc1'),
                           ('26.8.2', '26.8.2-demo'), ('26.8.2,2', '26.8.2.2'),
                           ('26.8.2', '26.8.2.02'), ('26.08.2', '26.08.2.2'),
                           ('26.8.2', '26.8.2.٢'), ('26.8.2', '26.8.2.2\n')]:
            with self.subTest(raw=raw, short=short):
                d = policy.reconcile(request(raw, short, '1.0'))
                self.assertEqual((d.action, d.reason), ('HOLD', 'RELATION_UNPROVEN'))

    def test_cask_and_vendor_hashes_are_both_required(self):
        i = request()
        for vendor in [None, '', 'b' * 64, 'A' * 64, 'no_check', 'a' * 63]:
            with self.subTest(vendor=vendor):
                d = policy.reconcile(replace(i, vendor_sha256=vendor))
                self.assertEqual((d.action, d.reason), ('HOLD', 'RELATION_UNPROVEN'))
        self.assertEqual(policy.reconcile(replace(i, declared_sha256=None)).action, 'HOLD')

    def test_identity_inspector_build_and_integrity_gates_cannot_be_overridden(self):
        i = request()
        for obs in [replace(i.observation, bundle_id='org.example.other'),
                    replace(i.observation, artifact_sha256='b' * 64),
                    replace(i.observation, inspector='other')]:
            self.assertEqual(policy.reconcile(replace(i, observation=obs)).reason,
                             'OBSERVATION_INCONSISTENT')
        self.assertEqual(policy.reconcile(replace(i, observation=replace(i.observation,
                         bundle_version='26.8.2.1'))).reason, 'RELATION_UNPROVEN')
        refusal = policy.InspectionRefusal('HASH_MISMATCH', True)
        self.assertEqual(policy.reconcile(replace(i, observation=refusal)).reason, 'HASH_MISMATCH')

    def test_monotonic_order_refresh_and_old_relations_are_preserved(self):
        for prior, action, reason in [('26.8.3', 'HOLD', 'DETECTION_REGRESSION'),
                                     ('opaque', 'HOLD', 'PRIOR_ORDER_UNKNOWN'),
                                     ('26.8.2.2.0', 'HOLD', 'EQUAL_ORDER_TEXT_DIFFERS'),
                                     ('26.8.2.2', 'REFRESH', 'EXACT_TEXT_UNCHANGED')]:
            d = policy.reconcile(request(prior=prior))
            self.assertEqual((d.action, d.reason), (action, reason))
        d = policy.reconcile(request('26.8.2', '26.8.2.0', '26.8.1'))
        self.assertEqual(d.relation, 'PAD')


class ChecksumSidecarTests(unittest.TestCase):
    URL = 'https://vendor.example.invalid/fixture.dmg'

    def read(self, body, status=200):
        response = Mock(status_code=status)
        response.iter_content.return_value = [body]
        with patch.object(c.requests, 'get', return_value=response) as get:
            result = c.read_vendor_sha256(self.URL)
        get.assert_called_once_with(self.URL + '.sha256', stream=True,
                                    timeout=(5, 5), allow_redirects=False)
        response.close.assert_called_once()
        return result

    def test_checksum_is_bound_to_exact_filename(self):
        self.assertEqual(self.read((SHA + '  fixture.dmg\n').encode()), SHA)
        self.assertEqual(self.read((SHA + ' *fixture.dmg\n').encode()), SHA)
        for body in [(SHA + '  other.dmg\n').encode(), SHA.encode(),
                     (SHA + '  fixture.dmg\n' + SHA + '  other.dmg\n').encode(),
                     b'<html>not a checksum</html>', b'\xff', b'x' * 4097]:
            with self.subTest(body=body[:80]):
                self.assertIsNone(self.read(body))

    def test_redirect_or_error_has_no_retry_and_no_body_read(self):
        for status in [301, 302, 403, 404, 429, 500]:
            response = Mock(status_code=status)
            with patch.object(c.requests, 'get', return_value=response) as get:
                self.assertIsNone(c.read_vendor_sha256(self.URL))
            get.assert_called_once()
            response.iter_content.assert_not_called()
            response.close.assert_called_once()

    def test_query_auth_fragment_or_non_https_url_is_not_requested(self):
        for url in ['http://vendor.example.invalid/fixture.dmg',
                    self.URL + '?token=fixture', self.URL + '#part',
                    'https://user:password@vendor.example.invalid/fixture.dmg',
                    'https://@vendor.example.invalid/fixture.dmg', 'https://[/fixture.dmg',
                    'https://vendor.example.invalid/fixture.pkg', None]:
            with patch.object(c.requests, 'get') as get:
                self.assertIsNone(c.read_vendor_sha256(url))
                get.assert_not_called()

    def test_request_timeout_fails_closed_and_restores_alarm(self):
        previous = signal.getsignal(signal.SIGALRM)
        with patch.object(c.requests, 'get', side_effect=c.requests.Timeout):
            self.assertIsNone(c.read_vendor_sha256(self.URL))
        self.assertEqual(signal.getsignal(signal.SIGALRM), previous)
        self.assertEqual(signal.getitimer(signal.ITIMER_REAL), (0, 0))

    def test_wall_clock_deadline_interrupts_request_before_response_exists(self):
        previous = signal.getsignal(signal.SIGALRM)

        def stalled_request(*args, **kwargs):
            time.sleep(1)
            self.fail('request was not interrupted')

        with patch.object(c.requests, 'get', side_effect=stalled_request), \
                patch.object(c, 'VENDOR_CHECKSUM_DEADLINE', 0.03):
            self.assertIsNone(c.read_vendor_sha256(self.URL))
        self.assertEqual(signal.getsignal(signal.SIGALRM), previous)
        self.assertEqual(signal.getitimer(signal.ITIMER_REAL), (0, 0))

    def test_wall_clock_deadline_interrupts_real_urllib3_chunked_trailers(self):
        body = (SHA + '  fixture.dmg\n').encode()
        wire = (b'HTTP/1.1 200 OK\r\nTransfer-Encoding: chunked\r\n\r\n' +
                ('%x\r\n' % len(body)).encode() + body + b'\r\n0\r\n')

        class TrailerStream(io.BytesIO):
            trailers = 0

            def readline(self, *args):
                line = super().readline(*args)
                if not line and self.trailers < 1000:
                    self.trailers += 1
                    time.sleep(0.002)
                    return b'X-Fixture-Trailer: keep-reading\r\n'
                return line or b'\r\n'

        stream = TrailerStream(wire)
        sock = Mock()
        sock.makefile.return_value = stream
        transport = http.client.HTTPResponse(sock, method='GET')
        transport.begin()
        response = c.requests.Response()
        response.status_code = 200
        response.raw = urllib3.response.HTTPResponse(
            body=transport, original_response=transport, preload_content=False,
            headers={'Transfer-Encoding': 'chunked'}, request_method='GET')
        previous = signal.getsignal(signal.SIGALRM)
        with patch.object(c.requests, 'get', return_value=response), \
                patch.object(c, 'VENDOR_CHECKSUM_DEADLINE', 0.03), \
                patch.object(response, 'close', wraps=response.close) as close:
            self.assertIsNone(c.read_vendor_sha256(self.URL))
            close.assert_called_once()
        self.assertGreater(stream.trailers, 0)
        self.assertLess(stream.trailers, 1000)
        self.assertEqual(signal.getsignal(signal.SIGALRM), previous)
        self.assertEqual(signal.getitimer(signal.ITIMER_REAL), (0, 0))

    def test_occupied_or_unavailable_alarm_never_starts_a_request(self):
        with patch.object(c.signal, 'getitimer', return_value=(1, 0)), \
                patch.object(c.signal, 'signal') as handler, \
                patch.object(c.signal, 'setitimer') as timer, \
                patch.object(c.requests, 'get') as get:
            self.assertIsNone(c.read_vendor_sha256(self.URL))
            handler.assert_not_called()
            timer.assert_not_called()
            get.assert_not_called()
        with patch.object(c.threading, 'current_thread', return_value=object()), \
                patch.object(c.requests, 'get') as get:
            self.assertIsNone(c.read_vendor_sha256(self.URL))
            get.assert_not_called()
        with patch.object(c, 'signal', object()), patch.object(c.requests, 'get') as get:
            self.assertIsNone(c.read_vendor_sha256(self.URL))
            get.assert_not_called()


class NumericSuffixCollectorTests(unittest.TestCase):
    run_case = integration.CollectorIntegrationTests.run_case

    def test_collector_writes_exact_bundle_text_and_reuses_the_inspected_hash(self):
        obs = c.BundleObservation(integration.SHA, integration.BUNDLE, '26.8.2.2', '26.8.2.2')
        _, new, report = self.run_case(obs, raw='26.8.2', prior='26.8.1',
                                      declared_sha=integration.SHA, vendor_sha=integration.SHA)
        self.assertEqual((json.loads(new)['version'], json.loads(new)['sha']),
                         ('26.8.2.2', integration.SHA))
        self.assertEqual(report['versionEvidence'][0]['vendorSha256'], integration.SHA)
        self.assertEqual(report['versionEvidence'][0]['relation'], 'VENDOR_CHECKED_NUMERIC_SUFFIX')
        self.assertEqual(report['failures'], [])

    def test_missing_or_wrong_vendor_checksum_and_no_check_preserve_prior_bytes(self):
        obs = c.BundleObservation(integration.SHA, integration.BUNDLE, '26.8.2.2', '26.8.2.2')
        for declared, vendor in [(integration.SHA, None), (integration.SHA, 'c' * 64),
                                 ('no_check', integration.SHA)]:
            old, new, report = self.run_case(obs, raw='26.8.2', prior='26.8.1',
                                          declared_sha=declared, vendor_sha=vendor)
            self.assertEqual(old, new)
            self.assertEqual(report['failures'][0]['reason'], 'RELATION_UNPROVEN')

    def test_checksum_reader_is_not_used_for_other_holds_or_existing_relations(self):
        app = {'version': '2.3.99397', 'bundleId': integration.BUNDLE,
               'fileName': 'fixture.dmg', 'url': 'https://example.invalid/fixture.dmg'}
        prior = {'version': '2.3.61406', 'sha': 'b' * 64, 'url': 'https://example.invalid/old.dmg'}
        for raw, short, build in [('2.3.99397', '3.6.13', '3.6.13'),
                                  ('5.0.0', '5.0.1', '172'),
                                  ('26.8.2', '26.8.2', '26.8.2')]:
            obs = c.BundleObservation(integration.SHA, integration.BUNDLE, short, build)
            with patch.object(c.shutil, 'which', return_value='/fake/hdiutil'), \
                    patch.object(c, 'inspect_dmg_artifact', return_value=obs), \
                    patch.object(c, 'read_vendor_sha256') as get:
                try:
                    c.reconcile_vendor_dmg(dict(app, version=raw), prior,
                                           {'version': raw, 'sha256': integration.SHA}, 'fixture')
                except c.CatalogVersionHold:
                    pass
                get.assert_not_called()


if __name__ == '__main__':
    unittest.main()
