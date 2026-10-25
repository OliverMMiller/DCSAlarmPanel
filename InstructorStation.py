# Imports
#general
import sys
import pygame
import time
from pathlib import Path
import logging
from logging.handlers import RotatingFileHandler
from typing import Callable
#pygame
from pygame.locals import QUIT
from OliversButtonModule import button as button
from OliversSquircleModule import squircle as squircle
from generateUniqueHornSound import pitch_shift
#network
import queue
import json
import paho.mqtt.client as mqtt
from paho.mqtt.enums import CallbackAPIVersion
from paho.mqtt import reasoncodes
    
    
# Initializing pygame and mixer
pygame.mixer.pre_init(frequency=48000, buffer=2048)
pygame.init()
pygame.mixer.init()


# Setting up screen
SCREEN_WIDTH = 1920
SCREEN_HEIGHT = 1200
DISPLAYSURF = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), (pygame.FULLSCREEN | pygame.SCALED ))  # | pygame.NOFRAME  pygame.RESIZABLE
myProgramName = "DCS Alarm Instructor Panel"
pygame.display.set_caption(myProgramName)
needsRedraw = True

# Setting up mixer
pygame.mixer.music.set_volume(1.00)
boatHorn = pygame.mixer.Sound("sound/shipHorn.wav")
boatHorn.set_volume(1.00)
newHorn = boatHorn
newHorn.set_volume(0.90)

waterSplash = pygame.mixer.Sound("sound/waterSplash.mp3")
waterSplash.set_volume(0.90)


# Set up logging
log_formatter = logging.Formatter(
    '%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
    datefmt='%m-%d %H:%M',
)

panel_handler = RotatingFileHandler(
    Path(__file__).with_name("panelLog.log"),
    maxBytes=1_000_000,
    backupCount=3,
    encoding="utf-8",
)
panel_handler.setLevel(logging.DEBUG)
panel_handler.setFormatter(log_formatter)
panel_handler.addFilter(
    lambda record: record.name != MQTTLogger.name or record.levelno >= logging.WARNING
)

console = logging.StreamHandler()
console.setLevel(logging.INFO)
console.setFormatter(logging.Formatter(
    '%(name)-12s %(levelname)-8s %(message)s'
))
console.addFilter(
    lambda record: record.name != MQTTLogger.name or record.levelno >= logging.WARNING
)

mqtt_handler = RotatingFileHandler(
    Path(__file__).with_name("MQTTlog.log"),
    maxBytes=1_000_000,
    backupCount=3,
    encoding="utf-8",
)
mqtt_handler.setLevel(logging.DEBUG)
mqtt_handler.setFormatter(log_formatter)

logging.basicConfig(
    level=logging.DEBUG,
    handlers=[panel_handler, console, mqtt_handler],
)

MQTTLogger = logging.getLogger("DCSAlarmPanel-MQTT")
MQTTLogger.setLevel(logging.INFO)
MQTTLogger.propagate = True

DEBUGMODE = False #################################################################

logging.info(f"Starting {myProgramName}")

#network queue for MQTT messages
network_queue = queue.Queue()

MQTT_Clear_json = {"DCSAlarm": False, "GeneralAlarm": False, "Acknowledge": False}

# Setting up fonts
hornFont = pygame.font.Font(None, 130)
alarmFont = pygame.font.Font("fonts/LiberationMono/LiberationMono-Bold.ttf", 90)
acknowledgeFont = pygame.font.Font(None, 90)
myFont = pygame.font.SysFont('Arial', 50)


# Images
image = {
    "toggleNightMode": pygame.image.load("images/ToggleDayMode_trimmed.png").convert_alpha(),
    "toggleDayMode": pygame.image.load("images/ToggleNightMode_trimmed.png").convert_alpha(),
}

# Setting up FPS
FPS = 60
FramePerSec = pygame.time.Clock()
displayFPSInfo = DEBUGMODE
executionStopwatch = 0.0

# Global variables
nightMode = False
fixesAlarmMuted = True
mousePos: tuple[int,int] = (0,0)

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
        
