#imports
import sys
import pygame
#import time
import pygame._sdl2.touch
from pygame.locals import QUIT

#Initialzing pygame and mixer
pygame.init()
pygame.mixer.init()

#defineing colors
WHITE = (255, 255, 255)

#seting up screen
SCREEN_WIDTH = 1080
SCREEN_HEIGHT = 720
DISPLAYSURF = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), (pygame.FULLSCREEN | pygame.SCALED | pygame.RESIZABLE))
pygame.display.set_caption('DCS Alarm Panel')
DISPLAYSURF.fill(WHITE)

#seting up mixer
pygame.mixer.music.set_volume(1.00)
DCSAlarm = pygame.mixer.Sound("sound/DCSAlarm.wav")
GeneralAlarm = pygame.mixer.Sound("sound/GeneralAlarm.wav")
HalifaxActionAlarm = pygame.mixer.Sound("sound/HalifaxActionAlarm.wav")

#images
image = {
"quit" :        pygame.image.load("images/Quit.png"),
"DCSred" :      pygame.image.load("images/DCS-red.png"),
"DCSgray" :     pygame.image.load("images/DCS-Gray.png"),
"generalred" :  pygame.image.load("images/General-red.png"),
"generalgray" : pygame.image.load("images/General-Gray.png"),
"actionred" :   pygame.image.load("images/Action-red.png"),
"actiongray" :  pygame.image.load("images/Action-Gray.png"),
"Acknowledge" : pygame.image.load("images/Acknowledge.png"),
}

#Setting up FPS
FPS = 30
FramePerSec = pygame.time.Clock()

class Alarm():
    def __init__(self):
        self.Alarm = False
Alarms = Alarm()
FINGERdown = False

#
font = pygame.font.SysFont('Arial', 50)

objects = []

class button():
    def __init__(self, x, y, width, height, image1, image2, onclickFunction=None, onePress=False):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.onclickFunction = onclickFunction
        self.onePress = onePress

        self.image1 = pygame.transform.scale((image1),(self.width, self.height))
        self.image2 = pygame.transform.scale((image2),(self.width, self.height))
        self.buttonRect = self.image1.get_rect()
        self.buttonRect.update((x, y),(self.width, self.height))

        self.image1 = self.image1.convert_alpha()
        self.image2 = self.image2.convert_alpha()

        #self.buttonSurface1 = pygame.Surface((self.width, self.height))
        #self.buttonSurface2 = pygame.Surface((self.width, self.height))

        self.alreadyPressed = False

        objects.append(self)

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

        #self.buttonSurface.blit(self.buttonSurface, [
        #    self.buttonRect.width/2 - self.buttonSurface.get_rect().width/2,
        #    self.buttonRect.height/2 - self.buttonSurface.get_rect().height/2
        #])
        #DISPLAYSURF.blit(self.buttonSurface, self.buttonRect)
#
def QUITfunc():
    pygame.quit()
    sys.exit()

def DCSAlarmFunc():
  DCSAlarm.play(loops = 8, fade_ms = 100)
  Alarms.Alarm = True
def GeneralAlarmFunc():
  GeneralAlarm.play(loops = 8, fade_ms = 100)
  Alarms.Alarm = True
def HalifaxActionAlarmFunc():
  HalifaxActionAlarm.play(loops = 8, fade_ms = 100)
  Alarms.Alarm = True

def stopAlarm():
  Alarms.Alarm = False
  DCSAlarm.stop()
  GeneralAlarm.stop()
  HalifaxActionAlarm.stop()

alarmButtonWidth = (SCREEN_WIDTH/3 - 2*30)
alarmButtonY = SCREEN_HEIGHT/2 - alarmButtonWidth/2

QUITbutton = button(SCREEN_WIDTH - 230, 30, 200, 100, image["quit"], image["quit"], QUITfunc)

DCSAlarmButton = button(30*2, alarmButtonY, alarmButtonWidth, alarmButtonWidth, image["DCSred"], image["DCSgray"], DCSAlarmFunc)
GeneralAlarmButton = button(30*3 + alarmButtonWidth, alarmButtonY, alarmButtonWidth, alarmButtonWidth, image["generalred"], image["generalgray"], GeneralAlarmFunc)
HalifaxActionAlarmButton = button(30*4 + alarmButtonWidth*2, alarmButtonY, alarmButtonWidth, alarmButtonWidth, image["actionred"], image["actiongray"], HalifaxActionAlarmFunc)

Acksize = (60, 80)
Acknowledge = button(Acksize[0], Acksize[1], SCREEN_WIDTH-(Acksize[0]*2), SCREEN_HEIGHT-(Acksize[1]*2), image["Acknowledge"], image["Acknowledge"], stopAlarm)
objects.pop(-1)
Acknowledge.alreadyPressed = True

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
    if Alarms.Alarm == True:
        Acknowledge.process(None)
        QUITbutton.process(None)
    else:
        for object in objects:
          object.process(None)

    pygame.display.update()
    FramePerSec.tick(FPS)
