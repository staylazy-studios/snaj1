from panda3d.core import CollisionBox, CollisionNode, MovieTexture, CardMaker, NodePath, TextNode, TransparencyAttrib
from direct.interval.IntervalGlobal import Sequence, Func, LerpFunctionInterval
from direct.gui.OnscreenImage import OnscreenImage
from direct.actor.Actor import Actor
from random import  uniform, choice, choices
import GlobalInstance

getModel = lambda f: "./new_assets/gltfs/"+f+".glb"
getGui   = lambda f: "./new_assets/gui/"+f
getSound = lambda f: "./new_assets/sounds/"+f

GI = GlobalInstance.GameObject

AI_LEVEL_CONFIG = ( # Index 0 should be None since levels go from 1 to 10. Just for readability
    None,
    (43, 50),
    (36, 43),
    (30, 36),
    (24, 30),
    (19, 24),
    (14, 19),
    (10, 14),
    (6, 10),
    (3, 6),
    (0, 3),
)


class Timer:
    def __init__(self, seconds):
        self.startAt = GI['base'].taskMgr.globalClock.getFrameTime()
        self.pauseAt = self.startAt
        self.paused = False
        self.seconds = seconds
        self.initSeconds = seconds
    def reset(self, newTime=None):
        self.startAt = GI['base'].taskMgr.globalClock.getFrameTime()
        self.paused = False
        if newTime:
            self.seconds = newTime
        else:
            self.seconds = self.initSeconds
    def timeIsUp(self):
        if self.paused: return False
        ft = GI['base'].taskMgr.globalClock.getFrameTime()

        secNow = ft - self.startAt
        if secNow >= self.seconds:
            return True
        else:
            return False
    def pause(self):
        self.pauseAt = GI['base'].taskMgr.globalClock.getFrameTime()
        self.paused = True
    def resume(self):
        resumeAt = GI['base'].taskMgr.globalClock.getFrameTime()
        self.seconds -= (self.pauseAt - self.startAt)
        self.startAt = resumeAt
        self.paused = False

class VideoEffect:
    def __init__(self, mtName, cmName, filename):
        tex = MovieTexture(mtName)
        tex.read(getGui(filename))
        cm = CardMaker(cmName)
        cm.setFrameFullscreenQuad()
        cm.setUvRange(tex)
        card = NodePath(cm.generate())
        card.reparentTo(GI['base'].render2d)
        card.setTexture(tex)
        self.sound = GI['base'].loader.loadSfx(getGui(filename))
        tex.synchronizeTo(self.sound)
        self.card = card

        self.timer = Timer(self.sound.length())
    def play(self):
        self.card.show()
        self.sound.play()
        self.timer.reset()
    def stop(self):
        self.sound.stop()
        self.card.hide()
    def update(self):
        if self.timer.timeIsUp():
            self.stop()
    def isPlaying(self):
        return self.sound.status() == self.sound.PLAYING

class LightFlicker:
    def __init__(self, lightButton, filename):
        self.button = lightButton
        self.times = [0.1, 0.2, 0.4, 0.5, 1.7, 1.9, 2, 2.1, 3.2, 3.1, 3.6, 3.9, 4.5, 4.6, 5.5, 5.6, 6]
        for index, sec in enumerate(self.times):
            self.times[index] = Timer(sec+3)
        self.index = 0
        self.lightOn = True
        self.done = False
        self.sound = GI['base'].loader.loadSfx(filename)
    def start(self):
        self.index = 0
        self.lightOn = True
        self.done = False
        self.sound.play()
        for timer in self.times:
            timer.reset()
    def stop(self):
        self.lightOn = False
        self.done = True
        self.sound.stop()
        self.button.plight.node().setColor((0, 0, 0, 0))
    def update(self):
        if not self.button.closed:
            self.start()
            return
        if self.done or not self.button.closed:
            return
        
        if self.times[self.index].timeIsUp():
            if self.lightOn:
                color = (0, 0, 0, 0)
                self.sound.stop()
                #color = (0.8, 0.8, 0.8, 1)
            else:
                color = (0.2, 0.2, 0.2, 0.4)
                self.sound.play()
            self.button.plight.node().setColor(color)
            self.index += 1
            self.lightOn = not self.lightOn
            if self.index == len(self.times):
                self.done = True
                self.button.toggle()