#Show credits while loading the program
DISPLAYSURF.fill("#202020")
creditsText = TextPrint()
creditsText.font1 = pygame.font.Font(None, 80)
creditsText.color = pygame.Color("#FFFFFF")

creditsText.line_height = creditsText.font1.get_height() + 10

creditsText.x = int(creditsText.line_height)
creditsText.y = int(SCREEN_HEIGHT) - (creditsText.line_height * 6)

creditsText.tprint(DISPLAYSURF, 
"""Contributed by CPO1 Miller, Oliver
    Chief Bosun's Mate, RCSCC Undaunted 2025

Support:
https://github.com/OliverMMiller/DCSAlarmPanel""", moveDown=True)
pygame.display.update()
del creditsText


class squircleButton(squircle, button):
    """
    Class to represent a button with a squircle shape.
    """
    def __init__(self, DISPLAYSURF: pygame.Surface, scenes: list, x: int, y: int, width: int, height: int,
                 text: str | None, myFont: pygame.font.Font | None, textColor: pygame.Color | None,
                 borderColor: pygame.Color | None, fillColor: pygame.Color | None,
                 onClickFunction: Callable | None,
                 borderRadius: int = 50, borderWidth: int = 3) -> None:
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
    MQTT_Client.disconnect()
    MQTTLogger.info("Disconnected due to program close")
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


def DCSAlarmButtonFunc():
    MQTT_Client.publish("ShipSim/Alarm", json.dumps({"Sender": myProgramName, "DCSAlarm": True, "GeneralAlarm": False, "Acknowledge": False}, indent=4))

def GeneralAlarmButtonFunc():
    MQTT_Client.publish("ShipSim/Alarm", json.dumps({"Sender": myProgramName, "DCSAlarm": False, "GeneralAlarm": True, "Acknowledge": False}, indent=4))

def AcknowledgeButtonFunc():
    MQTT_Client.publish("ShipSim/Alarm", json.dumps({"Sender": myProgramName, "DCSAlarm": False, "GeneralAlarm": False, "Acknowledge": True}, indent=4))
        




# def setIgnoreNextPress() -> None:
#     """
#     Used to prevent double activations on one click.
#     """
#     Acknowledge.ignoreNextPress = True
#     DCSAlarmButton.ignoreNextPress = True
#     GeneralAlarmButton.ignoreNextPress = True
#     resetFixTimeButton.ignoreNextPress = True

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


#Define MQTT Event Callbacks
def on_connect(client, userdata, flags, reason_code: reasoncodes.ReasonCode, properties):
    """Triggered automatically when the script successfully connects to Mosquitto."""

    if reason_code != 0:
        MQTTLogger.error("Connection failed (reason_code=%s): %s", reason_code)
        return
    MQTTLogger.info("Connected to Mosquitto Broker")
    
    result, mid = client.subscribe("ShipSim/Alarm/#")
    if result == mqtt.MQTT_ERR_SUCCESS:
        MQTTLogger.info("Requested subscription to ShipSim/Alarm/# (mid=%s)", mid)
    else:
        MQTTLogger.error("Subscription request failed with result code %s", result)
        
def on_connect_fail(client, userdata):
    """Triggered automatically when the client cannot connect to the broker."""
    MQTTLogger.warning("Failed to connect to Mosquitto Broker")

def on_disconnect(client, userdata, disconnect_flags, reason_code, properties):
    """Triggered automatically when the client disconnects from the broker."""
    if reason_code != 0:
        MQTTLogger.warning("Unexpected disconnection (reason_code=%s)", reason_code)
    else:
        MQTTLogger.info("Disconnected from Mosquitto Broker")

def on_subscribe(client, userdata, mid, reason_code_list, properties=None):
    """Triggered when the broker acknowledges a subscription request."""
    MQTTLogger.info(
        "Subscription acknowledged (mid=%s, result=%s)",
        mid,
        reason_code_list,
    )

