POLISH_VOICES = {'rachel': '21m00Tcm4TlvDq8ikWAM', 'domi': 'AZnzlk1XvdvUeBnXmlld'}

class ElevenLabsTTS:
    def synthesize(self, text, voice='default'):
        return b'audio'

def get_tts():
    return ElevenLabsTTS()

def text_to_speech(text, voice='rachel'):
    return get_tts().synthesize(text, voice)
