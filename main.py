# Imports
import sys
import pygame
import time
from pygame.locals import QUIT
from typing import Callable
from OliversButtonModule import button as button
from OliversSquircleModule import squircle as squircle

# Initializing pygame and mixer
pygame.mixer.pre_init(frequency=48000, buffer=2048)
pygame.init()
pygame.mixer.init()

# Defining colors
WHITE = (255, 255, 255)

# Setting up screen
resolutionMultiplier = 3
SCREEN_WIDTH = 1080 * resolutionMultiplier
SCREEN_HEIGHT = 720 * resolutionMultiplier
DISPLAYSURF = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), (pygame.FULLSCREEN | pygame.SCALED))  # | pygame.NOFRAME  pygame.RESIZABLE
pygame.display.set_caption('DCS Alarm Panel')

# Setting up mixer
pygame.mixer.music.set_volume(1.00)
Notify = pygame.mixer.Sound("sound/Notify.wav")
Notify.set_volume(0.5)
boatHorn = pygame.mixer.Sound("sound/BOATHorn_Horn of a ship 1.wav")
boatHorn.set_volume(1.00)

# Setting up fonts
hornFont = pygame.font.Font(None, 100 * resolutionMultiplier)
myFont = pygame.font.SysFont('Arial', 50)

# Original alarms (commented out for now)
# DCSAlarm = pygame.mixer.Sound("sound/DCSAlarm.wav")
# GeneralAlarm = pygame.mixer.Sound("sound/GeneralAlarm.wav")
# HalifaxActionAlarm = pygame.mixer.Sound("sound/HalifaxActionAlarm.wav")

# "Corrected" alarms
HalifaxActionAlarm = pygame.mixer.Sound("sound/DCSAlarm.wav")
DCSAlarm = pygame.mixer.Sound("sound/GeneralAlarm.wav")
GeneralAlarm = pygame.mixer.Sound("sound/HalifaxActionAlarm.wav")

# Images
image = {
    "muted": pygame.image.load("images/Muted.png").convert_alpha(),
    "unmuted": pygame.image.load("images/Unmuted.png").convert_alpha(),
    "toggleNightMode": pygame.image.load("images/ToggleDayMode.png").convert_alpha(),
    "toggleDayMode": pygame.image.load("images/ToggleNightMode.png").convert_alpha(),
}

# Setting up FPS
FPS = 60
FramePerSec = pygame.time.Clock()
alarmTimeFPS = 20
alarmTimeCounter = 0
displayFPSInfo = True

# Global variables
currentAlarm = None
AlarmTime = 6  # Minutes
ResetNext = False
nightMode = False
nextFix = time.localtime().tm_min + AlarmTime - 1 + (round(time.localtime().tm_sec / 60))
timeUntilNextFix = (60 - time.localtime().tm_min + nextFix) % 60
fixesAlarmMuted = True

# Scenes
scenes = {"default": [], "acknowledge": []}
scene = "default"
nextScene = "default"

class TextPrint:
    """
    Class to handle text printing on the screen.
    """
    def __init__(self):
        self.reset()
        self.font1 = pygame.font.Font(None, 90 * resolutionMultiplier)

    def tprint(self, screen, text, moveDown=False) -> None:
        """
        Prints text on the screen.
        """
        text_bitmap = self.font1.render(text, True, (0, 0, 0))
        screen.blit(text_bitmap, (self.x, self.y))
        if moveDown:
            self.y += self.line_height

    def reset(self) -> None:
        """
        Resets the text position.
        """
        self.x = 50 * resolutionMultiplier
        self.y = 50 * resolutionMultiplier
        self.line_height = 80 * resolutionMultiplier

class alarmObj:
    """
    Class to represent an alarm object.
    """
    def __init__(self, alarmButton: button, alarmSound: pygame.mixer.Sound) -> None:
        self.alarmButton = alarmButton
        self.alarmSound = alarmSound

    def playAlarm(self) -> None:
        """
        Plays the alarm sound if no other alarm is currently playing.
        Sets the next scene to 'acknowledge' and marks the alarm button as pressed.
        """
        global currentAlarm
        if currentAlarm is None:
            self.alarmSound.play(loops=-1, maxtime=(10**5), fade_ms=100)
            global nextScene
            currentAlarm = self
            nextScene = "acknowledge"
            self.alarmButton.alreadyPressed = True

