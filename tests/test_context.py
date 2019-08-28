# coding: utf-8

from alexandra import Context


class TestContext:
    '''alexandra.context.Context'''

    def setup_class(self):
        self.context = Context({
    "AudioPlayer": {},
    "Display": {},
    "System": {
      "application": {
        "applicationId": "[AppId]"
      },
      "user": {
        "userId": "[UserId]"
      },
      "device": {
        "deviceId": "[DeviceId]",
        "supportedInterfaces": {
          "AudioPlayer": {},
          "Alexa.Presentation.APL": {
            "runtime": {
              "maxVersion": "1.1"
            }
          }
        }
      },
      "apiEndpoint": "https://api.amazonalexa.com",
      "apiAccessToken": "<apiAccessToken-value>"
    }
  })

    def test_sanity(self):
        assert self.context.audio_player == {}
        assert self.context.display == {}
        assert self.context.application_id == "[AppId]"
        assert self.context.user_id == "[UserId]"
        assert self.context.device_id == "[DeviceId]"
        assert self.context.apl_version == "1.1"
        assert self.context.apl_version_available("1.0") == True
        assert self.context.apl_version_available("1.1") == True