def on_message(client, userdata, msg):
    """Triggered automatically whenever a message arrives on a subscribed topic."""
    MQTTLogger.info(
        "Received %s -> %s",
        msg.topic,
        msg.payload.decode("utf-8", errors="replace"),
    )

    try:
        # Decode bytes payload to string, then parse the JSON
        payload_str = msg.payload.decode('utf-8')
        payload_data = json.loads(payload_str)

        queue_item = {
            "topic": msg.topic,
            "data": payload_data
        }
        
        network_queue.put(queue_item)
        
    except json.JSONDecodeError:
        MQTTLogger.warning(
            "Received non-JSON payload on topic %s: %r",
            msg.topic,
            msg.payload,
        )
    except Exception as e:
        MQTTLogger.exception("Error handling incoming MQTT message: %s", e)


# Create button objects
buttonSpacing = 60

bottomButtonX = buttonSpacing*2
bottomButtonWidth = SCREEN_WIDTH - bottomButtonX*2
bottomButtonHeight = 225

alarmButtonWidth = int((SCREEN_WIDTH - 5*buttonSpacing) / 2.6 )
alarmButtonHeight = int(buttonSpacing * 5)
alarmButtonY = SCREEN_HEIGHT-bottomButtonHeight*2-alarmButtonHeight-buttonSpacing*4

topButtonY = 2*buttonSpacing
topButtonHeight = alarmButtonY - topButtonY - buttonSpacing

toggleNightModeButtonWidth = SCREEN_WIDTH - alarmButtonWidth*2 - bottomButtonX*2 - buttonSpacing*2


quitButton = button(DISPLAYSURF, [[],[scenes["default"], scenes["acknowledge"]]][DEBUGMODE],
                    SCREEN_WIDTH - 200 - buttonSpacing*2, buttonSpacing, 
                    200, 100, 
                    defaultImage=pygame.image.load("images/Quit.png").convert_alpha(), 
                    onClickFunction=quitFunc)

toggleNightModeButton = button(DISPLAYSURF, [scenes["default"], scenes["acknowledge"]],
                               SCREEN_WIDTH - toggleNightModeButtonWidth - buttonSpacing*2, alarmButtonY + int((toggleNightModeButtonWidth/4.72)),
                               toggleNightModeButtonWidth, int(toggleNightModeButtonWidth/1.72), 
                               defaultImage=image["toggleDayMode"], 
                               onClickFunction=toggleNightMode)

DCSAlarmButton = squircleButton(DISPLAYSURF, [scenes["default"]], 
                            buttonSpacing*2, alarmButtonY, 
                            alarmButtonWidth, alarmButtonHeight,
                            text="DCS\nAlarm", myFont=alarmFont, textColor=pygame.Color(0, 0, 0, 255), 
                            borderColor=pygame.Color(0, 0, 0, 255), fillColor=pygame.Color(170, 0, 0, 255),
                            onClickFunction=DCSAlarmButtonFunc,
                            borderRadius=75, borderWidth=5)
DCSAlarmButton.hoverImage = DCSAlarmButton.redraw(fillColor=pygame.Color(100, 100, 100, 255))

GeneralAlarmButton = squircleButton(DISPLAYSURF, [scenes["default"]], 
                            buttonSpacing * 3 + alarmButtonWidth, alarmButtonY, 
                            alarmButtonWidth, alarmButtonHeight, 
                            text="General\nAlarm", myFont=alarmFont, textColor=pygame.Color(0, 0, 0, 255), 
                            borderColor=pygame.Color(0, 0, 0, 255), fillColor=pygame.Color(170, 0, 0, 255),
                            onClickFunction=GeneralAlarmButtonFunc,
                            borderRadius=75, borderWidth=5)
GeneralAlarmButton.justificationType = "centered"
GeneralAlarmButton.hoverImage = GeneralAlarmButton.redraw(fillColor=pygame.Color(100, 100, 100, 255))

Acknowledge = squircleButton(DISPLAYSURF, [scenes["acknowledge"]], 
                            buttonSpacing*2, alarmButtonY, 
                            alarmButtonWidth*2 + buttonSpacing, alarmButtonHeight,
                        text="Acknowledge", myFont=acknowledgeFont, textColor=pygame.Color(0, 0, 0, 255), 
                        borderColor=pygame.Color(0, 0, 0, 255), fillColor=pygame.Color(225, 0, 0, 255),
                        onClickFunction=AcknowledgeButtonFunc,
                        borderRadius=75, borderWidth=5)