def stopAlarm() -> None:
    """
    Stops the currently playing alarm sound and resets the current alarm.
    Sets the next scene to 'default' and ignores the next button press.
    """
    global currentAlarm
    if currentAlarm:
        currentAlarm.alarmSound.stop()  # Stops the alarm sound
        currentAlarm = None
        global nextScene
        nextScene = "default"
        setIgnoreNextPress()

class squircleButton(squircle, button):
    """
    Class to represent a button with a squircle shape.
    """
    def __init__(self, DISPLAYSURF: pygame.Surface, scenes: list, x: int, y: int, width: int, height: int,
                 text: str | None, myFont: pygame.font.Font | None, textColor: pygame.Color | None,
                 borderColor: pygame.Color | None, fillColor: pygame.Color | None,
                 onClickFunction: Callable,
                 borderRadius: int = 50*resolutionMultiplier, borderWidth: int = 3*resolutionMultiplier,) -> None:
        """_summary_

        Args:
            DISPLAYSURF (pygame.Surface): surface to draw self onto when process is called
            scenes (list): scenes to add self
            x (int): distance from left of screen
            y (int): distance from top of screen
            width (int): width of self
            height (int): height of self
            text (str | None): text to display on button
            myFont (pygame.font.Font | None): font of text
            textColor (pygame.Color | None): text color
            borderColor (pygame.Color | None): border color
            fillColor (pygame.Color | None): fill color
            onClickFunction (Callable): function to run when button clicked
            borderRadius (int, optional): corner radius. Defaults to 50*resolutionMultiplier.
            borderWidth (int, optional): border width. Defaults to 3*resolutionMultiplier.

        Raises:
            ValueError: _description_
        """        
        squircle.__init__(self, width, height, fillColor, borderRadius, borderWidth, borderColor=borderColor)
        if text:
            if not (myFont and textColor):
                raise ValueError("myFont and textColor must be provided if text is provided")
            self.setText(text, myFont, textColor)
        button.__init__(self, DISPLAYSURF, scenes, x, y, width, height,
                        defaultImage=self.mySurface, onClickFunction=onClickFunction)

# Initialize alarm objects
currentAlarm: alarmObj | None

# Need to partly define alarm objects before defining buttons
DCSAlarmObj = alarmObj(None, DCSAlarm)
GeneralAlarmObj = alarmObj(None, GeneralAlarm)
HalifaxActionAlarmObj = alarmObj(None, HalifaxActionAlarm)

# Define functions
def quitFunc() -> None:
    """
    Quits the program when the 'Quit' button is pressed.
    """
    pygame.quit()
    sys.exit()

def toggleNightMode() -> None:
    """
    Toggles between night mode and day mode.
    """
    global nightMode
    if nightMode := not nightMode:
        toggleNightModeButton.updateImages(image["toggleNightMode"])
    else:
        toggleNightModeButton.updateImages(image["toggleDayMode"])

def resetFixesAlarm() -> None:
    """
    Resets the fixes alarm timer.
    """
    global nextFix
    nextFix = (time.localtime().tm_min + max(AlarmTime - 1, 0) + (round((time.localtime().tm_sec + 2) / 60))) % 60

def checkFixesAlarm() -> None:
    """
    Checks and updates the fixes alarm timer.
    """
    global nextFix
    global timeUntilNextFix
    global ResetNext
    mins = time.localtime().tm_min
    if timeUntilNextFix == 0 and time.localtime().tm_sec == 59:
        ResetNext = True
    elif ResetNext and time.localtime().tm_sec == 0:  # Checks if timer needs to be reset
        ResetNext = False
        nextFix = (mins + max(AlarmTime - 1, 0)) % 60
        if not fixesAlarmMuted:
            Notify.play(loops=1, fade_ms=0)
    elif timeUntilNextFix > AlarmTime:
        resetFixesAlarm()
    timeUntilNextFix = ((60 - mins) + nextFix) % 60  # Calculate timeUntilNextFix

def toggleFixesAlarmMute() -> None:
    """
    Toggles the mute state of the fixes alarm.
    """
    global fixesAlarmMuted
    if fixesAlarmMuted := not fixesAlarmMuted:
        fixesMuteButton.updateImages(image["muted"])
    else:
        fixesMuteButton.updateImages(image["unmuted"])

def setIgnoreNextPress() -> None:
    """
    Used to prevent double activations on one click.
    """
    Acknowledge.ignoreNextPress = True
    DCSAlarmButton.ignoreNextPress = True
    GeneralAlarmButton.ignoreNextPress = True
    HalifaxActionAlarmButton.ignoreNextPress = True
    resetFixTimeButton.ignoreNextPress = True

