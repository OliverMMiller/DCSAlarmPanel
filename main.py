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
}

#Setting up FPS
FPS = 60
FramePerSec = pygame.time.Clock()

Alarm = None

nextFix = (time.localtime().tm_min + 6)
timeUntilNextFix = nextFix - time.localtime().tm_min % 60
timeOfNextFix = nextFix % 60
        
scenes = { "default" : [], "acknowledge" : []}
scene = "default"
nextScene = "default"

FINGERdown = False

#
font = pygame.font.SysFont('Arial', 50)

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

        self.image1 = self.image1.convert_alpha()
        self.image2 = self.image2.convert_alpha()

        #self.buttonSurface1 = pygame.Surface((self.width, self.height))
        #self.buttonSurface2 = pygame.Surface((self.width, self.height))

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
     nextFix = time.localtime().tm_min + 6 + (round(time.localtime().tm_sec/60))

def checkFixesAlarm():
    global nextFix
    global timeUntilNextFix
    global timeOfNextFix
    timeUntilNextFix = nextFix - time.localtime().tm_min % 60
    if timeUntilNextFix <= 0:
        nextFix = (time.localtime().tm_min + 6) % 60
        timeOfNextFix = nextFix % 60
        Notify.play(loops = 1, fade_ms = 0)
    else:
        timeUntilNextFix = (nextFix - time.localtime().tm_min) % 60

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
#        elif event.type == pygame.MOUSEBUTTONUP:     #pos, button, touch
#            MOUSEBUTTONDOWN = False
#        elif event.type == pygame.MOUSEBUTTONDOWN:   #pos, button, touch
#            mousePos = event.pos
#            MOUSEBUTTONDOWN = True
#        elif event.type == pygame.FINGERDOWN: #touch_id, finger_id, x, y, dx, dy
#            mousePos = (event.x, event.y)
#            FINGERdown = True
#        elif event.type == pygame.FINGERUP:  #touch_id, finger_id, x, y, dx, dy
#           FINGERdown = False
    DISPLAYSURF.fill("#d0d0d0")

    scene = nextScene

    for object in scenes[scene]:
        object.process(None)

    checkFixesAlarm()
    print(F"{timeUntilNextFix} : {60 - time.localtime().tm_sec}")

    pygame.display.update()
    FramePerSec.tick(FPS)