hornButton = squircleButton(DISPLAYSURF, [scenes["default"], scenes["acknowledge"]], 
                            bottomButtonX, SCREEN_HEIGHT-bottomButtonHeight-buttonSpacing*2, 
                            bottomButtonWidth, bottomButtonHeight,
                            text="Horn", myFont=hornFont, textColor=pygame.Color(0, 0, 0, 255), 
                            borderColor=pygame.Color(0, 0, 0, 255), fillColor=pygame.Color(140, 140, 140, 255),
                            borderRadius = 75, onClickFunction=playHornFunc)
hornButton.onReleaseFunction = stopHornFunc
hornButton.clickedImage = hornButton.redraw(fillColor=pygame.Color(100, 100, 100, 255))

splashButton = squircleButton(DISPLAYSURF, [scenes["default"], scenes["acknowledge"]], 
                            bottomButtonX, SCREEN_HEIGHT-bottomButtonHeight*2-buttonSpacing*3, 
                            bottomButtonWidth, bottomButtonHeight,
                            text="Splash", myFont=hornFont, textColor=pygame.Color("#FFFFFF"), 
                            borderColor=pygame.Color("#000000"), fillColor=pygame.Color("#2624B4"),
                            borderRadius = 75, onClickFunction=playSplashFunc)
splashButton.clickedImage = splashButton.redraw(fillColor="#071350")


buttons = [hornButton,splashButton]

semitonesList = [-1, 0, 2, 4, 6, 13, 16, 20]
semitoneSectionWidth = hornButton.width / len(semitonesList)  # Calculate the width of each semitone segment


# Setup TPrint stuff
hornExtraText = TextPrint()
hornExtraText.reset()
hornExtraText.font1 = pygame.font.Font("fonts/LiberationMono/LiberationMono-Bold.ttf", 30)
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
FPSPrinter.font1 = pygame.font.Font(None, 50)
FPSPrinter.x = 30
FPSPrinter.y = 30

# Control which events are allowed on the queue
pygame.event.set_allowed((pygame.QUIT, pygame.KEYDOWN, pygame.WINDOWCLOSE,
                          pygame.WINDOWFOCUSGAINED, pygame.WINDOWFOCUSLOST, 
                          pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP))


hasOnClickFunction: list = []
hasOnReleaseFunction: list = []
for object in scenes[scene]:
    if hasattr(object, "onClickFunction"):
        if object.onClickFunction:
            hasOnClickFunction.append(object)
            if hasattr(object, "onReleaseFunction"):
                if object.onReleaseFunction:
                    hasOnReleaseFunction.append(object)
                    
# 3. Configure and Initialize the MQTT Client
MQTT_Client = mqtt.Client(CallbackAPIVersion.VERSION2)

MQTT_Client.on_connect = on_connect
MQTT_Client.on_subscribe = on_subscribe
MQTT_Client.on_message = on_message
MQTT_Client.on_connect_fail = on_connect_fail
MQTT_Client.on_disconnect = on_disconnect


# 4. Establish Connection to MQTT Broker
BROKER_IP = "NTC-Operations-Room-PI"#"127.0.0.1"
BROKER_PORT = 1883
KEEP_ALIVE_SECONDS = 60
reattemptConnectionTime: float = 30.0
reattemptConnectionTimer: float = time.monotonic()
    
# Configure the broker before the network thread attempts its first reconnect.
MQTTLogger.info("Connecting to broker at %s:%s", BROKER_IP, BROKER_PORT)
MQTT_Client.connect_async(BROKER_IP, BROKER_PORT, KEEP_ALIVE_SECONDS)

# 5. Spin up the non-blocking background thread
# This manages network traffic completely independently of the graphics loop.
MQTT_Client.loop_start()

#show credits for minimum 4 seconds before starting main loop
time.sleep(4)#####################################################################################################################################

#clear the event queue to avoid any queued events from before the program started
pygame.event.clear()


