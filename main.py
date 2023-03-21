#!/usr/bin/python3

config_wakeword  = ["hey computer", "a computer", "say computer"]
config_sleepword = ["never mind", "nevermind", "disregard", "thank you"]
config_stopword = ["break", "thats enough", "stop"]

import os
import sys
import time
import json

import openai
openai.organization = os.getenv("OPEN_API_ORG")
openai.api_key = os.getenv('OPENAI_API_KEY')
model_name = "gpt-3.5-turbo"

import speech_recognition as sr
r = sr.Recognizer()

from vosk import SetLogLevel
SetLogLevel(-1) # Hide Vosk logs

import pyttsx3
engine = pyttsx3.init()
voice = engine.getProperty('voices')[0]
engine.setProperty('voice', voice.id)

import pygame
pygame.mixer.init()

from io import BytesIO
from gtts import gTTS

in_conversation = False
block_input = False

def text_to_voice_gtts(text):
    mp3_buffer = BytesIO()
    tts = gTTS(text)
    tts.write_to_fp(mp3_buffer)
    mp3_buffer.seek(0)

    pygame.mixer.music.load(mp3_buffer)
    pygame.mixer.music.play()

    while wait_for_interrupt() and wait_for_speaking() == True:
        continue

def text_to_voice_pyttsx3(text):
    engine.say(text)
    engine.runAndWait()

def text_to_voice(text):
    text_to_voice_gtts(text)

def play_sound(type):
    sound_filename = "samples/computer_" + type + ".mp3"
    pygame.mixer.music.load(sound_filename)
    pygame.mixer.music.play()

def listen():
    with sr.Microphone(chunk_size=8192) as source:
        r.adjust_for_ambient_noise(source)
        audio = r.listen(source)

    # text = r.recognize_google(audio)

    text = json.loads(r.recognize_vosk(audio, 'en'))['text']

    return text

def wait_for_speaking():
    return pygame.mixer.music.get_busy() == True

def wait_for_interrupt():
    text = ""

    try:
        text = listen()
        print('>>> ' + text)
    except sr.UnknownValueError:
        pass

    if text.lower() in config_stopword:
        pygame.mixer.music.stop()
        play_sound('accepted')
        print("- interrupted...")
        return 1

    return 0

def wait_for_wakeup():
    print("- listening for keyword...")

    while True:
        text = ""

        try:
            text = listen()
            print('>>> ' + text)
        except sr.UnknownValueError:
            pass

        if text.lower() in config_wakeword:
            play_sound('wakeup')
            print("- waking up")
            wait_for_query()

def wait_for_query():
    print("- listening for query...")

    while True:
        text = ""

        try:
            text = listen()
            print('>>> ' + text)

        except sr.UnknownValueError as e:
            play_sound('error')
            print("- back to sleep...")
            # listen_for_wake_word()
            break

        if not text:
            continue

        if text.lower() in config_sleepword:
            play_sound('accepted')
            print("- back to sleep...")
            # listen_for_wake_word()
            break

        play_sound('processing')
        print("request: " + text)

        wrapped_text = "in as few words as possible, " + text

        try:
            response = openai.ChatCompletion.create(model=model_name, messages=[{"role": "user", "content": wrapped_text}])
            response_text = response.choices[0].message.content
        except openai.error.RateLimitError as e:
            play_sound('error')
            print("!!! openai exception: " + e.user_message)
            text_to_voice("open ai exception: " + e.user_message)
            print("- back to sleep...")
            # listen_for_wake_word()
            break

        if text and response_text:
            print("chatgpt response: " + response_text)
            text_to_voice(response_text)

def main():
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
