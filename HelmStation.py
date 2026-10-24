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
resolutionMultiplier = 1
SCREEN_WIDTH = 1920 * resolutionMultiplier
SCREEN_HEIGHT = 1200 * resolutionMultiplier
DISPLAYSURF = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), (pygame.FULLSCREEN | pygame.SCALED))  # | pygame.NOFRAME  pygame.RESIZABLE
pygame.display.set_caption('DCS Alarm Panel')
needsRedraw = True


# Setting up mixer
pygame.mixer.music.set_volume(1.00)
Notify = pygame.mixer.Sound("sound/Notify.wav")
Notify.set_volume(0.5)
boatHorn = pygame.mixer.Sound("sound/shipHorn.wav")
boatHorn.set_volume(1.00)

# Set up logging
log_path = Path(__file__).with_name("MQTTlog.log")
log_formatter = logging.Formatter("%(asctime)s %(levelname)s %(message)s")

MQTTLogger = logging.getLogger("DCSAlarmPanel")
MQTTLogger.setLevel(logging.INFO)
MQTTLogger.propagate = False

rotating_handler = RotatingFileHandler(
    log_path,
    maxBytes=1_000_000,
    backupCount=3,
    encoding="utf-8",
)
rotating_handler.setFormatter(log_formatter)
MQTTLogger.addHandler(rotating_handler)

MQTTLogger.info("Starting DCS Alarm Panel")

#network queue for MQTT messages
network_queue = queue.Queue()

MQTT_Clear_json = {"DCSAlarm": False, "GeneralAlarm": False, "Acknowledge": False}

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
displayFPSInfo = True
executionStopwatch = 0.0

# Global variables
currentAlarm = None
AlarmTime = 6  # Minutes
ResetNext = False
nightMode = False
nextFix = time.localtime().tm_min + AlarmTime - 1 + (round(time.localtime().tm_sec / 60))
timeUntilNextFix = (60 - time.localtime().tm_min + nextFix) % 60
previousSeconds = -1
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
        self.font1 = pygame.font.Font(None, 90 * resolutionMultiplier)
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
        self.x = 50 * resolutionMultiplier
        self.y = 50 * resolutionMultiplier
        self.line_height = 80 * resolutionMultiplier
        
#Show credits while loading the program
DISPLAYSURF.fill("#202020")
creditsText = TextPrint()
creditsText.font1 = pygame.font.Font(None, 40 * resolutionMultiplier)
creditsText.color = pygame.Color("#FFFFFF")

creditsText.line_height = creditsText.font1.get_height() + 10 * resolutionMultiplier

creditsText.x = int(creditsText.line_height)
creditsText.y = int(SCREEN_HEIGHT) - (creditsText.line_height * 6)

creditsText.tprint(DISPLAYSURF, 
"""Contributed by CPO1 Miller, Oliver
    Chief Bosun's Mate, RCSCC Undaunted 2025

Support:
https://github.com/OliverMMiller/DCSAlarmPanel""", moveDown=True)
pygame.display.update()
del creditsText

class alarmObj:
    """
    Class to represent an alarm object.
    """
    def __init__(self, alarmButton: button, alarmSound: pygame.mixer.Sound, MQTT_Alarm: dict[str, bool] | None = None) -> None:
        self.alarmButton = alarmButton
        self.alarmSound = alarmSound
        self.MQTT_Alarm = MQTT_Alarm

    def playAlarm(self, dontPublish: bool = False) -> None:
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
            
        if self.MQTT_Alarm and not dontPublish:
            MQTT_Client.publish("ShipSim/Alarm", json.dumps(self.MQTT_Alarm, indent=4), retain=True)

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
        
    MQTT_Client.publish("ShipSim/Alarm", json.dumps(MQTT_Clear_json, indent=4), retain=True,)

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

def resetFixesAlarm() -> None:
    """
    Resets the fixes alarm timer.
    """
    global nextFix
    nextFix = (time.localtime().tm_min + max(AlarmTime - 1, 0) + (round((seconds + 2) / 60))) % 60

def checkFixesAlarm() -> None:
    """
    Checks and updates the fixes alarm timer.
    """
    global nextFix
    global timeUntilNextFix
    global ResetNext
    mins = time.localtime().tm_min
    if timeUntilNextFix == 0 and seconds == 59:
        ResetNext = True
    elif ResetNext and seconds == 0:  # Checks if timer needs to be reset
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

        # Package everything neatly for your Pygame loop
        queue_item = {
            "topic": msg.topic,
            "data": payload_data
        }
        
        # Drop it into the queue. Pygame will safely pick it up on its next frame.
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
alarmButtonWidth = int(SCREEN_WIDTH / 3 - 2 * 30)
alarmButtonY = int(SCREEN_HEIGHT / 2 - alarmButtonWidth / 2)

quitButton = button(DISPLAYSURF, [scenes["default"], scenes["acknowledge"]], SCREEN_WIDTH - 230 * resolutionMultiplier, 30 * resolutionMultiplier, 
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
                        hoverImage=pygame.image.load("images/DCS-Gray.png").convert_alpha())

