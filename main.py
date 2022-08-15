from panda3d.core import loadPrcFileData

conf = """
#win-size 1920 1080
win-size 1280 720
win-fixed-size 1
window-title My Game
show-frame-rate-meter 1
textures-power-2 none
#fullscreen true
"""

loadPrcFileData("", conf)

from direct.interval.IntervalGlobal import Sequence, Func, LerpFunctionInterval
from direct.interval.ParticleInterval import ParticleInterval
from direct.particles.ParticleEffect import ParticleEffect
from direct.showbase.ShowBase import ShowBase
from direct.actor.Actor import Actor
from direct.gui.OnscreenText import OnscreenText
from direct.gui.OnscreenImage import OnscreenImage
from direct.gui.DirectGui import DirectButton, DGG, DirectFrame
from direct.showbase.Transitions import Transitions
from panda3d.core import PointLight, CollisionNode, CollisionTraverser, CollisionHandlerQueue, CollisionSegment, WindowProperties, TransparencyAttrib, TextNode
from random import random, randint
import GlobalInstance
from base_objects import *
import sys

import simplepbr

DAD_LEVEL = 8
DAD_MOVEPATTERN = (
    # The first room. Will not come back here
    ("Smoking Room", (-5, 22, 0), (0, 0, 0)),
    # These are the rooms which dad moves around randomly before going to the last room
    ("Dining Room", (-8, 12, 0), (0, 0, 0)),
    ("Baby Room", (-14, 7, 0), (0, 0, 0)),
    ("Right Hall", (5, 5, 0), (0, 0, 0)),
    ("Main Hall", (5, 9, 0), (0, 0, 0)),
    ("Break Room", (2, 5, 0), (0, 0, 0)),
    # The last room. After this room is when dad attacks the player. Unless the player closes the left door
    # This also has information about the jumpscare, camera pos, hpr & dad pos, hpr
    ("Left Hall", (-5, 5, 0), (0, 0, 0), (1, 0, 2.5), (90, -10, 0), (-3.5, 0, 0), (90, 0, 0)),
)
#DAD_MOVEMENT_TIME = (12, 1, 2, 3, 4, 5, 6, 7)
DAD_MOVEMENT_TIME = (3, 4, 5, 6, 7)

#MUM_LEVEL = 3
MUM_LEVEL = 9
MUM_MOVEPATTERN = (
    ("Kitchen", (4, 14, 0), (0, 0, 0)),

    ("Dining Room", (-5, 16, 0), (0, 0, 0)),
    ("Baby Room", (-16, 10, 0), (0, 0, 0)),
    ("Smoking Room", (-9, 22, 0), (40, 0, 0)),
    ("Main Hall", (2, 9, 0), (0, 0, 0)),
    ("Break Room", (0, 5, 0), (-60, 20, -10)),
    ("Left Hall", (-5, 0, 0), (90, 0, 0)),
    ("East Hall", (-10, 4, 0), (180, 0, 0)),

    ("Right Hall", (5, 5, 0), (0, 0, 0), (-1, 0, 2.5), (-90, -10, 0), (3.5, 0, 0), (-90, 0, 0)),
)
#MUM_MOVEMENT_TIME = (5, 6, 7)
MUM_MOVEMENT_TIME = (12, 1, 2, 3, 4, 5, 6, 7)

NIGHT = 1

leverPos = (-0.984056, 3.67174, 2.49041)

file_config = {
    'rollerDoor': "roller_door",
    'leftDoor': "left_door",
    'rightDoor': "right_door",
    'window': "window",

    'rollerDoorSounds': {
        "open": "roller_door_open.ogg",
        "close": "roller_door_close.ogg"
    },
    'leftDoorSounds': {
        "open": "",
        "close": ""
    },
    'rightDoorSounds': {
        "open": "",
        "close": ""
    },
    'windowSounds': {
        "open": "",
        "close": ""
    },

    'buttonSounds': {
        'on': "button_on.ogg",
        'off': "button_off.ogg"
    },

    'leverSounds': {
        'on': "lever_on.ogg",
        'off': "lever_off.ogg"
    },

    'doorTex': {
        "on": "door_on.png",
        "off": "door_off.png"
    },
    'lightTex': {
        "on": "light_on.png",
        "off": "light_off.png"
    },
    'lightSounds': 'lights.ogg',
}
filenames = {}
for k, v in file_config.items():
    if k.endswith("Sounds"):
        v = {t: getSound(i) for t, i in v.items()} if type(v) == dict else getSound(v)
    elif k.endswith("Tex"):
        v = {t: getGui(i) for t, i in v.items()} if type(v) == dict else getGui(v)
    else:
        v = {t: getModel(i) for t, i in v.items()} if type(v) == dict else getModel(v)
    filenames[k] = v





