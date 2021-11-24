from kivy.metrics import dp
from kivy.properties import ListProperty, StringProperty, BooleanProperty, ObjectProperty, NumericProperty

from kivy.core.window import Window
from kivy.animation import Animation

from kivy.uix.floatlayout import FloatLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.uix.button import Button
from kivy.uix.screenmanager import Screen, ScreenManager

from kivy.uix.behaviors import ButtonBehavior, ToggleButtonBehavior
from kivy.graphics import Color, Line, Rectangle, RoundedRectangle

from kivymd.uix.behaviors import (
    RectangularElevationBehavior,
    RectangularRippleBehavior,
    CircularElevationBehavior
)

from mygarden.mapview import MapView, MapSource


class Gyroscope(Widget):
    _angle = NumericProperty(0.)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

class InfoCard(
    RectangularElevationBehavior,
    RectangularRippleBehavior,
    ButtonBehavior,
    BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def on_press(self):
        print(self.icon)
        return super().on_press()


class ControllerCard(
    RectangularElevationBehavior,
    RectangularRippleBehavior,
    ButtonBehavior,
    BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def on_press(self):
        print(self.msg)
        return super().on_press()

class ArmIndecator(Widget):
    armed = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class DirectionKey(
    RectangularElevationBehavior,
    RectangularRippleBehavior,
    ButtonBehavior,
    BoxLayout):
    command = StringProperty('')
    command_code = StringProperty('')
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class StatusBar(FloatLayout):
    pass

class PanelTab(RectangularElevationBehavior,
    RectangularRippleBehavior,
    ButtonBehavior,
    Label):

    back_color = ListProperty([0,0,0,1])
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
class PanelScreen(Screen):
    pass

class PanelHeader(Widget):
    pass


class FormatToggleSelectArea(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

class FrameSizeToggleSelectArea(BoxLayout):
    pass

class ExpansionPanel(ButtonBehavior, BoxLayout):
    toggled = BooleanProperty(False)
    content_cls = ObjectProperty()
    text = StringProperty('')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.content_cls = Button(text='Hello', pos=self.pos, size=(dp(100), dp(50)))
        self.open_anim = Animation(height=dp(200), duration=.2)
        self.close_anim = Animation(height=dp(45), duration=.1)

    def on_press(self):
        if self.toggled:
            self.close_anim.start(self)
            self.open_anim.on_complete(self.remove_widget(self.content_cls))
            self.ids.icon.icon = 'chevron-right'
        else:
            self.open_anim.start(self)
            self.open_anim.on_complete(self.add_widget(self.content_cls))
            self.ids.icon.icon = 'chevron-down'
        self.toggled = not self.toggled
        return super().on_press()

class PanelManager(ScreenManager):
    pass

class SettingPanel(RectangularElevationBehavior, Widget):
    pass

class ControllersLayer(FloatLayout):
    pass

class InfoLayer(FloatLayout):
    pass

class MotionControllLayer(FloatLayout):
    pass

class CameraFeed(Image):
    pass

class DronesMap(MapView):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.map_source = MapSource(attribution="", min_zoom=3, max_zoom=18)

class MapWidget(ButtonBehavior, FloatLayout):
    pass

class CameraFeedLayer(Widget):
    pass

class CameraFeedThumbnail(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.feed = Image(source=('./assets/feed-placeholder.jpg'),
                            pos=self.pos, size=self.size, allow_stretch=True, 
                            keep_ratio=False)
        self.add_widget(self.feed)

        with self.canvas:
            Color(rgba=(0,0,0,0))
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(4)])
            Color(rgba=(0,0,0,.7))
            Line(width=dp(1.2), rectangle=[self.x, self.y, self.width, self.height])


class Container(FloatLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


        self.camera_feed_layer = CameraFeedLayer()
        self.camera_feed_layer.pos = 0,0
        self.camera_feed_layer.size = Window.size

        self.controller_layer = ControllersLayer()
        self.controller_layer.pos = 0,0
        self.controller_layer.size = Window.size

        self.map_layer = MapWidget()
        self.map_layer.pos = (dp(3), dp(3))
        self.map_layer.size = (dp(180), dp(100))

        self.add_widget(self.camera_feed_layer)
        self.add_widget(self.controller_layer)
        self.add_widget(self.map_layer)
