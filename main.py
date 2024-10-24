#print("started")

#imports
import sys
import pygame
import time
#import pygame._sdl2.touch
from pygame.locals import QUIT

#Initialzing pygame and mixer
pygame.mixer.pre_init(frequency=48000, buffer=2048)
pygame.init()
pygame.mixer.init()

#defineing colors
WHITE = (255, 255, 255)

#seting up screen
resolutionMultiplyer = 3
SCREEN_WIDTH = 1080 * resolutionMultiplyer
SCREEN_HEIGHT = 720 * resolutionMultiplyer
DISPLAYSURF = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), (pygame.FULLSCREEN | pygame.SCALED)) # | pygame.NOFRAME  pygame.RESIZABLE
pygame.display.set_caption('DCS Alarm Panel')
#DISPLAYSURF.fill(WHITE)

#seting up mixer
pygame.mixer.music.set_volume(1.00)
if False: #True for original alarms,  #False for "corected" alarms
    DCSAlarm = pygame.mixer.Sound("sound/DCSAlarm.wav")
    GeneralAlarm = pygame.mixer.Sound("sound/GeneralAlarm.wav")
    HalifaxActionAlarm = pygame.mixer.Sound("sound/HalifaxActionAlarm.wav")
else:
    HalifaxActionAlarm = pygame.mixer.Sound("sound/DCSAlarm.wav")
    DCSAlarm = pygame.mixer.Sound("sound/GeneralAlarm.wav")
    GeneralAlarm = pygame.mixer.Sound("sound/HalifaxActionAlarm.wav")
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
"toggleNightMode" : pygame.image.load("images/ToggleDayMode.png").convert_alpha(),
"toggleDayMode" : pygame.image.load("images/ToggleNightMode.png").convert_alpha(),
}

#Setting up FPS
FPS = 60
FramePerSec = pygame.time.Clock()
alarmTimeFPS = 5
alarmTimeCounter = 0
displayFPSInfo = True

Alarm = None
AlarmTime = 6 #Mins
ResetNext = False

nightMode = False

nextFix = time.localtime().tm_min + AlarmTime-1 + (round(time.localtime().tm_sec/60))
timeUntilNextFix = (60 - time.localtime().tm_min + nextFix) % 60 #(nextFix - time.localtime().tm_min) % 60
fixesAlarmMuted = True
       
scenes = { "default" : [], "acknowledge" : []}
scene = "default"
nextScene = "default"

FINGERdown = False

#
myfont = pygame.font.SysFont('Arial', 50)

class TextPrint:
    def __init__(self):
        self.reset()
        self.font1 = pygame.font.Font(None, 90 * resolutionMultiplyer)

    def tprint(self, screen, text, moveDown = False):
        text_bitmap = self.font1.render(text, True, (0, 0, 0))
        screen.blit(text_bitmap, (self.x, self.y))
        if moveDown:
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

#define functions
def QUITfunc(): # runs when "Quit" button is pressed
    #ends program
    pygame.quit()
    sys.exit()

def toggleNightMode():
    global nightMode
    nightMode = not nightMode
    if nightMode:
        toggleNightModeButton.image1 = pygame.transform.scale((image["toggleNightMode"]),(toggleNightModeButton.width, toggleNightModeButton.height))
        toggleNightModeButton.image2 = pygame.transform.scale((image["toggleNightMode"]),(toggleNightModeButton.width, toggleNightModeButton.height))
    else:
        toggleNightModeButton.image1 = pygame.transform.scale((image["toggleDayMode"]),(toggleNightModeButton.width, toggleNightModeButton.height))
        toggleNightModeButton.image2 = pygame.transform.scale((image["toggleDayMode"]),(toggleNightModeButton.width, toggleNightModeButton.height))

def DCSAlarmFunc(): # runs when corresponding button is pressed
  DCSAlarm.play(loops = 8, fade_ms = 100)
  global Alarm
  Alarm = DCSAlarm
  global nextScene
  nextScene = "acknowledge"
  setAlreadyPressed()
def GeneralAlarmFunc(): # runs when corresponding button is pressed
  GeneralAlarm.play(loops = 8, fade_ms = 100)
  global Alarm
  Alarm = GeneralAlarm
  global nextScene
  nextScene = "acknowledge"
  setAlreadyPressed()
def HalifaxActionAlarmFunc(): # runs when corresponding button is pressed
  HalifaxActionAlarm.play(loops = 8, fade_ms = 100)
  global Alarm
  Alarm = HalifaxActionAlarm
  global nextScene
  nextScene = "acknowledge"
  setAlreadyPressed()

def stopAlarm():
  global Alarm
  Alarm.stop() # stops audio
  Alarm = None
  global nextScene
  nextScene = "default"
  setAlreadyPressed()

def resetFixesAlarm(): # runs when the fixes timer button is pressed
     global nextFix
     nextFix = (time.localtime().tm_min + max(AlarmTime-1,0) + (round((time.localtime().tm_sec+2)/60))) % 60