class Clock:
    startAt = 12
    endAt = 7
    NIGHT = None

    def __init__(self):
        self.timeNow = self.startAt
        self.displayTime = lambda: f"{self.timeNow} AM"

        font = GI['base'].loader.loadFont("assets/font/five-nights-at-freddys.ttf")
        font.setPixelsPerUnit(240)

        textNode = TextNode('clock')
        textNode.setFont(font)
        textNode.setAlign(TextNode.ACenter)
        textNode.setText(self.displayTime())
        self.text = GI['base'].aspect2d.attachNewNode(textNode)
        self.text.setScale(0.2)
        self.text.setPos(-1.6, 0, 0.8)

        textNode = TextNode('night')
        textNode.setFont(font)
        textNode.setAlign(TextNode.ACenter)
        textNode.setText(f"Night {self.NIGHT}")
        self.nightText = GI['base'].aspect2d.attachNewNode(textNode)
        self.nightText.setScale(0.1)
        self.nightText.setPos(-1.6, 0, 0.7)

        self.timer = Timer(60)
    
    def update(self):
        if self.timer.timeIsUp():
            if self.timeNow == 12:
                self.timeNow = 1
            else:
                self.timeNow += 1
            
            self.text.node().setText(self.displayTime())
            self.timer.reset()
    
    def reset(self):
        self.timeNow = self.startAt
        self.timer.reset()

        self.text.node().setText(self.displayTime())

        self.show()
    
    def hide(self):
        self.text.hide()
        self.nightText.hide()
    
    def show(self):
        self.text.show()
        self.nightText.show()

class Battery:
    def __init__(self):
        textNode = TextNode('usageText')
        font = GI['base'].loader.loadFont("assets/font/five-nights-at-freddys.ttf")
        font.setPixelsPerUnit(240)
        textNode.setFont(font)
        textNode.setAlign(TextNode.ACenter)
        textNode.setText("Usage:")
        usageText = GI['base'].aspect2d.attachNewNode(textNode)
        usageText.setScale(0.15)
        usageText.setPos(-1.6, 0, -0.88)

        self.usageText = usageText
        
        pos = -1.3

        imageNum = 5
        self.usageImages = []
        for i in range(1, imageNum+1):
            image = OnscreenImage(getGui(f"power_usage{i}.png"), parent=GI['base'].aspect2d)
            image.setScale(0.05)
            image.setPos(pos, 0, -0.8)
            image.setTransparency(TransparencyAttrib.MAlpha)
            image.hide()
            self.usageImages.append(image)

            pos += 0.12
            
        self.usageImages[0].show()

        self.buttons = GI['base'].buttonMap.values()

        textNode = TextNode('powerLeftText')
        font = GI['base'].loader.loadFont("assets/font/five-nights-at-freddys.ttf")
        font.setPixelsPerUnit(240)
        textNode.setFont(font)
        textNode.setText("Power Left: 100%")
        self.powerLeftText = GI['base'].aspect2d.attachNewNode(textNode)
        self.powerLeftText.setScale(0.15)
        self.powerLeftText.setPos(-1.75, 0, -0.75)

        self.powerLeft = 100
        self.secTimer = Timer(1)
        self.seconds = 10
    
    def update(self):
        num = 1
        if GI['base'].onCams:
            num += 1
        for button in self.buttons:
            if button.closed:
                num += 1
        for image in self.usageImages[num:]:
            image.hide()
        for image in self.usageImages[1:num]:
            image.show()

        if self.secTimer.timeIsUp():
            if num == 1:
                if self.seconds:
                    self.seconds -= 1
                else:
                    self.seconds = 10
            elif num == 2:
                if self.seconds > 7 or not self.seconds:
                    self.seconds = 7
                else:
                    self.seconds -= 1
            elif num == 3:
                if self.seconds > 5 or not self.seconds:
                    self.seconds = 5
                else:
                    self.seconds -= 1
            elif num == 4:
                if self.seconds > 3 or not self.seconds:
                    self.seconds = 3
                else:
                    self.seconds -= 1
            else: # <= 5
                if self.seconds > 1 or not self.seconds:
                    self.seconds = 1
                else:
                    self.seconds -= 1

            if not self.seconds:
                self.powerLeft -= 1
                
            self.powerLeftText.node().setText(f"Power Left: {self.powerLeft}%")
            self.secTimer.reset()
    
    def reset(self):
        self.powerLeft = 100
        self.seconds = 10
        self.secTimer.reset()

        self.powerLeftText.node().setText(f"Power Left: {self.powerLeft}%")

        self.show()
        
    def hide(self):
        self.powerLeftText.hide()
        self.usageText.hide()
        for image in self.usageImages:
            image.hide()
    
    def show(self):
        self.powerLeftText.show()
        self.usageText.show()
        self.usageImages[0].show()

