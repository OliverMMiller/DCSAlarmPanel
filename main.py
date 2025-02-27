# Imports
import sys
import pygame
import time
from pygame.locals import QUIT
from typing import NewType
from OliversButtonModule import button as button

# Initializing pygame and mixer
pygame.mixer.pre_init(frequency=48000, buffer=2048)
pygame.init()
pygame.mixer.init()

# Defining colors
WHITE = (255, 255, 255)

# Setting up screen
RES_MULT = 3
SCREEN_WIDTH = 1080 * RES_MULT
SCREEN_HEIGHT = 720 * RES_MULT
DISPLAYSURF = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), (pygame.FULLSCREEN | pygame.SCALED))  # | pygame.NOFRAME  pygame.RESIZABLE
pygame.display.set_caption('DCS Alarm Panel')

# Setting up mixer
pygame.mixer.music.set_volume(1.00)
Notify = pygame.mixer.Sound("sound/Notify.wav")
Notify.set_volume(0.5)
longHornSound = pygame.mixer.Sound("sound/BOATHorn_Horn of a ship 1.wav")
longHornSound.set_volume(1.00)
shortHornSound = pygame.mixer.Sound("sound/BOATHorn_Horn of a ship 1.wav")
shortHornSound.set_volume(1.00)

# Setting up fonts
hornFont = pygame.font.Font(None, 33 * RES_MULT)
alarmFont = pygame.font.Font(None, 55 * RES_MULT)
myFont = pygame.font.SysFont('Arial', 20 * RES_MULT)

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
hornQueue = []
hornPlaying: str = ""
waitTime = time.time()

# Scenes
scenes = {"default": [], "acknowledge": []}
scene = "default"
nextScene = "default"

class TextPrint:
    """
    Class to handle text printing on the screen.
    """
    def __init__(self, x: int, y: int, 
                font: pygame.font.Font, textColor: pygame.Color = pygame.Color(0, 0, 0),
                lineSpacing: int | None = -1, indentSize: int = 10) -> None:
        self.myFont = font
        self.myFont = self.myFont
        self.textColor = textColor
        self.startX = x
        self.startY = y
        if lineSpacing is None:
            self.defaultLineSpacing = None
        else:
            self.defaultLineSpacing = lineSpacing
        self.indentSize = indentSize
        self.reset()

    def PrintLine(self, screen, text: str) -> None:
        """
        Prints text on the screen.
        """
        text_bitmap = self.myFont.render(text, True, self.textColor)
        screen.blit(text_bitmap, (self.x, self.y))
        if self.lineSpacing is not None:
            self.y += self.myFont.get_height() + self.lineSpacing
        
    def tprint(self, screen, text: list[str] | str) -> None:
        """
        Prints text on the screen.
        """
        if isinstance(text, str):
            if "\n" in text:
                text = text.split("\n")
            else:
                text = [text]
        if isinstance(text, list):
            for line in text:
                self.PrintLine(screen, line)
        else:
            raise ValueError("text must be a string or a list of strings")


    def reset(self) -> None:
        """
        Resets the text position.
        """
        self.x = self.startX
        self.y = self.startY
        self.lineSpacing = self.defaultLineSpacing
        
    def indent(self, direction: int) -> None:
        """
        Indents the text.
        """
        self.x += self.indentSize * direction

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

def validate_value(value: float | int, min: float | int, max: float | int) -> float | int:
    """
    Validates if a value is within a specified range.
    """
    if min <= value <= max:
        return value
    else:
        raise ValueError(f"Value {value} is out of the accepted range ({min}-{max})")

Unspecified = NewType("Unspecified", None)
def validate_kwarg(kwargsList, key: str, expected_type, default=Unspecified, validator=None):
    """
    Validates a key in kwargsList and returns the value if it exists and is of the expected type.
    Optionally validates the value using a provided validator function.
    
    Parameters:
    kwargsList (dict): The dictionary containing potential attributes.
    key (str): The key to look for in kwargsList.
    expected_type (type): The expected type of the value.
    default (any, optional): The default value to assign if key is not in kwargsList. Defaults to Unspecified.
    validator (function, optional): A function to validate the value. Defaults to None.
    """
    try:
        kwargsList = kwargsList["kwargs"]
    except KeyError:
        return
    if key in kwargsList and isinstance(kwargsList[key], expected_type):
        value = kwargsList[key]
        if validator:
            value = validator(value)
        return value
    elif default is not Unspecified:
        return default

