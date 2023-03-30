# chat-personal-assistant

This is a voice assistant that listens for a keyword, responds with beeps and boops, then listens for your queries to pass on the (currently) the OpenAI API. It then  speaks the result.

Inspiration from https://github.com/Infatoshi/chatgpt-voice-assistant - thanks!

Libs:
- speech_recognition: For speech-to-text capabilities. This can be configured to use a variety of engines.
  - vosk: Engine currently in use for speech-to-text.
  - google: Can be used instead of vosk.
- openai: For getting an intelligent response to your query from a higher power.
- gTTS: Currently using this for text-to-speech of the query response.
- pyttsx3: Can be used instead of gTTS.
- pygame: For the audio output

Install:
- set up an openai api key, save this and your openai api org (found in your profile) to .bash_profile using var names
  - OPEN_API_ORG
  - OPEN_API_KEY
- run: pip install openai python-dotenv SpeechRecognition pyttsx3 gtts vosk pygame

Usage:

    chmod +x main.py
    ./main.py

Will start up and display:

    - listening for keyword...

Speaking one of the wake words will wake up the assistant, listen for a query, and display:

    - listening for query...

Anything spoken at this point will be sent to ChatGPT, and returned as text, which will then be spoken back to you.
Once done, it will once again listen for a new query.

Any time it waits for your query, it can be returned to idle by speaking one of the sleep words.

The stop words can be used while the assistant is returning a response, but currently only works if the output cant be heard by the microphone.

By default, the responses will be short and concise. You can override this to be a detailed response by speaking one of the detail words in the query, which I would recommend be done at the beginning of the query.

Unfortunately, the longer the response generated by ChatGPT, the longer the it will take to hear anything, as there is processing and network latency to both ChatGPT and gTTS. This can be cut down a bit by using locally hosted TTS (such as pyttsx3) and language interfaces (such as Mycroft or LLama, not implemented here).

Have fun!
