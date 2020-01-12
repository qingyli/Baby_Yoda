import pygame
import threading
import paho.mqtt.client as mqtt
import pickle
import RPi.GPIO as GPIO
import time
from datetime import date
import schedule
# GCP credentials
from google.oauth2 import service_account

# Setup
credentials = service_account.Credentials.from_service_account_file('/home/pi/baby-yoda/gcp.json')
pygame.init()
voice_input = ''
GPIO.setmode(GPIO.BCM)
servo_h = 17
servo_l = 23
servo_r = 5

GPIO.setup(servo_h, GPIO.OUT)
h = GPIO.PWM(servo_h, 100)

GPIO.setup(servo_r, GPIO.OUT)
r = GPIO.PWM(servo_r, 50)
r.start(2.5)
GPIO.setup(servo_l, GPIO.OUT)
l = GPIO.PWM(servo_l, 50)
l.start(2.5)

ind = 0
day = 99
mon = 99
year = 99

''' IMPORT SCHEDULE DATABASE '''

DB_FILE = 'schedule.txt'
database = {}

try:
    with open(DB_FILE, 'rb') as file:
        print('Loading {}'.format(DB_FILE))
        #database = pickle.load(file)
except FileNotFoundError:
    pass



''' DATABASE FUNCTION '''

def update_database(db):
    with open(DB_FILE, 'wb') as file:
        pickle.dump(db, file, pickle.HIGHEST_PROTOCOL)
    pass


''' SPEAKER SECTION '''
def speak(text):
    """Synthesizes speech from the input string of text."""
    from google.cloud import texttospeech
    client = texttospeech.TextToSpeechClient(credentials=credentials)

    input_text = texttospeech.types.SynthesisInput(text=text)

    # Note: the voice can also be specified by name.
    # Names of voices can be retrieved with client.list_voices().
    voice = texttospeech.types.VoiceSelectionParams(
        language_code='en-US',
        ssml_gender=texttospeech.enums.SsmlVoiceGender.FEMALE)

    audio_config = texttospeech.types.AudioConfig(
        audio_encoding=texttospeech.enums.AudioEncoding.MP3)

    response = client.synthesize_speech(input_text, voice, audio_config)

    # The response's audio_content is binary.
    with open('output.mp3', 'wb') as out:
        out.write(response.audio_content)
        pygame.mixer.music.load("output.mp3")
        pygame.mixer.music.play()


''' LISTENER SECTION '''    
def get_voice_input(client, userdata, message):
    global ind
    global mon
    global day
    global year
    # Voice string receives from microphone
    voice_input = str(message.payload, "utf-8").lower().strip()
    print(voice_input)
    # Voice input handler
    # TODO
    if (voice_input in ["hey baby yoda", "hi baby yoda", "hello baby yoda","hey baby yoga", "hi baby yoga", "hello baby yoga"]):
        speak("Hi, how can I help you ?")
        h.start(2.5)
        h.ChangeDutyCycle(10)
        time.sleep(2)
        h.stop()
        
    if (voice_input in ["what's my homework today"]):
        today = date.today()
        #print(today.strftime("%m/%d/%y"))
        file_ = open(DB_FILE, 'r')
        for line in file_:
           if today.strftime("%m/%d/%y") in line:
                speak(line)
                print(line)
                time.sleep(1)
                
    
    while (voice_input in ["add a new task on my schedule"]) or ind > 0:    
        if ind == 0:
            ind = 1
            print("1")
            speak("what is the date?")
            time.sleep(2)
            break
        
        if ind == 1:
            day = voice_input
            dy = int(day)
            ind = 2
            print("2")
            if dy > 31 and dy < 1:
                ind = 1
                speak("invalid date, please say it again")
            else:
                speak("what is the month")
            time.sleep(2)
            break
        if ind == 2:
            mon = voice_input
            ind = 3
            print("3")
            if (int(mon) > 12) and (int(mon) < 1):
                ind = 2
                speak("invalid month, please say it again")
            else:
                speak("what is the year? state the last two number")
            time.sleep(2)
            break
        if ind == 3:
            year = voice_input
            ind = 4
            print("4")
            if int(year) > 100:
                ind = 3
                speak("invalid year, please say it again")
            else:
                speak("what is the subject")
            time.sleep(2)
            break
        if ind == 4:
            inp = open(DB_FILE, 'a')
            sub = voice_input
            #print(sub)
            pri = '\n' + str(mon) + '/' + str(day) + '/' + str(year) + '   ' + sub
            inp.write(pri)
            print(pri)
            ind = 0
            break
        
    if (voice_input in ["quit", "exit"]):
        speak("bye bye")
        GPIO.cleanup()
    #print(voice_input)
    
def on_connect(client, userdata, flags, rc):
    print("Connect to mqtt server")
    client.subscribe("qingyuanli/voice_input")
    client.message_callback_add("qingyuanli/voice_input", get_voice_input)
    
def listener_main():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.connect(host="eclipse.usc.edu", port=11000, keepalive=60)
    client.loop_start()
    pass

''' ACTION SECTION '''

# TODOS
def action_main():
    while True:
        pass
    pass


''' THREAD SECTION '''
if __name__ == '__main__':
    listener_thread = threading.Thread(target=listener_main, args=[])
    #action_thread = threading.Thread(target=action_main, args=[])

    listener_thread.start()
    #action_thread.start()