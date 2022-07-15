from direct.directbase import DirectStart
from pandac.PandaModules import *

smiley = loader.loadModel('smiley')
smiley.reparentTo(render)
smiley.setTag('pickable', '')

pickerNode = CollisionNode('mouseRay')
pickerNP = camera.attachNewNode(pickerNode)
pickerNode.setFromCollideMask(GeomNode.getDefaultCollideMask())
pickerRay = CollisionRay()
pickerNode.addSolid(pickerRay)
pickerNP.show()
rayQueue = CollisionHandlerQueue()
base.cTrav = CollisionTraverser()
base.cTrav.addCollider(pickerNP, rayQueue)

def pickObject():
        if base.mouseWatcherNode.hasMouse():
                mpos = base.mouseWatcherNode.getMouse()
                pickerRay.setFromLens(base.camNode, mpos.getX(), mpos.getY())
                if rayQueue.getNumEntries() > 0:
                        rayQueue.sortEntries()
                        print(rayQueue.entries)
                        entry = rayQueue.getEntry(0)
                        pickedNP = entry.getIntoNodePath()
                        if pickedNP.hasNetTag('pickable'):
                                print('Clicked on the nodepath (with tag "pickable"): %s' % pickedNP)
#base.oobe()
base.accept('mouse1', pickObject)
base.disableMouse() #- Disable default camera driver
camera.setY(camera, -10) #- Move the camera back a lil bit so we can see the smiley
run()