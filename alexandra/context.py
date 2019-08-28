import json
from packaging import version

class Context:
    """Provides easier access to context objects sent along with requests.

    The object parsed from the request can be accessed directly
    through the :py:attr:`body` member.
    """

    def __init__(self, context_body):
        self.body = context_body

    def __repr__(self):
        return '<Contect %s>' % json.dumps(self.body)

    @property
    def audio_player(self):
        return self.body['AudioPlayer']

    @property
    def display(self):
        return self.body['Display']

    @property
    def application_id(self):
        return self.body['System']['application']['applicationId']

    @property
    def user_id(self):
        return self.body['System']['user'].get('userId')

    @property
    def device_id(self):
        return self.body['System']['device'].get('deviceId')

    @property
    def apl_version(self):
        apl = self.body['System']['device']['supportedInterfaces'].get('Alexa.Presentation.APL')
        if apl:
            return apl['runtime']['maxVersion']
        else:
            return "0.0"

    def apl_version_available(self, v):
        apl = self.body['System']['device']['supportedInterfaces'].get('Alexa.Presentation.APL')
        if apl:
            return version.parse(apl['runtime']['maxVersion']) >= version.parse(v)
        else:
            return False


    def get(self, attr, default=None):
        """Get an attribute defined by this session"""

        attrs = self.body.get('attributes') or {}
        return attrs.get(attr, default)
