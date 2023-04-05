#!/usr/bin/python3
assistant_name = "computer"

config_wakeword     = [f"hey {assistant_name}", f"a {assistant_name}", f"say {assistant_name}", f"{assistant_name} i have a question", f"{assistant_name}, i have a question", f"wake up {assistant_name}", f"wake up, {assistant_name}"]
config_sleepword    = ["thats all", "that's all", "thank you", "go back to sleep", "thats enough for now", "that's enough for now", "thats all for now", "that's all for now"]
config_stopword     = ["end query", "never mind query", "nevermind query", "disregard query", "break query", "stop query"]
config_detailword   = ["in detail"]
config_greetings    = ["how can i help?", "what can i help you with?", "do you have a question?", "i am ready to answer your question.", "what do you need?", "yes sir?"]

maintain_conversation_history = False

import os
import sys
import json
# import argparse
import random
import openai
from io import BytesIO
from gtts import gTTS
import pygame

# use vosk for voice recognition
import speech_recognition as sr
import pyttsx3
from vosk import SetLogLevel

import pyttsx3

import whisper

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"

# set the following in .bash_profile
openai.organization = os.getenv("OPEN_API_ORG")
openai.api_key = os.getenv('OPENAI_API_KEY')
gpt_model_name = "gpt-3.5-turbo"
whisper_model = whisper.load_model('base')

r = sr.Recognizer()
SetLogLevel(-1) # Hide Vosk logs

engine = pyttsx3.init()
voice = engine.getProperty('voices')[0]
engine.setProperty('voice', voice.id)

# run mimic3 --voices to find which voices you have available
# preview voices and speakers here: https://mycroftai.github.io/mimic3-voices/
# run mimic3-download to get more
mimic3_selected_voice = "en_US/m-ailabs_low"
mimic3_selected_speaker = "2"

pygame.mixer.init()

chat_history_file = "history.log"
f = open(chat_history_file, "a")
f.close()

# ------------------------------------------------------

def text_to_speech_mimic3(text):
    os.system(f'mimic3 "{text}" --voice {mimic3_selected_voice} --speaker {mimic3_selected_speaker}')

def text_to_speech_gtts(text):
    mp3_buffer = BytesIO()
    tts = gTTS(text=text, lang="en", slow=False)
    tts.write_to_fp(mp3_buffer)
    mp3_buffer.seek(0)

    pygame.mixer.music.load(mp3_buffer)
    pygame.mixer.music.play()

    while wait_for_interrupt() and wait_for_speaking():
        continue

def text_to_speech_pyttsx3(text):
    engine.setProperty('voice', 'english')  # changes the voice
    engine.say(text)
    engine.runAndWait()

def text_to_speech(text):
    text_to_speech_mimic3(text)
    # text_to_speech_gtts(text)
    # text_to_speech_pyttsx3(text)

def play_sound(type):
    sound_filename = "samples/computer_" + type + ".mp3"
    pygame.mixer.music.load(sound_filename)
    pygame.mixer.music.play()

def listen_with_whisper():
    with sr.Microphone(chunk_size=8192) as source:
        try:
            r.adjust_for_ambient_noise(source)
            audio = r.listen(source, 10, 3)
        except sr.WaitTimeoutError:
            return ""

    with open("test_speech.wav", "wb") as wav_file:
        wav_file.write(audio.get_wav_data())
        wav_file.close()

    audio = whisper.load_audio("test_speech.wav")
    audio = whisper.pad_or_trim(audio)

    # make log-Mel spectrogram and move to the same device as the model
    mel = whisper.log_mel_spectrogram(audio).to(whisper_model.device)

    # detect the spoken language
    _, probs = whisper_model.detect_language(mel)

    # decode the audio
    options = whisper.DecodingOptions()
    result = whisper.decode(whisper_model, mel, options)

    text = result.text.rstrip('.').rstrip('!')

    # print the recognized text
    # print(text)

    return text