def assign_kwargs_if_valid(thisClass, kwargsList, key: str, expected_type, default=Unspecified, validator=None):
    """
    Assigns the value from kwargsList to an attribute of thisClass if it exists and is of the expected type.
    Optionally validates the value using a provided validator function.
    
    Parameters:
    thisClass (object): The class instance to assign the attribute to.
    kwargsList (dict): The dictionary containing potential attributes.
    key (str): The key to look for in kwargsList.
    expected_type (type): The expected type of the value.
    default (any, optional): The default value to assign if key is not in kwargsList. Defaults to Unspecified.
    validator (function, optional): A function to validate the value. Defaults to None.
    """
    try:
        kwargsList = kwargsList["kwargs"]
    except KeyError:
        return
    if key in kwargsList and isinstance(kwargsList[key], expected_type):
        value = kwargsList[key]
        if validator:
            value = validator(value)
        thisClass.__setattr__(key, value)
    elif default is not Unspecified:
        thisClass.__setattr__(key, default)
class squircle:
    """
    Class to represent a squircle shape.
    """
    def __init__(self, width: int, height: int, borderColor: pygame.Color | None, fillColor: pygame.Color | None, **kwargs) -> None:
        """
        Initializes a squircle shape.

        Args:
            width (int): The width of the squircle.
            height (int): The height of the squircle.
            borderColor (pygame.Color | None): The color of the border.
            fillColor (pygame.Color | None): The color to fill the squircle.
            
            borderWidth (int): The width of the border.
            borderRadius (int): The radius of the border corners.
            ignoreTextOverflow (bool): Whether to ignore text overflow.

        Raises:
            ValueError: If borderColor and/or fillColor are not provided.

        """
        self.width = width
        self.height = height
        self.borderColor = borderColor
        self.fillColor = fillColor
        self.mySurface = pygame.Surface((width, height), flags=pygame.SRCALPHA)
        self.borderWidth: int
        self.borderRadius: int
        self.ignoreTextOverflow: bool       
        assign_kwargs_if_valid(self, kwargs, "borderWidth", int, 3 * RES_MULT, validator=lambda x: validate_value(x, 0, min(width, height) / 2))
        assign_kwargs_if_valid(self, kwargs, "borderRadius", int, 50 * RES_MULT, validator=lambda x: validate_value(x, 0, min(width, height) / 2))
        assign_kwargs_if_valid(self, kwargs, "ignoreTextOverflow", bool, False)
        
        if not (self.borderColor and self.fillColor):
            raise ValueError("borderColor and/or fillColor must be provided")
        
        rect2 = pygame.Rect(self.borderWidth, self.borderWidth, self.width - (self.borderWidth * 2), self.height - (self.borderWidth * 2))
        if self.fillColor:
            pygame.draw.rect(self.mySurface, self.fillColor, rect2, 0, self.borderRadius)
        if self.borderColor:
            pygame.draw.rect(self.mySurface, self.borderColor, rect2, self.borderWidth, self.borderRadius)

    def updateText(self, **kwargs) -> None:
        """
        Updates the text on the squircle.
        """
        assign_kwargs_if_valid(self, kwargs, "text", str)
        assign_kwargs_if_valid(self, kwargs, "font", pygame.font.Font)
        assign_kwargs_if_valid(self, kwargs, "textColor", pygame.Color)
        assign_kwargs_if_valid(self, kwargs, "justificationType", str, "centered", validator=lambda x: x in ("centered", "absolute"))
        assign_kwargs_if_valid(self, kwargs, "xJustification", float, 0.5, validator=lambda x: validate_value(x, 0, 1))
        assign_kwargs_if_valid(self, kwargs, "yJustification", float, 0.5, validator=lambda x: validate_value(x, 0, 1))
        assign_kwargs_if_valid(self, kwargs, "lineSpacing", int, 4, validator=lambda x: validate_value(x, 0, 1**4))

        size = self.font.size(self.text)
        if (size[0] > self.width or size[1] > self.height) and not self.ignoreTextOverflow:
            raise ValueError(f"Text too large to fit in squircle\nText: {self.text}")
        if self.justificationType == "centered":
            x = self.width * self.xJustification - size[0] / 2
            y = self.height * self.yJustification - size[1] / 2
        if self.justificationType == "absolute":
            x = self.xJustification
            y = self.yJustification
        self.mySurface.blit(self.font.render(self.text, True, self.textColor), (x, y))

    def setText(self, text: str | list[str], font: pygame.font.Font, color: pygame.Color, 
                justificationType: str = "centered", 
                xJustification: float = 0.5, yJustification: float = 0.5) -> None:
        """
        Sets the text on the squircle.
        """
        self.text = text
        self.font = font
        self.textColor = color
        self.justificationType = justificationType
        self.xJustification = validate_value(xJustification, 0, 1)
        self.yJustification = validate_value(yJustification, 0, 1)
        self.updateText()

    def redraw(self, **kwargs) -> pygame.Surface:
        """
        Redraws the squircle with updated properties.
        """
        for arg in kwargs:
            if arg in ("width", "height", "borderColor", "fillColor", "borderWidth", "borderRadius"):
                setattr(self, arg, kwargs[arg])

        if not (self.borderColor and self.fillColor):
            raise ValueError("borderColor and/or fillColor must be provided")
        rect2 = pygame.Rect(self.borderWidth, self.borderWidth, self.width - (self.borderWidth * 2), self.height - (self.borderWidth * 2))
        if self.fillColor:
            pygame.draw.rect(self.mySurface, self.fillColor, rect2, 0, self.borderRadius)
        if self.borderColor:
            pygame.draw.rect(self.mySurface, self.borderColor, rect2, self.borderWidth, self.borderRadius)

        self.updateText()
        return self.mySurface