class DoorButton:
    def __init__(self, modelFname, cBoxName, cBoxPos, cBoxShape=(0, 0.02, 0.166, 0.166), hasAnims=False, sounds={}, doorActor=None, doorSounds={}, tex={}, plight=None, modelPos=(0, 0, 0)):
        if hasAnims:
            self.model = Actor(getModel(modelFname))
            self.hasAnims = True
        else:
            self.model = GI['base'].loader.loadModel(getModel(modelFname))
            self.hasAnims = False
        self.model.setPos(modelPos)
        self.model.reparentTo(GI['base'].environment)

        cBox = CollisionBox(*cBoxShape)
        cBoxNp = self.model.attachNewNode(CollisionNode(cBoxName))
        cBoxNp.node().addSolid(cBox)
        cBoxNp.setPos(*cBoxPos)

        self.cBoxNp = cBoxNp

        self.tex = {}
        for texName, fileName in tex.items():
            self.tex[texName] = GI['base'].loader.loadTexture(fileName)
        
        self.sounds = {}
        for soundName, fileName in sounds.items():
            self.sounds[soundName] = GI['base'].loader.loadSfx(fileName)

        self.closed = True
        self.door = doorActor
        if self.door:
            self.door.reparentTo(GI['base'].environment)
            self.door.sounds = {}
            for soundName, fileName in doorSounds.items():
                self.door.sounds[soundName] = GI['base'].loader.loadSfx(fileName)
        
        self.plight = plight

    def toggle(self, sound=True):
        if self.closed:
            if self.hasAnims:
                self.model.play("up")
            if self.door:
                self.door.play("open")
            if sound:
                if self.sounds:
                    self.sounds['on'].play()
                if self.door and self.door.sounds:
                    self.door.sounds['open'].play()
            if self.tex:
                for ts in self.model.findAllTextureStages():
                    self.model.setTexture(ts, self.tex['off'], 1)
            if self.plight:
                self.plight.node().setColor((0, 0, 0, 0))
        else:
            if self.hasAnims:
                self.model.play("down")
            if self.door:
                self.door.play("close")
            if sound:
                if self.sounds:
                    self.sounds['off'].play()
                if self.door and self.door.sounds:
                    self.door.sounds['close'].play()
            if self.tex:
                for ts in self.model.findAllTextureStages():
                    self.model.setTexture(ts, self.tex['on'], 1)
            if self.plight:
                self.plight.node().setColor((0.4, 0.4, 0.4, 1))
        self.closed = not self.closed