def playHornFunc() -> None:
    """
    Plays the boat horn sound.
    """
    if boatHorn.get_num_channels() < 2:
        boatHorn.play(loops=5, maxtime=(10**4 * 2), fade_ms=0)

def stopHornFunc() -> None:
    """
    Stops the boat horn sound.
    """
    boatHorn.stop()

# Create button objects
alarmButtonWidth = (SCREEN_WIDTH / 3 - 2 * 30)
alarmButtonY = SCREEN_HEIGHT / 2 - alarmButtonWidth / 2

quitButton = button(DISPLAYSURF, [], SCREEN_WIDTH - 230 * resolutionMultiplier, 30 * resolutionMultiplier, 
                    200 * resolutionMultiplier, 100 * resolutionMultiplier, 
                    defaultImage=pygame.image.load("images/Quit.png").convert_alpha(), 
                    onClickFunction=quitFunc)

resetFixTimeButton = button(DISPLAYSURF, [scenes["default"], scenes["acknowledge"]], 
                            30 * resolutionMultiplier, 30 * resolutionMultiplier, 
                            200 * resolutionMultiplier, 100 * resolutionMultiplier, 
                            pygame.image.load("images/Blank-Blue.png").convert_alpha(), 
                            onClickFunction=resetFixesAlarm)

fixesMuteButton = button(DISPLAYSURF, [scenes["default"], scenes["acknowledge"]], 
                         (200 + 30 + 30) * resolutionMultiplier, 30 * resolutionMultiplier, 
                         100 * resolutionMultiplier, 100 * resolutionMultiplier, 
                         defaultImage=pygame.image.load("images/Muted.png").convert_alpha(), 
                         onClickFunction=toggleFixesAlarmMute)

DCSAlarmButton = button(DISPLAYSURF, [scenes["default"]], 
                        30 * 2, alarmButtonY, 
                        alarmButtonWidth, alarmButtonWidth,
                        defaultImage=pygame.image.load("images/DCS-red.png").convert_alpha(),
                        hoverImage=pygame.image.load("images/DCS-Gray.png").convert_alpha(), 
                        onClickFunction=DCSAlarmObj.playAlarm)

GeneralAlarmButton = button(DISPLAYSURF, [scenes["default"]], 
                            30 * 3 + alarmButtonWidth, alarmButtonY, 
                            alarmButtonWidth, alarmButtonWidth, 
                            defaultImage=pygame.image.load("images/General-red.png").convert_alpha(),
                            hoverImage=pygame.image.load("images/General-Gray.png").convert_alpha(),
                            onClickFunction=GeneralAlarmObj.playAlarm)

HalifaxActionAlarmButton = button(DISPLAYSURF, [scenes["default"]], 
                                  30 * 4 + alarmButtonWidth * 2, alarmButtonY, 
                                  alarmButtonWidth, alarmButtonWidth,
                                  defaultImage=pygame.image.load("images/Action-red.png").convert_alpha(),
                                  hoverImage=pygame.image.load("images/Action-Gray.png").convert_alpha(),
                                  onClickFunction=HalifaxActionAlarmObj.playAlarm)

acknowledgeSize: tuple[float, float] = (60 * 1.7 * resolutionMultiplier, 80 * 1.7 * resolutionMultiplier)
Acknowledge = button(DISPLAYSURF, [scenes["acknowledge"]], 
                     acknowledgeSize[0], acknowledgeSize[1], 
                     SCREEN_WIDTH - (acknowledgeSize[0] * 2), SCREEN_HEIGHT - (acknowledgeSize[1] * 2), 
                     defaultImage=pygame.image.load("images/Acknowledge.png").convert_alpha(), 
                     onClickFunction=stopAlarm)
del acknowledgeSize
setIgnoreNextPress()

toggleNightModeButton = button(DISPLAYSURF, [scenes["default"], scenes["acknowledge"]],
                               (1080 - 190) * resolutionMultiplier, (720 - 170) * resolutionMultiplier, 
                               150 * resolutionMultiplier, 150 * resolutionMultiplier, 
                               defaultImage=image["toggleDayMode"], 
                               onClickFunction=toggleNightMode)

