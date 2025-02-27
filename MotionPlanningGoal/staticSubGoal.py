import numpy as np
from MotionPlanningGoal.subGoal import SubGoal
from MotionPlanningSceneHelpers.motionPlanningComponent import DimensionNotSuitableForEnv
from pyquaternion import Quaternion


class StaticSubGoal(SubGoal):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.checkCompleteness()
        self.checkDimensionality()

    def limitLow(self):
        if 'low' in self._contentDict:
            return np.array(self._contentDict['low'])
        else:
            return np.ones(self.m()) * -1

    def limitHigh(self):
        if 'high' in self._contentDict:
            return np.array(self._contentDict['high'])
        else:
            return np.ones(self.m()) * 1

    def evaluate(self, **kwargs):
        return []

    def toDict(self):
        return self._contentDict

    def position(self, **kwargs):
        return self._contentDict['desired_position']

    def velocity(self, **kwargs):
        return np.zeros(self.dim())

    def acceleration(self, **kwargs):
        return np.zeros(self.dim())

    def shuffle(self):
        randomPos = np.random.uniform(self.limitLow(), self.limitHigh(), self.m())
        self._contentDict['desired_position'] = randomPos.tolist()

    def angle(self):
        if 'angle' in self._contentDict:
            return self._contentDict['angle']
        else:
            return None

    def renderGym(self, viewer, rendering, **kwargs):
        coordinate_system_1 = viewer.draw_line([-3, 0], [3, 0], color=[0.0, 0.0, 0.0])
        coordinate_system_2 = viewer.draw_line([0, -3], [0, 3], color=[0.0, 0.0, 0.0])
        angle = self.angle()
        if angle:
            tf2 = rendering.Transform(rotation=self.angle())
        else:
            tf2 = rendering.Transform()
        coordinate_system_1.add_attr(tf2)
        coordinate_system_2.add_attr(tf2)
        if self.m() == 1:
            start_point = [-10, -10.0]
            end_point = [10.0, 10.0]
            start_point[self.indices()[0]] = 0.0
            end_point[self.indices()[0]] = 0.0
            goal = viewer.draw_line(start_point, end_point, color=[0.0, 1.0, 0.0])
            translation = [0.0, 0.0]
            translation[self.indices()[0]] = self.position()[0]
            tf = rendering.Transform(translation=translation)
            goal.add_attr(tf)
            goal.add_attr(tf2)
        elif self.m() == 2:
            x = self.position()
            goal = viewer.draw_circle(self.epsilon(), color=[0.0, 1.0, 0.0])
            tf = rendering.Transform(translation=(x[0], x[1]))
            goal.add_attr(tf)
            goal.add_attr(tf2)
        else:
            raise DimensionNotSuitableForEnv("PlanarGym only supports two dimensional obstacles")


    def add2Bullet(self, pybullet, position=[0.0, 0.0, 0.0]):
        if self.m() == 2:
            basePosition = self.position() + [0.0]
        elif self.m() == 3:
            basePosition = self.position()
        else:
            raise DimensionNotSuitableForEnv("Pybullet only supports three dimensional obstacles")
        rgbaColor = [0.0, 1.0, 0.0, 0.3]
        visualShapeId = pybullet.createVisualShape(pybullet.GEOM_SPHERE, rgbaColor=rgbaColor, radius=self.epsilon())
        collisionShape = -1
        baseOrientation = [0, 0, 0, 1]
        mass = 0

        pybullet.createMultiBody(
                    mass,
                    collisionShape,
                    visualShapeId,
                    basePosition,
                    baseOrientation,
        )

        if self.angle():
            for i in range(3):
                self.addAxisComponent(pybullet, i, position)

    def addAxisComponent(self, pybullet, i, goal_position):
        rgbaColor = [0.0, 0.0, 0.0, 0.3]
        angles = self.angle()
        if not angles:
            angles = Quaternion([1, 0., 0, 0])
        else:
            angles = Quaternion(angles).inverse
        orientation = Quaternion([1, 0, 0, 0])
        orientation[i+1] = 1.0
        orientation = orientation.normalised
        position = np.array([goal_position[0], goal_position[1], goal_position[2]])
        orientation = angles * orientation
        orientation_array = [orientation[1], orientation[2], orientation[3], orientation[0]]
        offset_array = [np.array([0.00, 0.00, -0.05]), np.array([0.0, 0.0, 0.05]), np.array([0.0, 0.0, 0.05])]

        position += orientation.rotate(offset_array[i])
        index_map = [1, 0, 2]
        rgbaColor[index_map[i]] = 1.0
        visual_shape_id = pybullet.createVisualShape(
            pybullet.GEOM_CYLINDER, rgbaColor=rgbaColor,radius=0.01, length=0.1
        )
        collisionShape = -1
        mass = 0
        pybullet.createMultiBody(
                    mass,
                    collisionShape,
                    visual_shape_id,
                    position,
                    orientation_array,
        )