class Character:
    def __init__(self, modelFile: str, sounds: dict, mechanics: dict, level: int, activeTimes: tuple) -> None:
        self.model = Actor(getModel(modelFile))
        self.model.reparentTo(GI['base'].environment)

        self.sounds = {}
        for soundName, fileName in sounds.items():
            self.sounds[soundName] = GI['base'].loader.loadSfx(getSound(fileName))
        
        self.mechanics = mechanics
        self.level = level
        self.activeTimes = activeTimes
        self.timer = Timer(uniform(*AI_LEVEL_CONFIG[self.level]))
        self.flashTimer = Timer(0)
    
    def start(self, newLevel: int=None, newActiveTimes: int=None) -> None:
        self.movement = self.mechanics[GI['base'].night]

        self.model.setPos(self.movement["S: start room"]["room"][1])
        self.model.setHpr(self.movement["S: start room"]["room"][2])
        self.stage = list(self.movement)[0]
        self.activeTimes = self.activeTimes if newActiveTimes is None else newActiveTimes

        newTime = uniform(*AI_LEVEL_CONFIG[self.level]) if newLevel is None else uniform(*AI_LEVEL_CONFIG[newLevel])
        self.timer.reset(newTime)
        self.flashTimer.pause()
        self.finalTimerIndex = 0
    
    def update(self) -> bool:
        """ returns true if Character has attacked the player """
        if self.stage.startswith('F'): # means it's at its final stage.
            if self.movement[self.stage]["door"] == "leftDoor" or self.movement[self.stage]["door"] == "rightDoor":
                lightDoor = GI['base'].buttonMap[self.movement[self.stage]["door"][0:-4]+"Light"]
                if lightDoor.closed and self.flashTimer.paused:
                    self.flashTimer.resume()
                elif not lightDoor.closed and not self.flashTimer.paused:
                    self.flashTimer.pause()
            if self.timer.timeIsUp():
                if not GI['base'].buttonMap[self.movement[self.stage]["door"]].closed:
                    return self.gameOver()
                self.finalTimerIndex += 1
                if self.finalTimerIndex != len(self.movement[self.stage]["jumps"]):
                    self.timer.reset(self.movement[self.stage]["jumps"][self.finalTimerIndex])
        
        if self.flashTimer.timeIsUp():
            pass
        elif not (self.timer.timeIsUp() and GI['base'].gameClock.timeNow in self.activeTimes):
            return

        currentRoom = self.movement[self.stage]["room"][0]
        self.stage = choices(self.movement[self.stage]["next"], range(1, len(self.movement[self.stage]["next"])+1))[0]
        self.finalTimerIndex = 0
        nextRoom, pos, hpr = self.movement[self.stage]["room"]

        GI['base'].stompingNoise.play()
        if GI['base'].onCams and (GI['base'].lastCam == currentRoom or GI['base'].lastCam == nextRoom):
            GI['base'].camStaticVid.play()
        
        self.model.setPos(pos)
        self.model.setHpr(hpr)
        
        if self.stage.startswith('F'):
            self.flashTimer.reset(self.movement[self.stage]["flash"])
            self.timer.reset(self.movement[self.stage]["jumps"][self.finalTimerIndex])
        else:
            self.flashTimer.pause()
            self.timer.reset(uniform(*AI_LEVEL_CONFIG[self.level]))
    
    def gameOver(self):
        if GI['base'].isGameOver:
            return
        if GI['base'].onCams:
            GI['base'].toggleCamera()
        if GI['base'].inGame:
            GI['base'].toggleIngame()
        GI['base'].isGameOver = True
        GI['base'].music.stop()
        GI['base'].weirdNoise.stop()
        GI['base'].camStaticVid.stop()
        GI['base'].cursor.hide()
        GI['base'].cursorHover.hide()
        GI['base'].leftLightFlicker.stop()
        GI['base'].rightLightFlicker.stop()
        GI['base'].gameClock.hide()
        GI['base'].battery.hide()

        camPos, camHpr = self.movement[self.stage]["camPosHpr"]
        pos, hpr = self.movement[self.stage]["posHpr"]
        GI['base'].camera.setHpr(camHpr)
        GI['base'].camera.setPos(camPos)
        self.model.setPos(pos)
        self.model.setHpr(hpr)
        self.model.stop()
        GI['base'].camModel.play("shake")
        self.model.play("jumpscare")
        self.sounds['jumpscare'].play()

        if(GI['base'].gameOverScreen.isHidden()):
            Sequence(Func(GI['base'].gameOverScreen.setAlphaScale,0.0),Func(GI['base'].gameOverScreen.show),LerpFunctionInterval(GI['base'].gameOverScreen.setAlphaScale,toData=1.0,fromData=0.0,duration=5.0)).start()

        #YAHA.screenTransition.fadeOut(5)

        #YAHA.gameOverText.show()

        GI['base'].taskMgr.doMethodLater(5, GI['base'].start, "start", extraArgs=[])