class squircleButton(squircle, button):
    """
    Class to represent a button with a squircle shape.
    """
    def __init__(self, DISPLAYSURF: pygame.Surface, scenes: list, x, y, width: int, height: int,
                 text: str | None, myFont: pygame.font.Font | None, textColor: pygame.Color | None,
                 borderColor: pygame.Color | None, fillColor: pygame.Color | None,
                 onClickFunction, **kwargs) -> None:
        squircle.__init__(self, width, height, borderColor, fillColor, kwargs = kwargs)
        if text:
            if not (myFont and textColor):
                raise ValueError("myFont and textColor must be provided if text is provided")
            self.setText(text, myFont, textColor)
        button.__init__(self, DISPLAYSURF, scenes, x, y, width, height,
                        defaultImage=self.mySurface, onClickFunction=onClickFunction,)


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
    
def shortHornFunc() -> None:
    if len(hornQueue) < 4:
        hornQueue.append("short")
def longHornFunc() -> None:
    if len(hornQueue) < 4:
        hornQueue.append("long")

# Create button objects
alarmButtonWidth = (SCREEN_WIDTH / 3 - 2 * 30)
alarmButtonY = SCREEN_HEIGHT / 2 - alarmButtonWidth / 2

quitButton = button(DISPLAYSURF, [], SCREEN_WIDTH - 230 * RES_MULT, 30 * RES_MULT, 
                    200 * RES_MULT, 100 * RES_MULT, 
                    defaultImage=pygame.image.load("images/Quit.png").convert_alpha(), 
                    onClickFunction=quitFunc)

resetFixTimeButton = squircleButton(DISPLAYSURF, [scenes["default"], scenes["acknowledge"]], 
                                    30 * RES_MULT, 30 * RES_MULT, 
                                    200 * RES_MULT, 100 * RES_MULT, 
                                    text=None, myFont=myFont, textColor=pygame.Color(0, 0, 0),
                                    borderColor=pygame.Color(0, 0, 0), fillColor=pygame.Color(153, 204, 255),
                                    onClickFunction=resetFixesAlarm, borderRadius = 30 * RES_MULT)

fixesMuteButton = button(DISPLAYSURF, [scenes["default"], scenes["acknowledge"]], 
                         (200 + 30 + 30) * RES_MULT, 30 * RES_MULT, 
                         100 * RES_MULT, 100 * RES_MULT, 
                         defaultImage=pygame.image.load("images/Muted.png").convert_alpha(), 
                         onClickFunction=toggleFixesAlarmMute)

DCSAlarmButton = squircleButton(DISPLAYSURF, [scenes["default"]], 
                                30 * 2, alarmButtonY, 
                                alarmButtonWidth, alarmButtonWidth/3,
                                text="DCS Alarm", myFont=alarmFont, textColor=pygame.Color(0, 0, 0),
                                borderColor=pygame.Color(0, 0, 0), fillColor=pygame.Color(220, 0, 0),
                                onClickFunction=DCSAlarmObj.playAlarm, borderRadius = 30 * RES_MULT)
