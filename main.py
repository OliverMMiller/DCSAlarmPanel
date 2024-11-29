#imports
import sys
import pygame
import time
from pygame.locals import QUIT

from OliversButtonModuleV2 import button as button

#initializing pygame and mixer
pygame.mixer.pre_init(frequency=48000, buffer=2048)
pygame.init()
pygame.mixer.init()

#defining colors
WHITE = (255, 255, 255)

#setting up screen
resolutionMultiplier = 3
SCREEN_WIDTH = 1080 * resolutionMultiplier
SCREEN_HEIGHT = 720 * resolutionMultiplier
DISPLAYSURF = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), (pygame.FULLSCREEN | pygame.SCALED)) # | pygame.NOFRAME  pygame.RESIZABLE
pygame.display.set_caption('DCS Alarm Panel')
#DISPLAYSURF.fill(WHITE)

#setting up mixer
pygame.mixer.music.set_volume(1.00)

# original alarms:
# DCSAlarm = pygame.mixer.Sound("sound/DCSAlarm.wav")
# GeneralAlarm = pygame.mixer.Sound("sound/GeneralAlarm.wav")
# HalifaxActionAlarm = pygame.mixer.Sound("sound/HalifaxActionAlarm.wav")

# "corrected" alarms:
HalifaxActionAlarm = pygame.mixer.Sound("sound/DCSAlarm.wav")
DCSAlarm = pygame.mixer.Sound("sound/GeneralAlarm.wav")
GeneralAlarm = pygame.mixer.Sound("sound/HalifaxActionAlarm.wav")

Notify = pygame.mixer.Sound("sound/Notify.wav")
Notify.set_volume(0.5)

