from panda3d.core import CollisionBox, CollisionNode, MovieTexture, CardMaker, NodePath, TextNode, TransparencyAttrib
from direct.gui.OnscreenImage import OnscreenImage
from direct.actor.Actor import Actor
from random import  uniform, choice
import GlobalInstance

getModel = lambda f: "./new_assets/gltfs/"+f+".glb"
getGui   = lambda f: "./new_assets/gui/"+f
getSound = lambda f: "./new_assets/sounds/"+f

AI_LEVEL_CONFIG = ( # Index 0 should be None since levels go from 1 to 10
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
        self.startAt = GlobalInstance.GameObject.taskMgr.globalClock.getFrameTime()
        self.seconds = seconds
    def reset(self, newTime=None):
        self.startAt = GlobalInstance.GameObject.taskMgr.globalClock.getFrameTime()
        if newTime:
            self.seconds = newTime
    def timeIsUp(self):
        ft = GlobalInstance.GameObject.taskMgr.globalClock.getFrameTime()

        secNow = ft - self.startAt
        if secNow >= self.seconds:
            return True
        else:
            return False

class VideoEffect:
    def __init__(self, mtName, cmName, filename):
        tex = MovieTexture(mtName)
        tex.read(getGui(filename))
        cm = CardMaker(cmName)
        cm.setFrameFullscreenQuad()
        cm.setUvRange(tex)
        card = NodePath(cm.generate())
        card.reparentTo(GlobalInstance.GameObject.render2d)
        card.setTexture(tex)
        self.sound = GlobalInstance.GameObject.loader.loadSfx(getGui(filename))
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
        self.sound = GlobalInstance.GameObject.loader.loadSfx(filename)
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

        font = GlobalInstance.GameObject.loader.loadFont("assets/font/five-nights-at-freddys.ttf")
        font.setPixelsPerUnit(240)

        textNode = TextNode('clock')
        textNode.setFont(font)
        textNode.setAlign(TextNode.ACenter)
        textNode.setText(self.displayTime())
        self.text = GlobalInstance.GameObject.aspect2d.attachNewNode(textNode)
        self.text.setScale(0.2)
        self.text.setPos(-1.6, 0, 0.8)

        textNode = TextNode('night')
        textNode.setFont(font)
        textNode.setAlign(TextNode.ACenter)
        textNode.setText(f"Night {self.NIGHT}")
        self.nightText = GlobalInstance.GameObject.aspect2d.attachNewNode(textNode)
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
        font = GlobalInstance.GameObject.loader.loadFont("assets/font/five-nights-at-freddys.ttf")
        font.setPixelsPerUnit(240)
        textNode.setFont(font)
        textNode.setAlign(TextNode.ACenter)
        textNode.setText("Usage:")
        usageText = GlobalInstance.GameObject.aspect2d.attachNewNode(textNode)
        usageText.setScale(0.15)
        usageText.setPos(-1.6, 0, -0.88)

        self.usageText = usageText
        
        pos = -1.3

        imageNum = 5
        self.usageImages = []
        for i in range(1, imageNum+1):
            image = OnscreenImage(getGui(f"power_usage{i}.png"), parent=GlobalInstance.GameObject.aspect2d)
            image.setScale(0.05)
            image.setPos(pos, 0, -0.8)
            image.setTransparency(TransparencyAttrib.MAlpha)
            image.hide()
            self.usageImages.append(image)

            pos += 0.12
            
        self.usageImages[0].show()

        self.buttons = GlobalInstance.GameObject.buttonMap.values()

        textNode = TextNode('powerLeftText')
        font = GlobalInstance.GameObject.loader.loadFont("assets/font/five-nights-at-freddys.ttf")
        font.setPixelsPerUnit(240)
        textNode.setFont(font)
        textNode.setText("Power Left: 100%")
        self.powerLeftText = GlobalInstance.GameObject.aspect2d.attachNewNode(textNode)
        self.powerLeftText.setScale(0.15)
        self.powerLeftText.setPos(-1.75, 0, -0.75)

        self.powerLeft = 100
        self.secTimer = Timer(1)
        self.seconds = 10
    
    def update(self):
        num = 1
        if GlobalInstance.GameObject.onCams:
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
            self.model = GlobalInstance.GameObject.loader.loadModel(getModel(modelFname))
            self.hasAnims = False
        self.model.setPos(modelPos)
        self.model.reparentTo(GlobalInstance.GameObject.environment)

        cBox = CollisionBox(*cBoxShape)
        cBoxNp = self.model.attachNewNode(CollisionNode(cBoxName))
        cBoxNp.node().addSolid(cBox)
        cBoxNp.setPos(*cBoxPos)

        self.cBoxNp = cBoxNp

        self.tex = {}
        for texName, fileName in tex.items():
            self.tex[texName] = GlobalInstance.GameObject.loader.loadTexture(fileName)
        
        self.sounds = {}
        for soundName, fileName in sounds.items():
            self.sounds[soundName] = GlobalInstance.GameObject.loader.loadSfx(fileName)

        self.closed = True
        self.door = doorActor
        if self.door:
            self.door.reparentTo(GlobalInstance.GameObject.environment)
            self.door.sounds = {}
            for soundName, fileName in doorSounds.items():
                self.door.sounds[soundName] = GlobalInstance.GameObject.loader.loadSfx(fileName)
        
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
                self.model.setTexture(self.tex['off'], 1)
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
                self.model.setTexture(self.tex['on'], 1)
            if self.plight:
                self.plight.node().setColor((0.4, 0.4, 0.4, 1))
        self.closed = not self.closed

class Animatronic:
    def __init__(self, model: dict, sounds: dict, movePattern: tuple, level: int, activeTimes: tuple, attackDoor: str) -> None:
        self.model = Actor(getModel(model))
        self.model.reparentTo(GlobalInstance.GameObject.environment)

        self.sounds = {}
        for soundName, fileName in sounds.items():
            self.sounds[soundName] = GlobalInstance.GameObject.loader.loadSfx(getSound(fileName))
        
        self.movePattern = movePattern
        self.level = level
        self.activeTimes = activeTimes
        self.attackDoor = attackDoor
        self.timer = Timer(uniform(*AI_LEVEL_CONFIG[level]))
        
    def start(self, newLevel: int=None, newActiveTimes: int=None) -> None:
        self.model.setPos(self.movePattern[0][1])
        self.model.setHpr(self.movePattern[0][2])
        self.lastRoom = self.movePattern[0][0]
        self.moveIndex = 0
        newTime = uniform(*AI_LEVEL_CONFIG[self.level]) if newLevel is None else uniform(*AI_LEVEL_CONFIG[newLevel])
        self.activeTimes = self.activeTimes if newActiveTimes is None else newActiveTimes
        self.timer.reset(newTime)
    
    def update(self, timeNow: int, stompingNoise, onCams: bool, lastCam: str, camStaticVid, buttonMap: dict) -> bool:
        """ returns true if Animatronic has attacked the player """
        if self.timer.timeIsUp() and timeNow in self.activeTimes:
            roomNow = self.lastRoom
            self.moveIndex += 1

            if self.lastRoom == self.movePattern[-1][0]:
                if not buttonMap[self.attackDoor].closed:
                    return True
                self.moveIndex = 0
                self.timer.reset(uniform(*AI_LEVEL_CONFIG[self.level]))
            
            if self.moveIndex >= len(self.movePattern[1:-1]):
                roomNext = self.movePattern[-1]
            else:
                roomNext = choice(self.movePattern[1:-1])
                while roomNext[0] == self.lastRoom:
                    roomNext = choice(self.movePattern[1:-1])

            stompingNoise.play()
            if onCams and (lastCam == roomNow or lastCam == roomNext[0]):
                camStaticVid.play()
            pos = roomNext[1]
            hpr = roomNext[2]
            self.model.setPos(pos)
            self.model.setHpr(hpr)

            self.lastRoom = roomNext[0]

            self.timer.reset(uniform(*AI_LEVEL_CONFIG[self.level]))