DCSAlarmButton.hoverImage = DCSAlarmButton.redraw(fillColor=pygame.Color(150, 150, 150)).copy()

GeneralAlarmButton = squircleButton(DISPLAYSURF, [scenes["default"]], 
                                    30 * 3 + alarmButtonWidth, alarmButtonY, 
                                    alarmButtonWidth, alarmButtonWidth/3, 
                                    text="General Alarm", myFont=alarmFont, textColor=pygame.Color(0, 0, 0),
                                    borderColor=pygame.Color(0, 0, 0), fillColor=pygame.Color(220, 0, 0),
                                    onClickFunction=GeneralAlarmObj.playAlarm, borderRadius = 30 * RES_MULT)
GeneralAlarmButton.hoverImage = GeneralAlarmButton.redraw(fillColor=pygame.Color(150, 150, 150)).copy()

HalifaxActionAlarmButton = squircleButton(DISPLAYSURF, [scenes["default"]], 
                                          30 * 4 + alarmButtonWidth * 2, alarmButtonY,
                                          alarmButtonWidth, alarmButtonWidth/3,
                                          text="Action Stations", myFont=alarmFont, textColor=pygame.Color(0, 0, 0),
                                          borderColor=pygame.Color(0, 0, 0), fillColor=pygame.Color(220, 0, 0),
                                          onClickFunction=HalifaxActionAlarmObj.playAlarm, borderRadius = 30 * RES_MULT)
HalifaxActionAlarmButton.hoverImage = HalifaxActionAlarmButton.redraw(fillColor=pygame.Color(150, 150, 150)).copy()

acknowledgeSize: tuple[float, float] = (60 * 1.7 * RES_MULT, 80 * 1.7 * RES_MULT)
Acknowledge = squircleButton(DISPLAYSURF, [scenes["acknowledge"]], 
                             acknowledgeSize[0], acknowledgeSize[1], 
                             SCREEN_WIDTH - (acknowledgeSize[0] * 2), SCREEN_HEIGHT - (acknowledgeSize[1] * 2), 
                             text="Acknowledge", myFont=pygame.font.Font(None, 160 * RES_MULT), textColor=pygame.Color(0, 0, 0),
                             borderColor=pygame.Color(0, 0, 0), fillColor=pygame.Color(200, 0, 0),
                             onClickFunction=stopAlarm)
del acknowledgeSize

setIgnoreNextPress()

toggleNightModeButton = button(DISPLAYSURF, [scenes["default"], scenes["acknowledge"]],
                               (1080 - 190) * RES_MULT, (720 - 170) * RES_MULT, 
                               150 * RES_MULT, 150 * RES_MULT, 
                               defaultImage=image["toggleDayMode"], 
                               onClickFunction=toggleNightMode)

hornQueueDisplay = squircleButton(DISPLAYSURF, [scenes["default"]], DCSAlarmButton.x, DCSAlarmButton.y + DCSAlarmButton.height + 35, 
                            GeneralAlarmButton.x + GeneralAlarmButton.width - DCSAlarmButton.x, SCREEN_HEIGHT - (GeneralAlarmButton.y + GeneralAlarmButton.height + 150),
                            text=None, myFont=pygame.font.Font(None, 500), textColor=pygame.Color(0, 0, 0),
                            borderColor=pygame.Color(0, 0, 0, 255), fillColor=pygame.Color(140, 140, 140, 255), 
                            borderRadius = 30 * RES_MULT, onClickFunction=None)


shortHornBlast = squircleButton(DISPLAYSURF, [scenes["default"]], HalifaxActionAlarmButton.x, HalifaxActionAlarmButton.y + HalifaxActionAlarmButton.height + 35, 
                            HalifaxActionAlarmButton.width, 120 * RES_MULT,
                            text="Add Short Blast to Queue", myFont=hornFont, textColor=pygame.Color(0, 0, 0, 255), 
                            borderRadius = 30 * RES_MULT,
                            borderColor=pygame.Color(0, 0, 0, 255), fillColor=pygame.Color(140, 140, 140, 255),
                            onClickFunction=shortHornFunc)
shortHornBlast.clickedImage = shortHornBlast.redraw(fillColor=pygame.Color(100, 100, 100, 255)).copy()
shortHornBlast.hoverImage = shortHornBlast.redraw(fillColor=pygame.Color(150, 150, 150)).copy()