#images
image = {
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

currentAlarm = None
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
myFont = pygame.font.SysFont('Arial', 50)

class TextPrint:
    def __init__(self):
        self.reset()
        self.font1 = pygame.font.Font(None, 90 * resolutionMultiplier)

    def tprint(self, screen, text, moveDown = False) -> None:
        text_bitmap = self.font1.render(text, True, (0, 0, 0))
        screen.blit(text_bitmap, (self.x, self.y))
        if moveDown:
            self.y += self.line_height

    def reset(self) -> None:
        self.x = 50 * resolutionMultiplier
        self.y = 50 * resolutionMultiplier
        self.line_height = 80 * resolutionMultiplier

class alarmObj():
    def __init__(self, alarmButton: button, alarmSound: pygame.mixer.Sound) -> None:
        self.alarmButton = alarmButton
        self.alarmSound = alarmSound
        
    def playAlarm(self) -> None:
        global currentAlarm
        if currentAlarm == None:
            self.alarmSound.play(loops = 5, fade_ms = 100)
            global nextScene
            currentAlarm = self
            nextScene = "acknowledge"
            self.alarmButton.alreadyPressed = True   
        
def stopAlarm() -> None:
    global currentAlarm
    if currentAlarm:
        currentAlarm.alarmSound.stop() # stops audio
        currentAlarm = None
        global nextScene
        nextScene = "default"
        setIgnoreNextPress()


currentAlarm: alarmObj | None
# need to partly define alarm objects before defining buttons
DCSAlarmObj = alarmObj(None, DCSAlarm)
GeneralAlarmObj = alarmObj(None, GeneralAlarm)
HalifaxActionAlarmObj = alarmObj(None, HalifaxActionAlarm)

#define functions
def quitFunc() -> None: # runs when "Quit" button is pressed
    #ends program
    pygame.quit()
    sys.exit()

def toggleNightMode() -> None:
    global nightMode
    if nightMode := not nightMode:
        toggleNightModeButton.updateImages(image["toggleNightMode"])
    else:
        toggleNightModeButton.updateImages(image["toggleDayMode"])

def resetFixesAlarm() -> None: # runs when the fixes timer button is pressed
     global nextFix
     nextFix = (time.localtime().tm_min + max(AlarmTime-1,0) + (round((time.localtime().tm_sec+2)/60))) % 60

def checkFixesAlarm() -> None: # runs each frame
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


def toggleFixesAlarmMute() -> None: # runs when mute button is pressed
    global fixesAlarmMuted
    if fixesAlarmMuted := not fixesAlarmMuted:
        fixesMuteButton.updateImages(image["muted"])
    else:
        fixesMuteButton.updateImages(image["unmuted"])


def setIgnoreNextPress() -> None: # used to prevent double activations on one click
    Acknowledge.ignoreNextPress = True
    DCSAlarmButton.ignoreNextPress = True
    GeneralAlarmButton.ignoreNextPress = True
    HalifaxActionAlarmButton.ignoreNextPress = True
    resetFixTimeButton.ignoreNextPress = True

#create button objects
alarmButtonWidth = (SCREEN_WIDTH/3 - 2*30)
alarmButtonY = SCREEN_HEIGHT/2 - alarmButtonWidth/2

quitButton = button(DISPLAYSURF, [], SCREEN_WIDTH - 230*resolutionMultiplier, 30*resolutionMultiplier, 
                    200*resolutionMultiplier, 100*resolutionMultiplier, 
                    defaultImage = pygame.image.load("images/Quit.png").convert_alpha(), 
                    onclickFunction = quitFunc)

resetFixTimeButton = button(DISPLAYSURF, [scenes["default"], scenes["acknowledge"]], 
                            30*resolutionMultiplier, 30*resolutionMultiplier, 
                            200*resolutionMultiplier, 100*resolutionMultiplier, 
                            pygame.image.load("images/Blank-Blue.png").convert_alpha(), 
                            onclickFunction = resetFixesAlarm)

fixesMuteButton = button(DISPLAYSURF, [scenes["default"], scenes["acknowledge"]], 
                         (200+30+30)*resolutionMultiplier, 30*resolutionMultiplier, 
                         100*resolutionMultiplier, 100*resolutionMultiplier, 
                         defaultImage = pygame.image.load("images/Muted.png").convert_alpha(), 
                         onclickFunction = toggleFixesAlarmMute)

DCSAlarmButton = button(DISPLAYSURF, [scenes["default"]], 
                        30*2, alarmButtonY, 
                        alarmButtonWidth, alarmButtonWidth,
                        defaultImage = pygame.image.load("images/DCS-red.png").convert_alpha(),
                        clickedImage = pygame.image.load("images/DCS-Gray.png").convert_alpha(), 
                        onclickFunction = DCSAlarmObj.playAlarm)

GeneralAlarmButton = button(DISPLAYSURF, [scenes["default"]], 
                            30*3 + alarmButtonWidth, alarmButtonY, 
                            alarmButtonWidth, alarmButtonWidth, 
                            defaultImage = pygame.image.load("images/General-red.png").convert_alpha(),
                            clickedImage = pygame.image.load("images/General-Gray.png").convert_alpha(),
                            onclickFunction = GeneralAlarmObj.playAlarm)

HalifaxActionAlarmButton = button(DISPLAYSURF, [scenes["default"]], 
                                  30*4 + alarmButtonWidth*2, alarmButtonY, 
                                  alarmButtonWidth, alarmButtonWidth,
                                  defaultImage = pygame.image.load("images/Action-red.png").convert_alpha(),
                                  clickedImage = pygame.image.load("images/Action-Gray.png").convert_alpha(),
                                  onclickFunction = HalifaxActionAlarmObj.playAlarm)

acknowledgeSize: tuple[float,float] = (60*1.7*resolutionMultiplier, 80*1.7*resolutionMultiplier)
Acknowledge = button(DISPLAYSURF, [scenes["acknowledge"]], 
                     acknowledgeSize[0], acknowledgeSize[1], 
                     SCREEN_WIDTH-(acknowledgeSize[0]*2), SCREEN_HEIGHT-(acknowledgeSize[1]*2), 
                     defaultImage = pygame.image.load("images/Acknowledge.png").convert_alpha(), 
                     onclickFunction = stopAlarm)
del acknowledgeSize
setIgnoreNextPress()

toggleNightModeButton = button(DISPLAYSURF, [scenes["default"], scenes["acknowledge"]],
                               (1080-190)*resolutionMultiplier, (720-170)*resolutionMultiplier, 
                               150*resolutionMultiplier, 150*resolutionMultiplier, 
                               defaultImage = image["toggleDayMode"], 
                               onclickFunction = toggleNightMode)

# finish defining alarm objects
DCSAlarmObj.alarmButton = DCSAlarmButton
GeneralAlarmObj.alarmButton = GeneralAlarmButton
HalifaxActionAlarmObj.alarmButton = HalifaxActionAlarmButton

#setup TPrint stuff
fixesAlarmPrinter = TextPrint()
fixesAlarmPrinter.reset()
FPSPrinter = TextPrint()
FPSPrinter.reset()
FPSPrinter.font1 = pygame.font.Font(None, 20 * resolutionMultiplier)
FPSPrinter.x = 10 * resolutionMultiplier
FPSPrinter.y = 10 * resolutionMultiplier
#FPSPrinter.line_height = 80 * resolutionMultiplier

pygame.event.set_allowed((pygame.QUIT, pygame.WINDOWFOCUSGAINED, pygame.WINDOWFOCUSLOST))#control which events are allowed on the queue

#print("starting loop")

while True: # main control loop
    buttonsInScene: list = []
    for object in scenes[scene]:
        if object.__class__ is button:
            buttonsInScene.append(object)

    for event in pygame.event.get():
        if event.type == QUIT: # if program exited then end program
            quitFunc()
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            quitFunc()
        elif event.type == pygame.WINDOWFOCUSGAINED:
            FPS = 60
        elif event.type == pygame.WINDOWFOCUSLOST:
            FPS = 2
        elif event.type == pygame.WINDOWCLOSE:
            #print("WINDOWCLOSE event detected - quitting...")
            quitFunc()
        elif event.type == pygame.MOUSEBUTTONDOWN:
            displayFPSInfo = not event.touch     
                
            if event.touch == 1:
                if quitButton.buttonRect.collidepoint(event.pos):
                        if quitButton in scenes["default"]:
                            quitFunc()
                else:
                    if quitButton in scenes["default"]:
                        scenes["default"].remove(quitButton)
                        scenes["acknowledge"].remove(quitButton)
                        
            elif quitButton in scenes["default"]:
                if quitButton.buttonRect.collidepoint(event.pos):
                    quitFunc()
            else:
                scenes["default"].insert(0,quitButton)
                scenes["acknowledge"].insert(0,quitButton)
                quitButton.ignoreNextPress = True      
                
            
            for thisButton in buttonsInScene:
                if thisButton.buttonRect.collidepoint(event.pos):
                    thisButton.runOnclickFunction = True
                    buttonsInScene.remove(thisButton)
            
                
            
    if nightMode:
        DISPLAYSURF.fill("#202525") # set background colour to night mode
    else:
        DISPLAYSURF.fill("#d0d0d0") # set background colour to day mode

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
   
    if displayFPSInfo:
        FPSPrinter.tprint(DISPLAYSURF, F"FPS: {round(FramePerSec.get_fps(),1)} ")
        FPSPrinter.tprint(DISPLAYSURF, F"                     mspt:{FramePerSec.get_time()} ")

    #render frame at the right time
    pygame.display.update()
    FramePerSec.tick(FPS)