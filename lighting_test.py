from direct.showbase.ShowBase import ShowBase
from panda3d.core import PointLight

class MyGame(ShowBase):
    def __init__(self):
        super().__init__()
#        self.disableMouse()

        self.env = self.loader.loadModel("assets/blend_files/map.gltf")
        self.env.reparentTo(self.render)

        self.plight = PointLight("plight")
        self.plight.setColor((0.6, 0.6, 0.6, 1))
        self.plight.attenuation = (0.1, 0, 0.1)
        self.plnp = self.render.attachNewNode(self.plight)
        self.plnp.setPos(0, 0, 6)
        self.render.setLight(self.plnp)

        self.render.setShaderAuto()

        self.camera.setPos(0, 0, 2)

game = MyGame()
game.run()