# Main control loop
while __name__ == "__main__":
    if displayFPSInfo:
        executionStopwatch = time.perf_counter()

    #Handle non-network (user) events
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
        elif event.type == pygame.MOUSEMOTION:
            needsRedraw = True
            mousePos = event.pos
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            needsRedraw = True
            mousePos = event.pos
            for thisIntractable in hasOnClickFunction[::-1]:
                if thisIntractable.myRect.collidepoint(event.pos):
                    thisIntractable.onClickFunction()
                    break

            # if event.touch == 1:
            #     displayFPSInfo = False
            #     if quitButton in scenes["default"]:
            #         scenes["default"].remove(quitButton)
            #         scenes["acknowledge"].remove(quitButton)
            # else:
            #     scenes["default"].insert(0, quitButton)
            #     scenes["acknowledge"].insert(0, quitButton)
            #     quitButton.ignoreNextPress = True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            needsRedraw = True
            mousePos = event.pos
            for thisIntractable in hasOnReleaseFunction:
                if thisIntractable.myRect.collidepoint(event.pos):
                    thisIntractable.onReleaseFunction()

    #handle network events
    if MQTT_Client.is_connected():
        try:
            while not network_queue.empty():
                msg = network_queue.get_nowait()
                
                # Extract data components
                topic = msg["topic"]
                alarm_data = msg["data"]  #Parsed dictionary

                MQTTLogger.debug("Processing network update for %s -> Data: %s", topic, alarm_data)
                
                if (alarm_data.get("DCSAlarm") == False and alarm_data.get("GeneralAlarm") == False and alarm_data.get("Acknowledge") == False):
                    nextScene = "default"
                    needsRedraw = True
                elif alarm_data.get("DCSAlarm") == True:
                    nextScene = "acknowledge"
                    needsRedraw = True
                elif alarm_data.get("GeneralAlarm") == True:
                    nextScene = "acknowledge"
                    needsRedraw = True


        except queue.Empty:
            pass
        
        
    elif time.monotonic() - reattemptConnectionTimer > reattemptConnectionTime:
        reattemptConnectionTimer = time.monotonic()
        MQTTLogger.info("Connecting to broker at %s:%s", BROKER_IP, BROKER_PORT)
        try:
            MQTT_Client.connect_async(BROKER_IP, BROKER_PORT, KEEP_ALIVE_SECONDS)
        except TimeoutError as e:
            MQTTLogger.info(f"Failed to connect: {e}")



    if needsRedraw:# or displayFPSInfo:
        if nightMode:
            DISPLAYSURF.fill("#202525")  # set background colour to night mode
        else:
            DISPLAYSURF.fill("#d0d0d0")  # set background colour to day mode

        if scene != nextScene:
            scene = nextScene
            hasOnClickFunction: list = []
            hasOnReleaseFunction: list = []
            for object in scenes[scene]:
                if hasattr(object, "onClickFunction"):
                    if object.onClickFunction:
                        hasOnClickFunction.append(object)
                        if hasattr(object, "onReleaseFunction"):
                            if object.onReleaseFunction:
                                hasOnReleaseFunction.append(object)

        # renders all objects in the current scene
        for object in scenes[scene]:
            object.process(mousePos)

        for i in range(len(semitonesList)-1):
            hornExtraText.x = int((i+1) * semitoneSectionWidth + hornButton.x)
            hornExtraText.y = hornButton.y + 4
            hornExtraText.tprint(DISPLAYSURF, "|", moveDown=False)
            hornExtraText.y = hornButton.y + hornButton.height - hornExtraText.font1.size("Horn")[1] - 4
            hornExtraText.tprint(DISPLAYSURF, "|", moveDown=False)
    
        SplashExtraText.tprint(DISPLAYSURF, splashButtonText, moveDown=False)

        if displayFPSInfo:
            FPSPrinter.tprint(DISPLAYSURF, F"FPS: {round(FramePerSec.get_fps(), 1)} ")
            FPSPrinter.tprint(DISPLAYSURF, F"{'':25}mspt:{(time.perf_counter() - executionStopwatch)*1000:.0f} ")


        # render frame
        pygame.display.update()
        needsRedraw = False
    FramePerSec.tick(FPS)