def checkFixesAlarm(): # runs each frame
    global nextFix
    global timeUntilNextFix
    global ResetNext
    mins = time.localtime().tm_min
    if timeUntilNextFix == 0 and time.localtime().tm_sec == 59:
        ResetNext = True
    elif ResetNext and time.localtime().tm_sec == 0: #checks if timer needs to be reset
        ResetNext = False
        nextFix = (mins + max(AlarmTime - 1, 0)) % 60
        if fixesAlarmMuted == False:
            Notify.play(loops = 1, fade_ms = 0)
    elif timeUntilNextFix > AlarmTime:
        resetFixesAlarm()
    timeUntilNextFix = ((60 - mins) + nextFix) % 60  # Calculate timeUntilNextFix


def toggleFixesAlarmMute(): # runs when mute button is pressed
    global fixesAlarmMuted
    fixesAlarmMuted = not fixesAlarmMuted
    if fixesAlarmMuted:
        FixsMuteButton.image1 = pygame.transform.scale((image["muted"]),(FixsMuteButton.width, FixsMuteButton.height))
        FixsMuteButton.image2 = pygame.transform.scale((image["muted"]),(FixsMuteButton.width, FixsMuteButton.height))
    else:
        FixsMuteButton.image1 = pygame.transform.scale((image["unmuted"]),(FixsMuteButton.width, FixsMuteButton.height))
        FixsMuteButton.image2 = pygame.transform.scale((image["unmuted"]),(FixsMuteButton.width, FixsMuteButton.height))

def setAlreadyPressed(): # used to prevent double activations on one click
    Acknowledge.alreadyPressed = True
    DCSAlarmButton.alreadyPressed = True
    GeneralAlarmButton.alreadyPressed = True
    HalifaxActionAlarmButton.alreadyPressed = True
    resetFixTimeButton.alreadyPressed = True

#create button objects
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

#toggleNightModeButton = button([scenes["default"], scenes["acknowledge"]], (SCREEN_WIDTH-30-150)*resolutionMultiplyer, (SCREEN_HEIGHT-30-150)*resolutionMultiplyer, 100*resolutionMultiplyer, 100*resolutionMultiplyer, image["toggleDayMode"], image["toggleDayMode"], toggleNightMode)
toggleNightModeButton = button([scenes["default"], scenes["acknowledge"]], (1080-190)*resolutionMultiplyer, (720-170)*resolutionMultiplyer, 150*resolutionMultiplyer, 150*resolutionMultiplyer, image["toggleDayMode"], image["toggleDayMode"], toggleNightMode)

pygame.event.set_allowed((pygame.QUIT, pygame.WINDOWFOCUSGAINED, pygame.WINDOWFOCUSLOST))#control which events are allowed on the queue

#setup TPrint stuff
fixesAlarmPrinter = TextPrint()
fixesAlarmPrinter.reset()
FPSPrinter = TextPrint()
FPSPrinter.reset()
FPSPrinter.font1 = pygame.font.Font(None, 20 * resolutionMultiplyer)
FPSPrinter.x = 10 * resolutionMultiplyer
FPSPrinter.y = 10 * resolutionMultiplyer
#FPSPrinter.line_height = 80 * resolutionMultiplyer

print("starting loop")

while True: # main controll loop
    for event in pygame.event.get():
        if event.type == QUIT: # if program exited then end program
            QUITfunc()
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            QUITfunc()
        elif event.type == pygame.WINDOWFOCUSGAINED:
            FPS = 60
        elif event.type == pygame.WINDOWFOCUSLOST:
            FPS = 2
        elif event.type == pygame.WINDOWCLOSE:
            #print("WINDOWCLOSE event dected - quiting...")
            QUITfunc()
        elif event.type == pygame.MOUSEBUTTONDOWN:
            #displayFPSInfo ^= 1
            displayFPSInfo = not event.touch

    if nightMode:
        DISPLAYSURF.fill("#202525") # set background colour
    else:
        DISPLAYSURF.fill("#d0d0d0") # set background colour

    scene = nextScene

    #renders all the buttons
    for object in scenes[scene]:
        object.process(None)

    #updates fixes alarm time values every few frames
    if alarmTimeCounter >= FPS / alarmTimeFPS:
        alarmTimeCounter = 0
        checkFixesAlarm()
    else:
        alarmTimeCounter += 1
    #render fixes alarm time
    seconds = 60 - time.localtime().tm_sec -1
    if seconds <= 9:
        fixesAlarmPrinter.tprint(DISPLAYSURF, F"{timeUntilNextFix} : 0{seconds}")
    else:
        fixesAlarmPrinter.tprint(DISPLAYSURF, F"{timeUntilNextFix} : {seconds}")

    #if timeUntilNextFix > AlarmTime:
    #    print( F"ERROR: timeUntilNextFix:{timeUntilNextFix} : {seconds}   @ time: {time.localtime().tm_min}:{time.localtime().tm_sec}   nextFix: {nextFix}")

    #print("running!")
   
    if displayFPSInfo:
        FPSPrinter.tprint(DISPLAYSURF, F"FPS: {round(FramePerSec.get_fps(),1)} ")
        FPSPrinter.tprint(DISPLAYSURF, F"                     mspt:{FramePerSec.get_time()} ")

    #render frame at the right time
    pygame.display.update()
    FramePerSec.tick(FPS)