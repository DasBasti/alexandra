import logging

from werkzeug.serving import run_simple

from alexandra.session import Session
from alexandra.context import Context
from alexandra.util import respond
from alexandra.wsgi import WsgiApp

log = logging.getLogger(__name__)


class Application:
    def __init__(self):
        self.intent_map = {}
        self.unknown_intent_fn = lambda x, y: respond(text='unknown intent')
        self.launch_fn = lambda _: respond()
        self.session_end_fn = respond

    def create_wsgi_app(self, validate_requests=True):
        """Return an object that can be run by any WSGI server (uWSGI,
        etc.) to serve this Alexa application.
        """

        return WsgiApp(self, validate_requests)

    def run(self, host, port, debug=True, validate_requests=True):
        """Utility method to quickly get a server up and running.

        :param debug: turns on Werkzeug debugger, code reloading, and full
            logging.
        :param validate_requests: whether or not to ensure that requests are
            sent by Amazon. This can be usefulfor manually testing the server.
        """

        if debug:
            # Turn on all alexandra log output
            logging.basicConfig(level=logging.DEBUG)

        app = self.create_wsgi_app(validate_requests)
        run_simple(host, port, app, use_reloader=debug, use_debugger=debug)

    def dispatch_request(self, body):
        """Given a parsed JSON request object, call the correct Intent, Launch,
        or SessionEnded function.

        This function is called after request parsing and validaion and will
        raise a `ValueError` if an unknown request type comes in.

        :param body: JSON object loaded from incoming request's POST data.
        """

        req_type = body.get('request', {}).get('type')
        session_obj = body.get('session', {})
        context_obj = body.get('context', {})

        session = Session(session_obj) if session_obj else None
        context = Context(context_obj) if context_obj else None

        if req_type == 'LaunchRequest':
            if self.launch_fn.__code__.co_argcount == 2:
                return self.launch_fn(session, context)
            else:
                return self.launch_fn(session)

        elif req_type == 'IntentRequest':
            intent = body['request']['intent']['name']
            intent_fn = self.intent_map.get(intent, self.unknown_intent_fn)

            slots = {
                slot['name']: slot.get('value')
                for _, slot in
                body['request']['intent'].get('slots', {}).items()
            }
            if body['request']['intent'].get('confirmationStatus'):
                slots['confirmationStatus'] = body['request']['intent'].get('confirmationStatus')

            ids = {}
            for _, slot in body['request']['intent'].get('slots', {}).items():
                if slot['resolutions']['resolutionsPerAuthority'][0]['status']['code'] == "ER_SUCCESS_MATCH":
                    ids[slot['name']] = slot['resolutions']['resolutionsPerAuthority'][0]['values'][0]['value']['id']
                else :
                    ids = {"ER_SUCCESS_NO_MATCH": slot['value']}
                    log.error('unknown query string: %s', slot['value'])
                
            arity = intent_fn.__code__.co_argcount

            if arity == 2:
                return intent_fn(slots, session)

            if arity == 3:
                return intent_fn(slots, ids, session)
            
            if arity == 4:
                return intent_fn(slots, ids, session, context)
            
            return intent_fn()

        elif req_type == 'SessionEndedRequest':
            return self.session_end_fn()

        log.error('invalid request type: %s', req_type)
        raise ValueError('bad request: %s', body)

    def launch(self, func):
        """Decorator to register a function to be called whenever the
        app receives a LaunchRequest (which happens when someone
        invokes your skill without specifying an intent). ::

            @alexa_app.launch
            def launch_handler(session):
                pass
        """

        self.launch_fn = func
        return func

    def intent(self, intent_name):
        """Decorator to register a handler for the given intent.

        The decorated function can either take 0, 2 or 3 arguments. If two are
        specified, it will be provided a dictionary of `{slot_name: value}`. If
        three are defined it will proovide a dictionary of `{slot_name: id}`
        based on the ID given in the develper console. Variante with arguments 
        also provide a :py:class:`alexandra.session.Session` instance.

        If no session was provided in the request, the session object will be
        `None`. ::

            @alexa_app.intent('FooBarBaz')
            def foo_bar_baz_intent(slots, session):
                pass
                
            @alexa_app.intent('FooBarBaz')
            def foo_bar_baz_intent(slots, ids, session):
                pass

            @alexa_app.intent('NoArgs')
            def noargs_intent():
                pass
        """

        # nested decorator so we can have params.
        def _decorator(func):
            arity = func.__code__.co_argcount

            if arity not in [0, 2, 3, 4]:
                raise ValueError("expected 0, 2, 3 or 4 argument function")

            self.intent_map[intent_name] = func
            return func

        return _decorator

    def unknown_intent(self, func):
        """Decorator to register a function to be called when an unknown intent
        is received. This should only happen when the intents/utterance file
        are malformed.
        """

        self.unknown_intent_fn = func
        return func

    def session_end(self, func):
        """ Decorator to register a function to be called when a
        SessionEndedRequest is received.
        """

        self.session_end_fn = func
        return func
