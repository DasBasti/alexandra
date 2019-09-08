import pytest

from alexandra import util
from alexandra.app import Application


def _request(req_type, session=None):
    return {
        'request': {
            'type': req_type,
        },
        'session': session
    }


def _intent(name, slots=None, ids={}, session=None, context=None):
    req = _request('IntentRequest', session)

    req['request']['intent'] = {
        'name': name,
        'slots': {
            k: {'name': k, 'value': v, "resolutions": {"resolutionsPerAuthority": [{"status": {"code": "ER_SUCCESS_MATCH"},"values": [{"value": {"id": ids.get(k)}}]}]}}
            for k, v in (slots or {}).items()
        }
    }
    req['context'] = context

    return req


def _intent_no_match(name, slots=None, ids={}, session=None, context=None):
    req = _request('IntentRequest', session)

    req['request']['intent'] = {
        'name': name,
        'slots': {
            k: {'name': k, 'value': v, "resolutions": {"resolutionsPerAuthority": [{"status": {"code": "ER_SUCCESS_NO_MATCH"},"values": [{"value": {"id": ids.get(k)}}]}]}}
            for k, v in (slots or {}).items()
        }
    }
    req['context'] = context

    return req


def test_sanity():
    '''If this fails the sky is falling.'''
    app = Application()

    assert app.dispatch_request(_request('LaunchRequest')) == app.launch_fn(None)
    assert app.dispatch_request(_intent('Foo')) == app.unknown_intent_fn(None, None)
    assert app.dispatch_request(_request('SessionEndedRequest')) == app.session_end_fn()


def test_launch_request():
    app = Application()

    @app.launch
    def launch(sesh):
        assert sesh.get('fizz') == 'buzz'
        return 123

    sesh = {'attributes': {'fizz': 'buzz'}}
    assert app.dispatch_request(_request('LaunchRequest', sesh)) == 123

    @app.launch
    def launch_no_session(sesh):
        assert sesh is None
        return 456

    assert app.dispatch_request(_request('LaunchRequest')) == 456


def test_intent_noargs():
    app = Application()

    slots = {'fizz': 'buzz', 'ab': 'cd'}
    session = {'attributes': {'foo': 'bar'}}

    @app.intent('Foo')
    def foo():
        return 'foo'

    @app.intent('Bar')
    def bar():
        return 'bar'

    assert app.dispatch_request(_intent('Foo')) == 'foo'
    assert app.dispatch_request(_intent('Foo', slots=slots, session=session)) == 'foo'
    assert app.dispatch_request(_intent('Bar')) == 'bar'


def test_intent_withargs():
    app = Application()

    @app.intent('Foo')
    def foo(slots, session):
        assert slots.get('fizz') == 'buzz'
        assert session.get('foo') == 'bar'

        return 'foo'

    slots = {'fizz': 'buzz', 'ab': 'cd'}
    session = {'attributes': {'foo': 'bar'}}

    assert app.dispatch_request(_intent('Foo', slots=slots, session=session)) == 'foo'


def test_intent_withargs_id():
    app = Application()

    @app.intent('Bar')
    def bar(slots, ids, session):
        assert slots.get('fizz') == 'buzz'
        assert ids.get('fizz') == 'BUZZ'
        assert session.get('foo') == 'bar'

        return 'bar'

    slots = {'fizz': 'buzz', 'ab': 'cd'}
    ids = {'fizz':'BUZZ', 'ab': 'CD'}
    session = {'attributes': {'foo': 'bar'}}
    
    assert app.dispatch_request(_intent('Bar', slots=slots, ids=ids, session=session)) == 'bar'


def test_intent_withargs_id_context():
    app = Application()

    @app.intent('Bar')
    def bar(slots, ids, session, context):
        assert slots.get('fizz') == 'buzz'
        assert ids.get('fizz') == 'BUZZ'
        assert session.get('foo') == 'bar'
        assert context.get('baz') == 'BAZ'

        return 'bar'

    slots = {'fizz': 'buzz', 'ab': 'cd'}
    ids = {'fizz':'BUZZ', 'ab': 'CD'}
    session = {'attributes': {'foo': 'bar'}}
    context = {'baz': 'BAZ'}
    
    assert app.dispatch_request(_intent('Bar', slots=slots, ids=ids, session=session, context=context)) == 'bar'


def test_intent_withargs_id_no_match():
    app = Application()

    @app.intent('Bar')
    def bar(slots, ids, session, context):
        assert slots.get('fizz') == 'buzz'
        assert ids.get('ER_SUCCESS_NO_MATCH') == 'buzz'
        assert session.get('foo') == 'bar'
        assert context.get('baz') == 'BAZ'

        return 'bar'

    slots = {'fizz':'buzz'}
    ids = {'fizz':'buzz'}
    session = {'attributes': {'foo': 'bar'}}
    context = {'baz': 'BAZ'}
    
    assert app.dispatch_request(_intent_no_match('Bar', slots=slots, ids=ids, session=session, context=context)) == 'bar'


def test_intent_badargs():
    app = Application()

    with pytest.raises(ValueError):
        @app.intent('Foo')
        def bad_intent_handler(a, b, c, d, e, f):
            pass


def test_unknown_request_type():
    with pytest.raises(ValueError):
        Application().dispatch_request(_request(req_type='something bad'))


def test_unknown_intent_handler():
    app = Application()

    @app.unknown_intent
    def unknown_handler_no_args():
        return 'foo'

    assert app.dispatch_request(_intent('What?')) == 'foo'

    @app.unknown_intent
    def unknown_handler_with_args(slots, session):
        assert slots.get('fizz') == 'buzz'
        assert session.get('foo') == 'bar'

        return 'bar'

    slots = {'fizz': 'buzz', 'ab': 'cd'}
    session = {'attributes': {'foo': 'bar'}}

    assert app.dispatch_request(_intent('What?', slots=slots, session=session)) == 'bar'