GeneralAlarmButton = button(DISPLAYSURF, [scenes["default"]], 
                            30 * 3 + alarmButtonWidth, alarmButtonY, 
                            alarmButtonWidth, alarmButtonWidth, 
                            defaultImage=pygame.image.load("images/General-red.png").convert_alpha(),
                            hoverImage=pygame.image.load("images/General-Gray.png").convert_alpha())

HalifaxActionAlarmButton = button(DISPLAYSURF, [scenes["default"]], 
                                  30 * 4 + alarmButtonWidth * 2, alarmButtonY, 
                                  alarmButtonWidth, alarmButtonWidth,
                                  defaultImage=pygame.image.load("images/Action-red.png").convert_alpha(),
                                  hoverImage=pygame.image.load("images/Action-Gray.png").convert_alpha())

acknowledgeSize: tuple[int, int] = (int(60 * 1.7 * resolutionMultiplier), int(80 * 1.7 * resolutionMultiplier))
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

# define alarm objects
DCSAlarmObj = alarmObj(DCSAlarmButton, DCSAlarm, {"DCSAlarm": True, "GeneralAlarm": False, "Acknowledge": False})
GeneralAlarmObj = alarmObj(GeneralAlarmButton, GeneralAlarm, {"DCSAlarm": False, "GeneralAlarm": True, "Acknowledge": False})
HalifaxActionAlarmObj = alarmObj(HalifaxActionAlarmButton, HalifaxActionAlarm)
#add on-click function after defining alarm objects to avoid circular reference
HalifaxActionAlarmButton.onClickFunction = HalifaxActionAlarmObj.playAlarm
GeneralAlarmButton.onClickFunction = GeneralAlarmObj.playAlarm
DCSAlarmButton.onClickFunction = DCSAlarmObj.playAlarm

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
reattemptConnectionTimer: float = 0.0
    
# 5. Spin up the non-blocking background thread
# This manages network traffic completely independently of the graphics loop.
MQTT_Client.loop_start()

#show credits for minimum 4 seconds before starting main loop
#time.sleep(4)#####################################################################################################################################

#clear the event queue to avoid any queued events from before the program started
pygame.event.clear()


# Main control loop
while __name__ == "__main__":
    if displayFPSInfo:
        executionStopwatch = time.perf_counter()

    #Handle non-network (user) events
    doubleClickBlacklist = []
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
            for thisIntractable in hasOnClickFunction:
                if thisIntractable not in doubleClickBlacklist and thisIntractable.myRect.collidepoint(event.pos):
                    thisIntractable.onClickFunction()
                    doubleClickBlacklist.append(thisIntractable)

            if event.touch == 1:
                displayFPSInfo = False
                if quitButton in scenes["default"]:
                    scenes["default"].remove(quitButton)
                    scenes["acknowledge"].remove(quitButton)
            else:
                scenes["default"].insert(0, quitButton)
                scenes["acknowledge"].insert(0, quitButton)
                quitButton.ignoreNextPress = True
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
                alarm_data = msg["data"]  # This is your parsed dictionary
                

                # Extract specific variables from the dictionary payload
                # DCSAlarm = alarm_data.get("DCSAlarm") 
                # DCSAlarmObj.playAlarm()
                # GeneralAlarm = alarm_data.get("GeneralAlarm")
                # Acknowledge = alarm_data.get("Acknowledge") 
                
                MQTTLogger.info("Processing network update for %s -> Data: %s", topic, alarm_data)
                
                if alarm_data.get("Acknowledge") is True:
                    stopAlarm()
                elif alarm_data.get("DCSAlarm") is True:
                    DCSAlarmObj.playAlarm(dontPublish=True)
                elif alarm_data.get("GeneralAlarm") is True:
                    GeneralAlarmObj.playAlarm(dontPublish=True)
                

        except queue.Empty:
            pass
        
        
    elif time.monotonic() - reattemptConnectionTimer > reattemptConnectionTime:
        reattemptConnectionTimer = time.monotonic()
        MQTTLogger.info("Connecting to broker at %s:%s", BROKER_IP, BROKER_PORT)
        try:
            MQTT_Client.connect_async(BROKER_IP, BROKER_PORT, KEEP_ALIVE_SECONDS)
        except TimeoutError as e:
            MQTTLogger.info(f"Failed to connect: {e}")

    # determines if fixes timer needs to be calculated and redrawn
    seconds = time.localtime().tm_sec
    if previousSeconds != seconds:
        checkFixesAlarm()
        needsRedraw = True
        previousSeconds = seconds



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


        # render fixes alarm time
        fixesAlarmPrinter.tprint(DISPLAYSURF, F"{timeUntilNextFix} : {60 - seconds - 1:02}")

        if displayFPSInfo:
            FPSPrinter.tprint(DISPLAYSURF, F"FPS: {round(FramePerSec.get_fps(), 1)} ")
            FPSPrinter.tprint(DISPLAYSURF, F"{'':25}mspt:{(time.perf_counter() - executionStopwatch)*1000:.0f} ")


        # render frame
        pygame.display.update()
        needsRedraw = False
    FramePerSec.tick(FPS)