class MyGame(ShowBase):
    def __init__(self):
        super().__init__()
        self.set_background_color(0, 0, 0, 0)
        self.pipeline = simplepbr.init()
        self.disableMouse()
        #self.oobe()

        pl = PointLight("pl")
        pn = self.render.attachNewNode(pl)
        pn.setPos(0, 0, 8)
        self.render.setLight(pn)

        self.night = NIGHT
        GlobalInstance.GameObject['base'] = self

        # Load the environment model and various door/window models
        self.environment = self.loader.loadModel(getModel("map"))
        self.environment.reparentTo(self.render)

        Clock.NIGHT = NIGHT


        # Load the button models
        rightDoorButton = DoorButton(
            "right_door_button",
            "rightDoor",
            (3.67, -1.3, 2.27),
            sounds = filenames['buttonSounds'],
            doorActor = Actor(
                filenames['rightDoor']
            ),
            #doorSounds = filenames['']
            tex=filenames['doorTex']
        )
        
        rightPlight = PointLight("rightPlight")
        rightPlight.setColor((0.2, 0.2, 0.2, 0.4))
        rightPlight.attenuation = (0.1, 0, 0.1)
        rightPlnp = self.render.attachNewNode(rightPlight)
        rightPlnp.setPos(5.3, 5, 6)
        self.render.setLight(rightPlnp)
        
        rightLightButton = DoorButton(
            "right_light_button",
            "rightLight",
            (3.67, -1.3, 1.83),
            tex=filenames['lightTex'],
            plight=rightPlnp
        )
        self.rightLightFlicker = LightFlicker(rightLightButton, filenames['lightSounds'])

        leftDoorButton = DoorButton(
            "left_door_button",
            "leftDoor",
            (-3.64, -1.27, 2.27),
            sounds = filenames['buttonSounds'],
            doorActor = Actor(
                filenames['leftDoor']
            ),
            #doorSounds = filenames['']
            tex=filenames['doorTex']
        )

        leftPlight = PointLight("leftPlight")
        leftPlight.setColor((0.2, 0.2, 0.2, 0.4))
        leftPlight.attenuation = (0.1, 0, 0.1)
        leftPlnp = self.render.attachNewNode(leftPlight)
        leftPlnp.setPos(-5.3, 5, 6)
        self.render.setLight(leftPlnp)
        
        leftLightButton = DoorButton(
            "left_light_button",
            "leftLight",
            (-3.64, -1.27, 1.83),
            tex=filenames['lightTex'],
            plight=leftPlnp,
        )
        self.leftLightFlicker = LightFlicker(leftLightButton, filenames['lightSounds'])

        rollerLever = DoorButton(
            "roller_lever",
            "rollerDoor",
            (0.37, 0, 0.07),
            (0, 0.14, 0.02, 0.26),
            True,
            filenames['leverSounds'],
            doorActor = Actor(
                filenames['rollerDoor']
            ),
            doorSounds = filenames['rollerDoorSounds'],
            modelPos = leverPos
        )

        windowLever = DoorButton(
            "window_lever",
            "window",
            (-0.35, 0, 0.05),
            (0, 0.14, 0.02, 0.26),
            True,
            filenames['leverSounds'],
            doorActor = Actor(
                filenames['window']
            ),
            #doorSounds = filenames[''],
            modelPos = leverPos
        )

        self.buttonMap = {
            'rightDoor': rightDoorButton,
            'leftDoor': leftDoorButton,
            'rollerDoor': rollerLever,
            'window': windowLever,
            'rightLight': rightLightButton,
            'leftLight': leftLightButton
        }


        self.enableParticles()

        self.music = self.loader.loadMusic(getSound("bg_music.ogg"))
        self.music.setVolume(0.1)
        self.music.setLoop(True)


        # Animatronics

        self.dad = Character(
            "dad",
            #{"jump": "moan.ogg"},
            {"jumpscare": "jully_jumpscare.ogg"},
            DAD_MOVEMENT,
            DAD_LEVEL,
            DAD_MOVEMENT_TIME
        )

        #self.dad.movePattern


        self.mum = Character(
            "mum",
            #{"jump": "moan.ogg"},
            {"jumpscare": "jully_jumpscare.ogg"},
            #MUM_MOVEPATTERN,
            MUM_MOVEMENT,
            MUM_LEVEL,
            MUM_MOVEMENT_TIME
        )

        #self.mum.movePattern


        self.joshNoise = self.loader.loadSfx(getSound("oh_no.ogg"))
        self.plsEnemies = self.loader.loadSfx(getSound("pls_enemies.ogg"))
        self.weirdNoise = self.loader.loadSfx(getSound("weird_noise.ogg"))
        self.weirdNoiseTimer = Timer(randint(10,100))

        self.stompingNoise = self.loader.loadSfx(getSound("fast_stomping.ogg"))

        # Create a PointLight
        plight = PointLight("plight") 
        plight.setColor((0.8, 0.15, 0.0, 0.9))
        plight.attenuation = (0.1, 0, 0.15)
        plnp = self.render.attachNewNode(plight)
        plnp.setPos(0, 0, 5)
        #self.render.setLight(plnp)
        #self.roomLight = plnp

        # Doesn't work with simplepbr
        #self.render.setShaderAuto()


        
        # Room lights
        roomLights = (
            # (colour, attenuation, position)
            ((0.8, 0.15, 0.0, 0.9), (1, 0, 0.2), (-6, 16, 4)),
        )
        '''
        {
            "office": ((0, 0, 2.5), (0, 0, 0)),
            "Dining Room": [(-1, 7.5, 3), (80, -10, 0), (10, -10, 0), randint(10,80), randint(0,1)],
            "Main Hall": [(1, 9, 3), (-90, -10, 0), (-120, -10, 0), randint(-120,-90), randint(0,1)],
            "Left Hall": [(-7, 0, 3.5), (0, -20, 0), (-40, -20, 0), randint(-40,0), randint(0,1)],
            "Right Hall": [(7, 0, 3.5), (40, -20, 0), (0, -20, 0), randint(0,40), randint(0,1)],
            "Break Room": [(-2, 4.5, 3), (-50, -10, 0), (-80, 10, 0), randint(-80,-50), randint(0,1)],
            "East Hall": [(10, 11, 3), (-150, -10, 0), (-200, -10, 0), randint(-200,-150), randint(0,1)],
            "Baby Room": [(-16, 5.5, 3), (0, -10, 0), (-70, -10, 0), randint(-70,0), randint(0,1)],
            "Kitchen": [(6, 17, 3.5), (160, -20, 0), (100, -20, 0), randint(100,160), randint(0,1)],
            "Smoking Room": [(-12, 18, 3), (0, -10, 0), (-100, -10, 0), randint(-100,0), randint(0,1)],
            "Shed": [(-19, 23, 3.5), (-90, -20, 0), (-180, -20, 0), randint(-180,-90), randint(0,1)],
            "Front Door": [(-12, 12.5, 3), (70, -30, 0), (0, -30, 0), randint(0,70), randint(0,1)]
        }
        leftPlight = PointLight("leftPlight")
        leftPlight.setColor((0.2, 0.2, 0.2, 0.4))
        leftPlight.attenuation = (0.1, 0, 0.1)
        leftPlnp = self.render.attachNewNode(leftPlight)
        leftPlnp.setPos(-5.3, 5, 6)
        self.render.setLight(leftPlnp)'''
        
        for lightMap in roomLights:
            lightNode = PointLight("leftPlight")
            lightNode.setColor(lightMap[0])
            lightNode.attenuation = lightMap[1]
            lightPlnp = self.render.attachNewNode(lightNode)
            lightPlnp.setPos(lightMap[2])
            #self.render.setLight(lightPlnp)
        


        # Collision segment starting from the camera position and extending out to Y15 relative to 'self.camera' ('base.camera')
        segment = CollisionSegment(0, 0, 0, 0, 15, 0)
        segNode = CollisionNode("segment")
        segNode.add_solid(segment)
        segNp = self.camera.attachNewNode(segNode)
        #segNp.show()

        # Creating CollisionTraverser object and showing for debug
        self.cTrav = CollisionTraverser('segment-to-button')
        #self.cTrav.showCollisions(self.render)

        self.queue = CollisionHandlerQueue()
        self.cTrav.addCollider(segNp, self.queue)
        self.cTrav.traverse(self.render)


        # camModel is only used for camera animation. Use self.camera for camera manipulation
        self.camModel = Actor(getModel("camera"))
        self.camModel.reparentTo(self.render)
        joint = self.camModel.exposeJoint(None, "modelRoot", "Bone")
        self.camera.reparentTo(joint)


        # Puts the cursor image onscreen
        self.cursor = OnscreenImage(getGui("cursor.png"), scale=0.01)
        self.cursor.setTransparency(TransparencyAttrib.MAlpha)
        self.cursor.hide()

        self.cursorHover = OnscreenImage(getGui("cursor_hover.png"), scale=0.03)
        self.cursorHover.setTransparency(TransparencyAttrib.MAlpha)
        self.cursorHover.hide()


        self.camStaticVid = VideoEffect("cam static screen", "fullscreen card", "static-cam_new.avi")
        self.camStaticVid.stop()

        self.screenTransition = Transitions(self.loader)
        self.gameOverScreen = OnscreenImage(getGui("game_over_screen.png"), scale=(1.8, 0, 1), parent=self.aspect2d)
        self.gameOverScreen.setTransparency(TransparencyAttrib.MAlpha)

        self.mapFrame = DirectFrame(
            frameSize = (-0.5, 0.5, -0.5, 0.5),
            pos = (-0.8, 0, 0.8),
            parent = self.a2dBottomRight,
            frameColor=(0,0,0,0)
        )

        mapImage = OnscreenImage(getGui("map/map4.png"), scale=(0.8, 0, 0.6), parent=self.mapFrame)
        mapImage.setTransparency(TransparencyAttrib.MAlpha)

        self.mapText = OnscreenText(text="", pos=(0.5, 1, 0), fg=(1, 1, 1, 1), parent=self.mapFrame)

        mapBtns = {
            "btn1": ("Left Hall", (-0.35, 0, -0.4)),
            "btn2": ("Right Hall", (0.35, 0, -0.4)),
            "btn3": ("Break Room", (-0.1, 0, -0.2)),
            "btn4": ("Main Hall", (0.1, 0, 0)),
            "btn5": ("Dining Room", (-0.12, 0, -0.03)),
            "btn6": ("East Hall", (0.55, 0, 0.1)),
            "btn7": ("Baby Room", (-0.7, 0, -0.1)),
            "btn8": ("Kitchen", (0.2, 0, 0.3)),
            "btn9": ("Smoking Room", (-0.45, 0, 0.38)),
            "btn10": ("Shed", (-0.8, 0, 0.4)),
            "btn11": ("Front Door", (-0.55, 0, 0.2))
        }

        for btnName, info in mapBtns.items():
            _ = DirectButton(
                command = lambda room=info[0]: self.cameraTo(room),
                frameTexture = (
                    getGui("buttons/"+btnName+".png"),
                    getGui("buttons/"+btnName+"_click.png"),
                    getGui("buttons/"+btnName+"_rollover.png")
                ),
                frameSize = (-0.06, 0.15, -0.06, 0.1),
                pos = info[1],
                relief = DGG.FLAT,
                parent = self.mapFrame
            ).setTransparency(TransparencyAttrib.MAlpha)
        
        self.mapFrame.hide()

        self.gameClock = Clock()
        self.battery = Battery()

        textNode = TextNode('gameOverText')
        font = self.loader.loadFont("assets/font/five-nights-at-freddys.ttf")
        font.setPixelsPerUnit(240)
        textNode.setFont(font)
        textNode.setText("GAME OVER")
        textNode.setAlign(TextNode.ACenter)
        textNode.setSlant(0.1)
        textNode.setTextColor(255, 0, 0, 1)
        textNode.setShadow(0.05, 0.05)
        self.gameOverText = self.aspect2dp.attachNewNode(textNode)
        self.gameOverText.setScale(0.2)


        # Accept keyboard events
        self.accept("f11", self.toggleFullscreen)
        self.accept("escape", sys.exit)
        self.accept("mouse1", self.mouseClick)
        self.accept("c", self.toggleCamera)

        # Runs update method every frame
        self.taskMgr.add(self.update, "update")

        self.start()
    

    # starts the game
    def start(self):
        self.camera.setPos(0, 0, 2.5)
        self.camera.setHpr(0, 0, 0)
        self.camModel.pose("shake", 0)

        # security camera controls
        self.camPos = {
            "office": ((0, 0, 2.5), (0, 0, 0)),
            "Dining Room": [(-1, 7.5, 3), (80, -10, 0), (10, -10, 0), randint(10,80), randint(0,1)],
            "Main Hall": [(1, 9, 3), (-90, -10, 0), (-120, -10, 0), randint(-120,-90), randint(0,1)],
            "Left Hall": [(-7, 0, 3.5), (0, -20, 0), (-40, -20, 0), randint(-40,0), randint(0,1)],
            "Right Hall": [(7, 0, 3.5), (40, -20, 0), (0, -20, 0), randint(0,40), randint(0,1)],
            "Break Room": [(-2, 4.5, 3), (-50, -10, 0), (-80, 10, 0), randint(-80,-50), randint(0,1)],
            "East Hall": [(10, 11, 3), (-150, -10, 0), (-200, -10, 0), randint(-200,-150), randint(0,1)],
            "Baby Room": [(-16, 5.5, 3), (0, -10, 0), (-70, -10, 0), randint(-70,0), randint(0,1)],
            "Kitchen": [(6, 17, 3.5), (160, -20, 0), (100, -20, 0), randint(100,160), randint(0,1)],
            "Smoking Room": [(-12, 18, 3), (0, -10, 0), (-100, -10, 0), randint(-100,0), randint(0,1)],
            "Shed": [(-19, 23, 3.5), (-90, -20, 0), (-180, -20, 0), randint(-180,-90), randint(0,1)],
            "Front Door": [(-12, 12.5, 3), (70, -30, 0), (0, -30, 0), randint(0,70), randint(0,1)]
        }

        self.camH = 0
        self.camTurning = False
        self.lastCam = 'Dining Room'

        
        self.music.play()
        self.weirdNoiseTimer.reset(randint(10,100))


        for btn in self.buttonMap.values():
            if btn.closed:
                btn.toggle(sound=False)



        # dad
        self.dad.start()
        
        self.mum.start()
        
        #self.dad.model.loop("idle")
        #self.mum.model.loop("idle")

        
        self.cursor.show()
        self.cursorHover.hide()
        self.camStaticVid.stop()
        self.mapFrame.hide()
        self.gameOverText.hide()

        self.gameClock.reset()
        self.battery.reset()

        #self.roomLight.node().setColor((0.8, 0.15, 0.0, 0.9))

        self.screenTransition.noFade()
        self.gameOverScreen.hide()

        # In-game variables
        self.inGame = False
        self.isGameOver = False
        self.fullscreen = False
        self.onCams = False
        self.lastMouseX, self.lastMouseY = None, None
        self.rotateH, self.rotateP = 0, 0
    

    # toggles security camera on or off
    def toggleCamera(self):
        if self.isGameOver or self.camStaticVid.isPlaying():
            return
        if self.inGame:
            self.camLens.setNear(0.1)
            self.cursor.hide()
            self.cursorHover.hide()
            self.mapFrame.show()
            camName = self.lastCam
        elif self.onCams:
            self.camLens.setNear(1)
            self.mapFrame.hide()
            camName = 'office'
        else:
            return
        self.onCams = not self.onCams
        self.cameraTo(camName)
        self.toggleIngame()
        

    # changes security camera
    def cameraTo(self, camTo):
        if self.isGameOver:
            return
        pos = self.camPos[camTo][0]
        hpr = self.camPos[camTo][1]

        if not self.camH or self.lastCam != camTo:
            if camTo != 'office':
                self.camH = self.camPos[camTo][3]
                self.camTurning = self.camPos[camTo][4]
                self.lastCam = camTo
                self.mapText.setText(camTo)
            
        self.camera.setPos(pos)
        self.camera.setHpr(hpr)
            

    # Toggles fullscreen
    def toggleFullscreen(self):
        self.fullscreen = not self.fullscreen

        wp = WindowProperties()
        wp.fullscreen = self.fullscreen
        if self.fullscreen:
            wp.size = (1920, 1080)
        else:
            wp.size = (1280, 720)
            wp.origin = (-2, -2)
            wp.fixed_size = True
        self.win.requestProperties(wp)


    # Toggles if player is in game
    def toggleIngame(self):
        if self.isGameOver:
            return
        self.inGame = not self.inGame

        wp = WindowProperties()
        wp.setCursorHidden(self.inGame)
        if self.inGame:
            wp.setMouseMode(WindowProperties.M_confined)
        else:
            wp.setMouseMode(WindowProperties.M_absolute)
        self.win.requestProperties(wp)
    

    # Recenters the cursor position
    def recenterCursor(self):
        self.win.movePointer(
            0,
            int(self.win.getProperties().getXSize() / 2),
            int(self.win.getProperties().getYSize() / 2)
        )
    

    # Method that gets called every time left mouse button is clicked
    def mouseClick(self):
        if self.isGameOver or self.camStaticVid.isPlaying():
            return
        if self.inGame:
            for entry in self.queue.entries:
                intoNp = entry.getIntoNodePath()
                name = intoNp.getName()
                button = self.buttonMap[name]
                
                if button.door:
                    openAnim = button.door.getAnimControl('open')
                    closeAnim = button.door.getAnimControl('close')
                    if openAnim.isPlaying() or closeAnim.isPlaying():
                        return
                
                #sparks = ParticleEffect()
                #sparks.loadConfig(getModel("sparks.ptf"))
                #sparks.setScale(0.1)
                #partInt = ParticleInterval(sparks, intoNp, duration=0.2, cleanup=True)
                #partInt.start()
                
                button.toggle()
        elif self.onCams:
            return
        else:
            self.toggleIngame()
    

    # Update method to run every frame
    def update(self, task):
        dt = self.taskMgr.globalClock.getDt()

        if self.isGameOver:
            return task.cont

        if random() < 0.00_001:
            self.joshNoise.play()

        if not self.onCams:
            if self.queue.entries:
                self.cursor.hide()
                self.cursorHover.show()
            else:
                self.cursorHover.hide()
                self.cursor.show()

        if self.inGame:
            mw = self.mouseWatcherNode
            if mw.hasMouse():
                x, y = mw.getMouseX(), mw.getMouseY()
                if self.lastMouseX is not None:
                    dx, dy = x, y
                else:
                    dx, dy = 0, 0
                self.lastMouseX, self.lastMouseY = x, y
            else:
                self.toggleIngame()
                x, y, dx, dy = 0, 0, 0, 0
            self.recenterCursor()
            self.lastMouseX, self.lastMouseY = 0, 0
            
            self.rotateH -= dx * dt * 1500
            self.rotateP += dy * dt * 1000

            if self.rotateP > 10:
                self.rotateP -= self.rotateP - 10
            elif self.rotateP < -20:
                self.rotateP -= self.rotateP + 20

            self.camera.setH(self.rotateH)
            self.camera.setP(self.rotateP)
        elif self.onCams:
            minH = self.camPos[self.lastCam][1][0]
            maxH = self.camPos[self.lastCam][2][0]

            if self.camH > minH:
                self.camTurning = False
            elif self.camH < maxH:
                self.camTurning = True
            
            if self.camTurning:
                self.camH += dt * 5
            else:
                self.camH -= dt * 5
            
            self.camPos[self.lastCam][3] = self.camH
            self.camPos[self.lastCam][4] = self.camTurning
            self.camera.setH(self.camH)
        


        if self.weirdNoiseTimer.timeIsUp():
            self.weirdNoise.play()
            self.weirdNoiseTimer.reset(randint(10,100))



        self.gameClock.update()
        self.battery.update()

        self.camStaticVid.update()
        self.leftLightFlicker.update()
        self.rightLightFlicker.update()

        self.dad.update()
        self.mum.update()

        return task.cont
        



if __name__ == "__main__":
    game = MyGame()
    game.run()