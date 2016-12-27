try:
    from cStringIO import StringIO
except:
    from io import StringIO

import datetime as dt
import logging

from alexandra import util


class TestRespond:
    '''alexandra.util.respond'''

    def test_sanity(self):
        resp = util.respond()

        assert resp == {
            'version': '1.0',
            'response': {
                'outputSpeech': {'type': 'PlainText', 'text': ''},
                'shouldEndSession': True
            },
            'sessionAttributes': {}
        }

    def test_output_format(self):
        resp = util.respond(text='foobar')
        assert resp['response'] == {
            'outputSpeech': {'type': 'PlainText', 'text': 'foobar'},
            'shouldEndSession': True
        }

        resp = util.respond(ssml='foobar')
        assert resp['response'] == {
            'outputSpeech': {'type': 'SSML', 'ssml': 'foobar'},
            'shouldEndSession': True
        }

    def test_reprompt(self):
        resp = util.respond(reprompt_text='foobar')
        assert resp['response']['reprompt'] == {
            'outputSpeech': {'type': 'PlainText', 'text': 'foobar'}
        }

        resp = util.respond(reprompt_ssml='foobar')
        assert resp['response']['reprompt'] == {
            'outputSpeech': {'type': 'SSML', 'ssml': 'foobar'}
        }

    def test_argument_mashup(self):
        resp = util.respond(text='foo', reprompt_ssml='bar',
                            attributes={'a': 'b'}, end_session=False)

        assert resp == {
            'version': '1.0',
            'response': {
                'outputSpeech': {'type': 'PlainText', 'text': 'foo'},
                'shouldEndSession': False,
                'reprompt': {
                    'outputSpeech': {'type': 'SSML', 'ssml': 'bar'}
                }
            },
            'sessionAttributes': {'a': 'b'}
        }


class TestReprompt:
    '''alexandra.util.reprompt'''

    def test_reprompt_sanity(self):
        assert util.reprompt(text='foo') == util.respond(reprompt_text='foo', end_session=False)
        assert util.reprompt(ssml='foo') == util.respond(reprompt_ssml='foo', end_session=False)


class TestValidateTimestamp:
    '''alexandra.util.validate_request_timestamp'''

    def setup_class(self):
        self.log = StringIO()
        self.logger = logging.StreamHandler(stream=self.log)

        logging.getLogger('alexandra').addHandler(self.logger)

    def teardown_class(self):
        logging.getLogger('alexandra').removeHandler(self.logger)

    def last_log(self):
        value = self.log.getvalue()
        self.log.truncate(0)
        self.log.seek(0)

        return value

    def test_missing_timestamp(self):
        assert util.validate_request_timestamp({}) is False
        assert self.last_log() == 'timestamp not present {}\n'

    def test_expired_timestamp(self):
        future = dt.datetime.utcnow() + dt.timedelta(hours=3)
        past = dt.datetime.utcnow() - dt.timedelta(hours=3)

        assert util.validate_request_timestamp({
            'request': {'timestamp': future.strftime('%Y-%m-%dT%H:%M:%SZ')}
        }) is False

        assert 'timestamp difference too high' in self.last_log()

        assert util.validate_request_timestamp({
            'request': {'timestamp': past.strftime('%Y-%m-%dT%H:%M:%SZ')}
        }) is False

        assert 'timestamp difference too high' in self.last_log()

    def test_good_timestamp(self):
        now = dt.datetime.utcnow()

        assert util.validate_request_timestamp({
            'request': {'timestamp': now.strftime('%Y-%m-%dT%H:%M:%SZ')}
        }) is True


class TestValidateCertificate:
    '''alexandra.util.validate_request_certificate'''

    def setup_class(self):
        self.log = StringIO()
        self.logger = logging.StreamHandler(stream=self.log)

        logging.getLogger('alexandra').addHandler(self.logger)

    def teardown_class(self):
        self.log.close()
        logging.getLogger('alexandra').removeHandler(self.logger)

    def last_log(self):
        value = self.log.getvalue()
        self.log.truncate(0)
        self.log.seek(0)

        return value

    def test_bogus_urls(self):
        '''explicitly given by amazon docs as failure cases'''

        cases = [
            'http://s3.amazonaws.com/echo.api/echo-api-cert.pem',
            'https://notamazon.com/echo.api/echo-api-cert.pem',
            'https://s3.amazonaws.com/EcHo.aPi/echo-api-cert.pem',
            'https://s3.amazonaws.com/invalid.path/echo-api-cert.pem',
            'https://s3.amazonaws.com:563/echo.api/echo-api-cert.pem',
        ]

        for case in cases:
            assert util._get_certificate(case) is None
            assert self.last_log() == 'invalid cert location %s\n' % case

    def test_good_url_expired_cert(self):
        '''correctly formatted url, but certificate expired'''

        cases = [
            'https://s3.amazonaws.com/echo.api/echo-api-cert.pem',
            'https://s3.amazonaws.com:443/echo.api/echo-api-cert.pem',
        ]

        for case in cases:
            assert util._get_certificate(case) is None
            assert self.last_log() == 'certificate expired or invalid\n'
