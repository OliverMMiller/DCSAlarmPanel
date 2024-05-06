#imports
import sys
import pygame
import time
import pygame._sdl2.touch
from pygame.locals import QUIT

#Initialzing pygame and mixer
pygame.init()
pygame.mixer.init()

#defineing colors
WHITE = (255, 255, 255)

#seting up screen
resolutionMultiplyer = 5
SCREEN_WIDTH = 1080 * resolutionMultiplyer
SCREEN_HEIGHT = 720 * resolutionMultiplyer
DISPLAYSURF = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), (pygame.FULLSCREEN | pygame.SCALED | pygame.RESIZABLE))
pygame.display.set_caption('DCS Alarm Panel')
DISPLAYSURF.fill(WHITE)

#seting up mixer
pygame.mixer.music.set_volume(1.00)
DCSAlarm = pygame.mixer.Sound("sound/DCSAlarm.wav")
GeneralAlarm = pygame.mixer.Sound("sound/GeneralAlarm.wav")
HalifaxActionAlarm = pygame.mixer.Sound("sound/HalifaxActionAlarm.wav")
Notify = pygame.mixer.Sound("sound/Notify.wav")
Notify.set_volume(0.08)

#images
image = {
"quit" :        pygame.image.load("images/Quit.png").convert_alpha(),
"Blankblue" :   pygame.image.load("images/Blank-Blue.png").convert_alpha(),
"DCSred" :      pygame.image.load("images/DCS-red.png").convert_alpha(),
"DCSgray" :     pygame.image.load("images/DCS-Gray.png").convert_alpha(),
"generalred" :  pygame.image.load("images/General-red.png").convert_alpha(),
"generalgray" : pygame.image.load("images/General-Gray.png").convert_alpha(),
"actionred" :   pygame.image.load("images/Action-red.png").convert_alpha(),
"actiongray" :  pygame.image.load("images/Action-Gray.png").convert_alpha(),
"Acknowledge" : pygame.image.load("images/Acknowledge.png").convert_alpha(),
"muted" : pygame.image.load("images/Muted.png").convert_alpha(),
"unmuted" : pygame.image.load("images/Unmuted.png").convert_alpha(),
}

#Setting up FPS
FPS = 60
FramePerSec = pygame.time.Clock()

Alarm = None
AlarmTime = 6#Mins

nextFix = time.localtime().tm_min + AlarmTime-1 + (round(time.localtime().tm_sec/60))
timeUntilNextFix = (60 - time.localtime().tm_min + nextFix) % 60 #(nextFix - time.localtime().tm_min) % 60
#timeOfNextFix = nextFix % 60
fixesAlarmMuted = True
        
scenes = { "default" : [], "acknowledge" : []}
scene = "default"
nextScene = "default"

FINGERdown = False

#
font = pygame.font.SysFont('Arial', 50)

class TextPrint:
    def __init__(self):
        self.reset()
        self.font = pygame.font.Font(None, 90 * resolutionMultiplyer)

    def tprint(self, screen, text):
        text_bitmap = self.font.render(text, True, (0, 0, 0))
        screen.blit(text_bitmap, (self.x, self.y))
        self.y += self.line_height

    def reset(self):
        self.x = 50 * resolutionMultiplyer
        self.y = 50 * resolutionMultiplyer
        self.line_height = 80 * resolutionMultiplyer

class button():
    def __init__(self, parentScenes, x, y, width, height, image1, image2, onclickFunction=None, onePress=False):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.onclickFunction = onclickFunction
        self.onePress = onePress

        self.image1 = pygame.transform.scale((image1),(self.width, self.height))
        self.image2 = pygame.transform.scale((image2),(self.width, self.height))
        self.buttonRect = self.image1.get_rect()
        self.buttonRect.update((self.x, self.y),(self.width, self.height))

        self.alreadyPressed = False

        for num in range(len(parentScenes)):
            parentScenes[num].insert(0,self)

    def process(self, mousePos):

        if mousePos == None:
            mousePos = pygame.mouse.get_pos()
    
        if self.buttonRect.collidepoint(mousePos) and pygame.mouse.get_pressed(num_buttons=3)[0] or FINGERdown == True:
            if self.onePress:
                self.onclickFunction()
            elif not self.alreadyPressed:
                self.onclickFunction()
                self.alreadyPressed = True

            DISPLAYSURF.blit(self.image1, self.buttonRect)

        else:
            self.alreadyPressed = False
            DISPLAYSURF.blit(self.image2, self.buttonRect)

#
def QUITfunc():
    pygame.quit()
    sys.exit()

def DCSAlarmFunc():
  DCSAlarm.play(loops = 8, fade_ms = 100)
  global Alarm
  Alarm = DCSAlarm
  global nextScene
  nextScene = "acknowledge"
  setAlreadyPressed()
def GeneralAlarmFunc():
  GeneralAlarm.play(loops = 8, fade_ms = 100)
  global Alarm
  Alarm = GeneralAlarm
  global nextScene
  nextScene = "acknowledge"
  setAlreadyPressed()
