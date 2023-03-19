# chat-personal-assistant

This is a voice assistant that listens for a keyword, responds with beeps and boops, then listens for your queries to pass on the (currently) the OpenAI API. It then  speaks the result.

Uses:
- speech_recognition: For speech-to-text capabilities. This can be configured to use a variety of engines.
- vosk: Currently useing this for speech-to-text.
- google: Currently useing this for speech-to-text.
- openai: For sending your query to a higher power.
- gTTS: Currently using this for text-to-speech of the query response.
- pyttsx3: Not using this currently, but can be used instead of gTTS.
- pygame: For the audio output
