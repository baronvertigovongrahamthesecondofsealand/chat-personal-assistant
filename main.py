#!/usr/bin/python3

config_wakeword = ["hey computer", "a computer", "say computer"]
config_sleepword = ["never mind", "nevermind", "disregard"]

import os
import sys
import time
import json

import openai
openai.organization = os.getenv("OPEN_API_ORG")
openai.api_key = os.getenv('OPENAI_API_KEY')
#model_name = "gpt-3.5-turbo"
model_name = "babbage"

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

def text_to_voice_gtts(text):
    mp3_buffer = BytesIO()
    tts = gTTS(text)
    tts.write_to_fp(mp3_buffer)
    mp3_buffer.seek(0)

    pygame.mixer.music.load(mp3_buffer)
    pygame.mixer.music.play()

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

def listen_for_wake_word():
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
            listen_and_respond()
            break

        if text.lower() in config_sleepword:
            play_sound('accepted')
            print("- back to sleep...")
            listen_for_wake_word()
            break

def listen_and_respond():
    print("- listening for statement...")

    while True:
        text = ""

        try:
            text = listen()
            print('>>> ' + text)

        except sr.UnknownValueError as e:
            play_sound('error')
            print("- back to sleep...")
            listen_for_wake_word()
            break

        if not text:
            continue

        if text.lower() in config_sleepword:
            play_sound('accepted')
            print("- back to sleep...")
            listen_for_wake_word()
            break

        play_sound('processing')
        print("request: " + text)

        try:
            response = openai.ChatCompletion.create(model=model_name, messages=[{"role": "user", "content": text}])
            response_text = response.choices[0].message.content
        except openai.error.RateLimitError as e:
            play_sound('error')
            print("!!! openai exception: " + e.user_message)
            text_to_voice("open ai exception: " + e.user_message)
            listen_for_wake_word()
            break

        if not text:
            continue

        print("chatgpt response: " + response_text)

        text_to_voice(response_text)

        time.sleep(2)
        listen_for_wake_word()

def main():
    listen_for_wake_word()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        try:
            sys.exit(130)
        except SystemExit:
            os._exit(130)