def HalifaxActionAlarmFunc():
  HalifaxActionAlarm.play(loops = 8, fade_ms = 100)
  global Alarm
  Alarm = HalifaxActionAlarm
  global nextScene
  nextScene = "acknowledge"
  setAlreadyPressed()

def stopAlarm():
  global Alarm
  Alarm.stop()
  Alarm = None
  global nextScene
  nextScene = "default"
  setAlreadyPressed()

def resetFixesAlarm():
     #time.localtime().tm_min
     global nextFix
     nextFix = (time.localtime().tm_min + max(AlarmTime-1,0) + (round((time.localtime().tm_sec+2)/60))) % 60

def checkFixesAlarm():
    global nextFix
    global timeUntilNextFix
    #global timeOfNextFix
    mins = time.localtime().tm_min
    if (nextFix - mins < 0) :
        nextFix = (mins + max(AlarmTime - 1, 0)) % 60
        #timeOfNextFix = nextFix % 60
        if fixesAlarmMuted == False:
            Notify.play(loops = 1, fade_ms = 0)
    timeUntilNextFix = ((60 - mins) + nextFix) % 60  # Calculate timeUntilNextFix

def toggleFixesAlarmMute():
    global fixesAlarmMuted
    fixesAlarmMuted = not fixesAlarmMuted
    if fixesAlarmMuted:
        FixsMuteButton.image1 = image["muted"]
        FixsMuteButton.image2 = image["muted"]
    else:
        FixsMuteButton.image1 = image["unmuted"]
        FixsMuteButton.image2 = image["unmuted"]

def setAlreadyPressed():
    Acknowledge.alreadyPressed = True
    DCSAlarmButton.alreadyPressed = True
    GeneralAlarmButton.alreadyPressed = True
    HalifaxActionAlarmButton.alreadyPressed = True
    resetFixTimeButton.alreadyPressed = True

alarmButtonWidth = (SCREEN_WIDTH/3 - 2*30)
alarmButtonY = SCREEN_HEIGHT/2 - alarmButtonWidth/2

QUITbutton = button([scenes["default"], scenes["acknowledge"]], SCREEN_WIDTH - 230*resolutionMultiplyer, 30*resolutionMultiplyer, 200*resolutionMultiplyer, 100*resolutionMultiplyer, image["quit"], image["quit"], QUITfunc)

resetFixTimeButton = button([scenes["default"], scenes["acknowledge"]], 30*resolutionMultiplyer, 30*resolutionMultiplyer, 200*resolutionMultiplyer, 100*resolutionMultiplyer, image["Blankblue"], image["Blankblue"], resetFixesAlarm)
FixsMuteButton = button([scenes["default"], scenes["acknowledge"]], (200+30+30)*resolutionMultiplyer, 30*resolutionMultiplyer, 100*resolutionMultiplyer, 100*resolutionMultiplyer, image["muted"], image["muted"], toggleFixesAlarmMute)

DCSAlarmButton = button([scenes["default"]], 30*2, alarmButtonY, alarmButtonWidth, alarmButtonWidth, image["DCSred"], image["DCSgray"], DCSAlarmFunc)
GeneralAlarmButton = button([scenes["default"]], 30*3 + alarmButtonWidth, alarmButtonY, alarmButtonWidth, alarmButtonWidth, image["generalred"], image["generalgray"], GeneralAlarmFunc)
HalifaxActionAlarmButton = button([scenes["default"]], 30*4 + alarmButtonWidth*2, alarmButtonY, alarmButtonWidth, alarmButtonWidth, image["actionred"], image["actiongray"], HalifaxActionAlarmFunc)

Acksize = (60*1.7*resolutionMultiplyer, 80*1.7*resolutionMultiplyer)
Acknowledge = button([scenes["acknowledge"]], Acksize[0], Acksize[1], SCREEN_WIDTH-(Acksize[0]*2), SCREEN_HEIGHT-(Acksize[1]*2), image["Acknowledge"], image["Acknowledge"], stopAlarm)
setAlreadyPressed()

pygame.event.set_allowed(QUIT,)#control which events are allowed on the queue

while True:
    for event in pygame.event.get():
        if event.type == QUIT:
            pygame.quit()
            sys.exit()

    DISPLAYSURF.fill("#d0d0d0")
    TextPrint().reset()

    scene = nextScene

    #renders all the buttons
    for object in scenes[scene]:
        object.process(None)

    #fixes timer
    checkFixesAlarm()
    seconds = 60 - time.localtime().tm_sec -1
    if seconds <= 9:
        TextPrint().tprint(DISPLAYSURF, F"{timeUntilNextFix} : 0{seconds}")
    else:
        TextPrint().tprint(DISPLAYSURF, F"{timeUntilNextFix} : {seconds}")

    #render frame at the right time
    pygame.display.update()
    FramePerSec.tick(FPS)
