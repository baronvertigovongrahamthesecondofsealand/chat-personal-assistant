#!/usr/bin/python3

config_wakeword     = ["hey computer", "a computer", "say computer", "computer i have a question", "computer, i have a question", "wake up computer", "wake up, computer"]
config_sleepword    = ["thats all", "that's all", "thank you", "go back to sleep", "thats enough for now", "that's enough for now", "thats all for now", "that's all for now"]
config_stopword     = ["end query", "never mind query", "nevermind query", "disregard query", "break query", "stop query"]
config_detailword   = ["in detail"]

import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"

import sys
import json

import openai
model_name = "gpt-3.5-turbo"
# set the following in .bash_profile
openai.organization = os.getenv("OPEN_API_ORG")
openai.api_key = os.getenv('OPENAI_API_KEY')        # set in .bash_profile

import speech_recognition as sr
r = sr.Recognizer()

from vosk import SetLogLevel
SetLogLevel(-1) # Hide Vosk logs

# import pyttsx3
# engine = pyttsx3.init()
# voice = engine.getProperty('voices')[0]
# engine.setProperty('voice', voice.id)

import pygame
pygame.mixer.init()

from io import BytesIO
from gtts import gTTS

chat_history_file = "history.log"
f = open(chat_history_file, "a")
f.close()

# ------------------------------------------------------

def text_to_voice_gtts(text):
    mp3_buffer = BytesIO()
    tts = gTTS(text=text, lang="en", slow=False)
    tts.write_to_fp(mp3_buffer)
    mp3_buffer.seek(0)

    pygame.mixer.music.load(mp3_buffer)
    pygame.mixer.music.play()

    while wait_for_interrupt() and wait_for_speaking():
        continue

# def text_to_voice_pyttsx3(text):
#     engine.setProperty('voice', 'english')  # changes the voice
#     engine.say(text)
#     engine.runAndWait()

def text_to_voice(text):
    text_to_voice_gtts(text)
    # text_to_voice_pyttsx3(text)

def play_sound(type):
    sound_filename = "samples/computer_" + type + ".mp3"
    pygame.mixer.music.load(sound_filename)
    pygame.mixer.music.play()

def listen():
    with sr.Microphone(chunk_size=8192) as source:
        try:
            r.adjust_for_ambient_noise(source)
            audio = r.listen(source, 10, 3)
        except sr.WaitTimeoutError:
            return ""

    # text = r.recognize_google(audio)
    text = json.loads(r.recognize_vosk(audio, 'en'))['text']

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
        print("- listening for query...")
        play_sound('wakeup')

        text = ""

        try:
            text = listen()
            # print('>>> ' + text)

        except sr.UnknownValueError as e:
            play_sound('error')
            print("- back to sleep...")
            break

        if not text:
            continue

        if text.lower() in config_sleepword:
            play_sound('accepted')
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

        f = open(chat_history_file, "r")
        chat_history = f.read()
        print(chat_history)
        wrapped_text = chat_history + "concisely answer the following: " + text

        for detailword in config_detailword:
            if detailword in text.lower():
                wrapped_text = "answer the following: " + text

        play_sound('processing')
        print("- query detected: " + text)

        try:
            print('- sending to chatgpt: "' + wrapped_text+'"')
            response = openai.ChatCompletion.create(model=model_name, messages=[{"role": "user", "content": wrapped_text}])
            response_text = response.choices[0].message.content
        except openai.error.RateLimitError as e:
            play_sound('error')
            print("!!! openai exception: " + e.user_message)
            text_to_voice("open ai exception: " + e.user_message)
            print("- back to sleep...")
            break
        except openai.error.APIConnectionError as e:
            play_sound('error')
            print("!!! openai exception: " + e.user_message)
            text_to_voice("open ai exception: " + e.user_message)
            print("- back to sleep...")
            break

        if text and response_text:
            f = open(chat_history_file, "a")
            f.write("user: " + text + "\n")
            f.write("chatgpt: " + response_text + "\n")
            f.close()
            print("- chatgpt response: " + response_text)
            text_to_voice(response_text)

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
