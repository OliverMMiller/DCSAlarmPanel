# Imports
import sys
import pygame
import time
from pygame.locals import QUIT
from typing import Callable
from OliversButtonModule import button as button
from OliversSquircleModule import squircle as squircle

from generateUniqueHornSound import pitch_shift

# Initializing pygame and mixer
pygame.mixer.pre_init(frequency=48000, buffer=2048)
pygame.init()
pygame.mixer.init()

# Defining colors
WHITE = (255, 255, 255)

# Setting up screen
DISPLAYSURF = pygame.display.set_mode((0, 0), (pygame.FULLSCREEN))  # | pygame.NOFRAME  pygame.RESIZABLE
pygame.display.set_caption('Horn Button')
SCREEN_WIDTH, SCREEN_HEIGHT = pygame.display.get_surface().get_size()

# Setting up mixer
pygame.mixer.music.set_volume(1.00)
boatHorn = pygame.mixer.Sound("sound/shipHorn.wav")
boatHorn.set_volume(1.00)
newHorn = boatHorn
newHorn.set_volume(0.90)

waterSplash = pygame.mixer.Sound("sound/waterSplash.mp3")
waterSplash.set_volume(0.70)

# Setting up fonts
hornFont = pygame.font.Font(None, 200)

# Setting up FPS
FPS = 60
FramePerSec = pygame.time.Clock()

# Global variables
nightMode = True

# Scenes
scenes = {"default": []}
scene = "default"

class TextPrint:
    """
    Class to handle text printing on the screen.
    """
    def __init__(self):
        self.reset()
        self.font1 = pygame.font.Font(None, 90)
        self.color = pygame.Color(0, 0, 0)

    def tprint(self, screen, text, moveDown=False) -> None:
        """
        Prints text on the screen.
        """
        for i in text.splitlines():
            text_bitmap = self.font1.render(i, True, self.color)
            screen.blit(text_bitmap, (self.x, self.y))
            if moveDown:
                self.y += self.line_height

    def reset(self) -> None:
        """
        Resets the text position.
        """
        self.x = 50
        self.y = 50
        self.line_height = 80


class squircleButton(squircle, button):
    """
    Class to represent a button with a squircle shape.
    """
    def __init__(self, DISPLAYSURF: pygame.Surface, scenes: list, x: int, y: int, width: int, height: int,
                 text: str | None, myFont: pygame.font.Font | None, textColor: pygame.Color | None,
                 borderColor: pygame.Color | None, fillColor: pygame.Color | None,
                 onClickFunction: Callable,
                 borderRadius: int = 50, borderWidth: int = 3,) -> None:
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
            borderRadius (int, optional): corner radius. Defaults to 50.
            borderWidth (int, optional): border width. Defaults to 3.

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

# Define functions
def quitFunc() -> None:
    """
    Quits the program when the 'Quit' button is pressed.
    """
    pygame.quit()
    sys.exit()
    
def weightedAverage(a: float, b: float, weight: float) -> float:
    return (a * weight + b * (1 - weight))


