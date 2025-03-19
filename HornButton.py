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
SCREEN_WIDTH = 1080
SCREEN_HEIGHT = 720
DISPLAYSURF = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), (pygame.FULLSCREEN | pygame.SCALED))  # | pygame.NOFRAME  pygame.RESIZABLE
pygame.display.set_caption('Horn Button')

# Setting up mixer
pygame.mixer.music.set_volume(1.00)
boatHorn = pygame.mixer.Sound("sound/BOATHorn_Horn of a ship 1.wav")
boatHorn.set_volume(1.00)

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

hornButton = squircleButton(DISPLAYSURF, [scenes["default"]], 50, 50, 
                            SCREEN_WIDTH - 100, SCREEN_HEIGHT - 100,
                            text="Horn", myFont=hornFont, textColor=pygame.Color(0, 0, 0, 255), 
                            borderColor=pygame.Color(0, 0, 0, 255), fillColor=pygame.Color(140, 140, 140, 255),
                            borderRadius = 100, onClickFunction=playHornFunc)
hornButton.onReleaseFunction = stopHornFunc
hornButton.clickedImage = hornButton.redraw(fillColor=pygame.Color(100, 100, 100, 255))


# Setup TPrint stuff
fixesAlarmPrinter = TextPrint()
fixesAlarmPrinter.reset()
FPSPrinter = TextPrint()
FPSPrinter.reset()
FPSPrinter.font1 = pygame.font.Font(None, 20)
FPSPrinter.x = 10
FPSPrinter.y = 10

# Control which events are allowed on the queue
pygame.event.set_allowed((pygame.QUIT, pygame.KEYDOWN, pygame.WINDOWCLOSE,
                          pygame.WINDOWFOCUSGAINED, pygame.WINDOWFOCUSLOST, 
                          pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP))

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
            hornButton.onClickFunction()
        elif event.type == pygame.MOUSEBUTTONUP:
            hornButton.onReleaseFunction()

    if nightMode:
        DISPLAYSURF.fill("#202525")  # set background colour to night mode
    else:
        DISPLAYSURF.fill("#d0d0d0")  # set background colour to day mode

    # renders button
    hornButton.process(None)

    # FPSPrinter.tprint(DISPLAYSURF, F"FPS: {round(FramePerSec.get_fps(), 1)} ")
    # FPSPrinter.tprint(DISPLAYSURF, F"                     mspt:{FramePerSec.get_time()} ")

    # render frame at the right time
    pygame.display.update()
    FramePerSec.tick(FPS)