longHornBlast = squircleButton(DISPLAYSURF, [scenes["default"]], shortHornBlast.x, shortHornBlast.y + shortHornBlast.height + 35, 
                            shortHornBlast.width, shortHornBlast.height,
                            text="Add long Blast to Queue", myFont=hornFont, textColor=pygame.Color(0, 0, 0, 255), 
                            borderRadius = 30 * RES_MULT,
                            borderColor=pygame.Color(0, 0, 0, 255), fillColor=pygame.Color(140, 140, 140, 255),
                            onClickFunction=longHornFunc)
longHornBlast.clickedImage = longHornBlast.redraw(fillColor=pygame.Color(100, 100, 100, 255)).copy()
longHornBlast.hoverImage = longHornBlast.redraw(fillColor=pygame.Color(150, 150, 150)).copy()

# Finish defining alarm objects
DCSAlarmObj.alarmButton = DCSAlarmButton
GeneralAlarmObj.alarmButton = GeneralAlarmButton
HalifaxActionAlarmObj.alarmButton = HalifaxActionAlarmButton

# Setup TPrint stuff
fixesAlarmPrinter = TextPrint(50 * RES_MULT, 50 * RES_MULT, pygame.font.Font(None, 90 * RES_MULT), pygame.Color(0, 0, 0), lineSpacing = None)
FPSPrinter = TextPrint(10 * RES_MULT, 10 * RES_MULT, pygame.font.Font(None, 20 * RES_MULT), pygame.Color(0, 0, 0), lineSpacing = None)
hornQueueWriter = TextPrint(hornQueueDisplay.x + 30 * RES_MULT, hornQueueDisplay.y + 30 * RES_MULT, pygame.font.Font(None, 50 * RES_MULT), pygame.Color(0, 0, 0), lineSpacing = 0 * RES_MULT)
def updateHornQueueDisplay() -> None:
    """
    Updates the horn queue display.
    """
    global hornQueue
    global hornPlaying
    global waitTime
    hornQueueWriter.reset()
    #print(f"{hornQueue} : {hornPlaying} - {shortHornSound.get_num_channels()} - {longHornSound.get_num_channels()}")
    if shortHornSound.get_num_channels() == 0 and longHornSound.get_num_channels() == 0 and hornPlaying in ("short", "long"):
        hornPlaying = ""
        waitTime = time.time()
        
    if hornQueue and hornPlaying == "" and time.time() > waitTime + 1:
        hornPlaying = hornQueue.pop(0)
        if hornPlaying == "short":
            shortHornSound.play()
        elif hornPlaying == "long":
            longHornSound.play()
    if hornPlaying:
        hornQueueWriter.tprint(DISPLAYSURF, "Horn Playing:")
        hornQueueWriter.indent(1)
        hornQueueWriter.tprint(DISPLAYSURF, hornPlaying)
    hornQueueWriter.tprint(DISPLAYSURF, "Horn Queue:")
    hornQueueWriter.indent(1)
    hornQueueWriter.tprint(DISPLAYSURF, hornQueue)


# Control which events are allowed on the queue
pygame.event.set_allowed((pygame.QUIT, pygame.KEYDOWN, pygame.WINDOWCLOSE,
                          pygame.WINDOWFOCUSGAINED, pygame.WINDOWFOCUSLOST, 
                          pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP))

# Main control loop
while __name__ == "__main__":
    hasOnClickFunction: list = []
    #hasOnReleaseFunction: list = []
    for object in scenes[scene]:
        if hasattr(object, "onClickFunction"):
            if object.onClickFunction:
                hasOnClickFunction.append(object)
        # if hasattr(object, "onReleaseFunction"):
        #     if object.onReleaseFunction:
        #         hasOnReleaseFunction.append(object)

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
        # elif event.type == pygame.MOUSEBUTTONUP:
        #     for thisIntractable in hasOnReleaseFunction:
        #         if thisIntractable.myRect.collidepoint(event.pos):
        #             thisIntractable.onReleaseFunction()
        #             hasOnReleaseFunction.remove(thisIntractable)

    if nightMode:
        DISPLAYSURF.fill("#202525")  # set background colour to night mode
    else:
        DISPLAYSURF.fill("#d0d0d0")  # set background colour to day mode

    scene = nextScene

    # renders all objects in the current scene
    for object in scenes[scene]:
        object.process(None)

    updateHornQueueDisplay()

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