DAD_MOVEMENT = {
    1: {
        "S: start room": {
            "room": ("Smoking Room", (-5, 22, 0), (0, 0, 0)),
            "next": ("1: dining room",)
        },
        "1: dining room": {
            "room": ("Dining Room", (-8, 12, 0), (0, 0, 0)),
            "next": ("2: baby room", "2: main hall")
        },
        "2: baby room": {
            "room": ("Baby Room", (-14, 7, 0), (0, 0, 0)),
            "next": ("1: dining room", "3: left hall")
        },
        "2: main hall": {
            "room": ("Main Hall", (5, 9, 0), (0, 0, 0)),
            "next": ("1: dining room", "3: break room")
        },
        "3: left hall": {
            "room": ("Left Hall", (-5, 5, 0), (0, 0, 0)),
            "next": ("2: baby room", "F: left hall")
        },
        "3: break room": {
            "room": ("Break Room", (2, 5, 0), (0, 0, 0)),
            "next": ("2: main hall", "F: break room")
        },
        "F: left hall": {
            "room": ("Left Hall", (-5, 5, 0), (0, 0, 0)),
            "next": ("1: dining room", "2: baby room"),
            "door": "leftDoor",
            "flash": 5,
            "jumps": (5, 4, 6),
            "posHpr": ((-3.5, 0, 0), (90, 0, 0)),
            "camPosHpr": ((1, 0, 2.5), (90, -10, 0))
        },
        "F: break room": {
            "room": ("Break Room", (2, 5, 0), (0, 0, 0)),
            "next": ("1: dining room", "2: main hall"),
            "door": "rollerDoor",
            "flash": 5,
            "jumps": (5, 4, 6),
            "posHpr": ((0.9, 2.3, 0.9), (-0.2, 0, 0)),
            "camPosHpr": ((-2.2, -3.3, 2.8), (-30, 85, 0))
        }
    }
}

MUM_MOVEMENT = {
    1: {
        "S: start room": {
            "room": ("Kitchen", (4, 14, 0), (0, 0, 0)),
            "next": ("1: dining room",)
        },
        "1: dining room": {
            "room": ("Dining Room", (-5, 16, 0), (0, 0, 0)),
            "next": ("2: dining room", "2: main hall")
        },
        "2: dining room": {
            "room": ("Dining Room", (-1, 11, 0), (0, 0, 0)),
            "next": ("3: left hall", "2: main hall")
        },
        "2: main hall": {
            "room": ("Main Hall", (2, 9, 0), (0, 0, 0)),
            "next": ("1: dining room", "2: dining room", "3: east hall")
        },
        "3: left hall": {
            "room": ("Left Hall", (-5, 0, 0), (90, 0, 0)),
            "next": ("2: dining room", "1: dining room")
        },
        "3: east hall": {
            "room": ("East Hall", (9.5, 4.5, 0), (0.7, 0, 0)),
            "next": ("F: right hall",)
        },
        "F: right hall": {
            "room": ("Right Hall", (5, 5, 0), (0, 0, 0)),
            "next": ("2: main hall", "2: dining room"),
            "door": "rightDoor",
            "flash": 8,
            "jumps": (8, 4, 5),
            "posHpr": ((3.5, 0, 0), (-90, 0, 0)),
            "camPosHpr": ((-1, 0, 2.5), (-90, -10, 0))
        }
    }
}

"""
random.choices( next_rooms, range(1, len(next_rooms)+1) )[0]
"""