def listen_with_sr():
    with sr.Microphone(chunk_size=8192) as source:
        try:
            r.adjust_for_ambient_noise(source)
            audio = r.listen(source, 10, 3)
        except sr.WaitTimeoutError:
            return ""

    # text = r.recognize_google(audio)
    text = json.loads(r.recognize_vosk(audio, 'en'))['text']

    return text

def listen():
    text = listen_with_whisper()
    # text = listen_with_sr()

    return text

def wait_for_speaking():
    return pygame.mixer.music.get_busy()

def wait_for_interrupt():
    text = ""

    try:
        text = listen()
        # print('>>>: ' + text)
    except sr.UnknownValueError:
        return True

    if text.lower() in config_stopword:
        pygame.mixer.music.stop()
        play_sound('accepted')
        print("- interrupted...")
        return False

    return True

def wait_for_wakeup():
    text_to_speech(f"personal chat assistant online. my name is {assistant_name}. entering idle state until woken.")
    print("- listening for wake word...")

    while True:
        text = ""

        try:
            text = listen()
            # print('>>> ' + text)
        except sr.UnknownValueError:
            pass

        if text.lower() in config_wakeword:
            print("- waking up")
            wait_for_query()

def wait_for_query():
    while True:
        play_sound('wakeup')
        text_to_speech(random.choice(config_greetings))
        print("- listening for query...")

        text = ""

        try:
            text = listen()
            # print('>>> ' + text)

        except sr.UnknownValueError as e:
            play_sound('error')
            text_to_speech("there was an error in processing audio input. going back to sleep.")
            print("- back to sleep...")
            break

        if not text:
            continue

        if text.lower() in config_sleepword:
            play_sound('accepted')
            text_to_speech("if you need assistance again, let me know. going back to sleep.")
            print("- back to sleep...")
            break

        stophere = False

        for stopword in config_stopword:
            if stopword in text.lower():
                play_sound('accepted')
                stophere = True
                break

        if stophere:
            continue

        wrapped_text = "concisely answer the following: " + text
        for detailword in config_detailword:
            if detailword in text.lower():
                wrapped_text = text
                break

        if maintain_conversation_history:
            f = open(chat_history_file, "r")
            chat_history = f.read()
            print(chat_history)
            wrapped_text = chat_history + wrapped_text

        play_sound('processing')
        text_to_speech("processing...")
        print("- query detected: " + text)

        try:
            print('- sending to chatgpt: "' + wrapped_text+'"')
            response = openai.ChatCompletion.create(model=gpt_model_name, messages=[{"role": "user", "content": wrapped_text}])
            response_text = response.choices[0].message.content
        except openai.error.RateLimitError as e:
            play_sound('error')
            print("!!! openai exception: " + e.user_message)
            text_to_speech("open ai exception: " + e.user_message)
            print("- back to sleep...")
            break
        except openai.error.APIConnectionError as e:
            play_sound('error')
            print("!!! openai exception: " + e.user_message)
            text_to_speech("open ai exception: " + e.user_message)
            print("- back to sleep...")
            break

        if text and response_text:
            play_sound('accepted')
            print("- chatgpt response: " + response_text)
            text_to_speech(response_text)
            if maintain_conversation_history:
                f = open(chat_history_file, "a")
                f.write("user: " + text + "\n")
                f.write("chatgpt: " + response_text + "\n")
                f.close()

def intro():
    print("-- chat personal assistant --")
    print()
    print("wake words: use these to wake up the assistant from ignoring input")
    print(config_wakeword)
    print()
    print("stop words: use these to interrupt a response or break from input")
    print(config_stopword)
    print()
    print("detail words: use these before a query to get more detailed answers, defaults to concise responses")
    print(config_detailword)
    print()
    print("sleep words: use these to put the assistant back into idle")
    print(config_sleepword)
    print()

def main():
    intro()
    wait_for_wakeup()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(130)
        except SystemExit:
            os._exit(130)