hornButton = squircleButton(DISPLAYSURF, [scenes["default"]], 300, SCREEN_HEIGHT - 500, 
                            700 * resolutionMultiplier, 160 * resolutionMultiplier,
                            text="Horn", myFont=hornFont, textColor=pygame.Color(0, 0, 0, 255), 
                            borderColor=pygame.Color(0, 0, 0, 255), fillColor=pygame.Color(140, 140, 140, 255),
                            onClickFunction=playHornFunc)
hornButton.onReleaseFunction = stopHornFunc
hornButton.clickedImage = hornButton.redraw(fillColor=pygame.Color(100, 100, 100, 255))

# Finish defining alarm objects
DCSAlarmObj.alarmButton = DCSAlarmButton
GeneralAlarmObj.alarmButton = GeneralAlarmButton
HalifaxActionAlarmObj.alarmButton = HalifaxActionAlarmButton

# Setup TPrint stuff
fixesAlarmPrinter = TextPrint()
fixesAlarmPrinter.reset()
FPSPrinter = TextPrint()
FPSPrinter.reset()
FPSPrinter.font1 = pygame.font.Font(None, 20 * resolutionMultiplier)
FPSPrinter.x = 10 * resolutionMultiplier
FPSPrinter.y = 10 * resolutionMultiplier

# Control which events are allowed on the queue
pygame.event.set_allowed((pygame.QUIT, pygame.KEYDOWN, pygame.WINDOWCLOSE,
                          pygame.WINDOWFOCUSGAINED, pygame.WINDOWFOCUSLOST, 
                          pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP))

# Main control loop
while __name__ == "__main__":
    hasOnClickFunction: list = []
    hasOnReleaseFunction: list = []
    for object in scenes[scene]:
        if hasattr(object, "onClickFunction"):
            if object.onClickFunction:
                hasOnClickFunction.append(object)
                if hasattr(object, "onReleaseFunction"):
                    if object.onReleaseFunction:
                        hasOnReleaseFunction.append(object)

    for event in pygame.event.get():
        if event.type == QUIT:  # if program exited then end program
            quitFunc()
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            quitFunc()
        elif event.type == pygame.WINDOWFOCUSGAINED:
            FPS = 60
        elif event.type == pygame.WINDOWFOCUSLOST:
            FPS = 2
        elif event.type == pygame.WINDOWCLOSE:
            quitFunc()
        elif event.type == pygame.MOUSEBUTTONDOWN:
            for thisIntractable in hasOnClickFunction:
                if thisIntractable.myRect.collidepoint(event.pos):
                    thisIntractable.onClickFunction()
                    hasOnClickFunction.remove(thisIntractable)

            if event.touch == 1:
                displayFPSInfo = False
                if quitButton in scenes["default"]:
                    scenes["default"].remove(quitButton)
                    scenes["acknowledge"].remove(quitButton)
            else:
                scenes["default"].insert(0, quitButton)
                scenes["acknowledge"].insert(0, quitButton)
                quitButton.ignoreNextPress = True
        elif event.type == pygame.MOUSEBUTTONUP:
            for thisIntractable in hasOnReleaseFunction:
                if thisIntractable.myRect.collidepoint(event.pos):
                    thisIntractable.onReleaseFunction()
                    hasOnReleaseFunction.remove(thisIntractable)

    if nightMode:
        DISPLAYSURF.fill("#202525")  # set background colour to night mode
    else:
        DISPLAYSURF.fill("#d0d0d0")  # set background colour to day mode

    scene = nextScene

    # renders all objects in the current scene
    for object in scenes[scene]:
        object.process(None)

    # updates fixes alarm time values every few frames
    if alarmTimeCounter >= FPS / alarmTimeFPS:
        alarmTimeCounter = 0
        checkFixesAlarm()
    else:
        alarmTimeCounter += 1
    # render fixes alarm time
    seconds = 60 - time.localtime().tm_sec - 1
    if seconds <= 9:
        fixesAlarmPrinter.tprint(DISPLAYSURF, F"{timeUntilNextFix} : 0{seconds}")
    else:
        fixesAlarmPrinter.tprint(DISPLAYSURF, F"{timeUntilNextFix} : {seconds}")

    if displayFPSInfo:
        FPSPrinter.tprint(DISPLAYSURF, F"FPS: {round(FramePerSec.get_fps(), 1)} ")
        FPSPrinter.tprint(DISPLAYSURF, F"                     mspt:{FramePerSec.get_time()} ")

    # render frame at the right time
    pygame.display.update()
    FramePerSec.tick(FPS)