def playHornFunc() -> None:
    """
    Plays the boat horn sound.
    """
    global newHorn
    newHorn = pitch_shift(boatHorn , semitonesList[int(((pygame.mouse.get_pos()[0] - hornButton.x)) // semitoneSectionWidth)])
    
    if newHorn.get_num_channels() < 2:
        newHorn.play(loops=5, maxtime=(10**4 * 2), fade_ms=0)


def stopHornFunc() -> None:
    """
    Stops the boat horn sound.
    """
    #print("Stopping horn sound")
    newHorn.stop()
    
def playSplashFunc() -> None:
    """
    Plays the water splash sound.
    """
    NumSplashes = waterSplash.get_num_channels()
    if NumSplashes > 1:
        waterSplash.set_volume(min(weightedAverage((pygame.mouse.get_pos()[0] - splashButton.x) / splashButton.width,
                                               waterSplash.get_volume(), 0.6), 
                                   0.9)) # This is the maximum volume for the splash sound
    else:
        waterSplash.set_volume(min((pygame.mouse.get_pos()[0] - splashButton.x) / splashButton.width, 1))
    if NumSplashes < 5:
        waterSplash.play()

# Create button objects



hornButton = squircleButton(DISPLAYSURF, [scenes["default"]], 50, 50, 
                            SCREEN_WIDTH - 100, 300,
                            text="Horn", myFont=hornFont, textColor=pygame.Color(0, 0, 0, 255), 
                            borderColor=pygame.Color(0, 0, 0, 255), fillColor=pygame.Color(140, 140, 140, 255),
                            borderRadius = 100, onClickFunction=playHornFunc)
hornButton.onReleaseFunction = stopHornFunc
hornButton.clickedImage = hornButton.redraw(fillColor=pygame.Color(100, 100, 100, 255))

splashButton = squircleButton(DISPLAYSURF, [scenes["default"]], 50, hornButton.y + hornButton.height + 50, 
                            SCREEN_WIDTH - 100, 300,
                            text="Splash", myFont=hornFont, textColor=pygame.Color("#FFFFFF"), 
                            borderColor=pygame.Color("#000000"), fillColor=pygame.Color("#2624B4"),
                            borderRadius = 100, onClickFunction=playSplashFunc)
splashButton.clickedImage = splashButton.redraw(fillColor="#071350")


buttons = [hornButton,splashButton]

#Unicorn stuff

semitonesList = [-1, 0, 2, 4, 6, 13, 16, 20]
semitoneSectionWidth = hornButton.width / len(semitonesList)  # Calculate the width of each semitone segment



# Setup TPrint stuff
hornExtraText = TextPrint()
hornExtraText.reset()
hornExtraText.font1 = pygame.font.Font(None, 25)
hornExtraText.color = pygame.Color("#000000")
SplashExtraText = TextPrint()
SplashExtraText.reset()
SplashExtraText.font1 = pygame.font.Font(None, 70)
SplashExtraText.color = pygame.Color("#FFFFFF")
splashButtonText = "Quiet        <--             -->        Loud"
SplashExtraText.x = int(splashButton.x + int(splashButton.width/2) - SplashExtraText.font1.size(splashButtonText)[0]/2)
SplashExtraText.y = splashButton.y + splashButton.height - SplashExtraText.font1.size(splashButtonText)[1] - 25
FPSPrinter = TextPrint()
FPSPrinter.reset()
FPSPrinter.font1 = pygame.font.Font(None, 20)
FPSPrinter.x = 10
FPSPrinter.y = 10

# Control which events are allowed on the queue
pygame.event.set_allowed((pygame.QUIT, pygame.KEYDOWN, pygame.WINDOWCLOSE,
                          pygame.WINDOWFOCUSGAINED, pygame.WINDOWFOCUSLOST, 
                          pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP))

#credits
DISPLAYSURF.fill("#202020")
creditsText = TextPrint()
creditsText.font1 = pygame.font.Font(None, 50)
creditsText.color = pygame.Color("#FFFFFF")

creditsText.line_height = creditsText.font1.get_height() + 20

creditsText.x = int(creditsText.line_height)
creditsText.y = int(SCREEN_HEIGHT - creditsText.line_height * 6)

creditsText.tprint(DISPLAYSURF, 
"""Contributed by CPO1 Miller, Oliver
    Chief Bosun's Mate, RCSCC Undaunted 2025

Support:
https://github.com/OliverMMiller/DCSAlarmPanel""", moveDown=True)
pygame.display.update()
time.sleep(4)
del creditsText

# Main control loop
while __name__ == "__main__":
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
            for thisButton in buttons:
                if thisButton.myRect.collidepoint(event.pos):
                    if not thisButton.ignoreNextPress:
                        if not thisButton.alreadyPressed or not thisButton.runFuncOnce:
                            thisButton.alreadyPressed = True
                            if thisButton.onClickFunction is not None:
                                thisButton.onClickFunction()
        elif event.type == pygame.MOUSEBUTTONUP:
            for thisButton in buttons:
                thisButton.alreadyPressed = False
                if thisButton.onReleaseFunction is not None:
                        thisButton.onReleaseFunction()

    if nightMode:
        DISPLAYSURF.fill("#202525")  # set background colour to night mode
    else:
        DISPLAYSURF.fill("#d0d0d0")  # set background colour to day mode

    # renders button
    for thisButton in buttons:
        thisButton.process(None)

    for i in range(len(semitonesList)-1):
        hornExtraText.x = int((i+1) * semitoneSectionWidth + hornButton.x)
        hornExtraText.y = hornButton.y + 4
        hornExtraText.tprint(DISPLAYSURF, "|", moveDown=False)
        hornExtraText.y = hornButton.y + hornButton.height - hornExtraText.font1.size("Horn")[1] - 4
        hornExtraText.tprint(DISPLAYSURF, "|", moveDown=False)
    
    SplashExtraText.tprint(DISPLAYSURF, splashButtonText, moveDown=False)


    # FPSPrinter.tprint(DISPLAYSURF, F"FPS: {round(FramePerSec.get_fps(), 1)} ")
    # FPSPrinter.tprint(DISPLAYSURF, F"                     mspt:{FramePerSec.get_time()} ")

    # render frame at the right time
    pygame.display.update()
    FramePerSec.tick(FPS)