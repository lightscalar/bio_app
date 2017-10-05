from chart import *
from engine import *
from kivy.clock import Clock
from kivy.app import App
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.recycleview import RecycleView
from kivy.properties import NumericProperty, StringProperty, BooleanProperty
from kivy.config import Config
from prepare_downloads import create_csv
from sixer import *
from solid_db import SolidDB
import time

# Configure the dimensions of the application window.
Config.set('graphics', 'resizable', '0') # 0 being off 1 being on
Config.set('graphics', 'width', '1000')
Config.set('graphics', 'height', '600')


# Create an instance of the database.
db = SolidDB('data/db.json')


class MenuScreen(Screen):
    pass


class AnnotateScreen(Screen):
    pass


class ReportBuilderScreen(Screen):
    pass


class SessionScreen(Screen):
    pass


class PiezoScreen(Screen):
    pass


class PPGScreen(Screen):
    pass


class RV(RecycleView):
    '''View the session.'''

    def __init__(self, **kwargs):
        super(RV, self).__init__(**kwargs)
        self.refresh()

    def refresh(self):
        data = db.all('sessions')
        data = sorted(data, key=lambda x: x['createdAt'], reverse=True)
        self.data = data

    def create_session(self):
        '''Create a new session.'''
        session = {'hid': sixer()}
        session = db.insert('session', session)
        self.refresh()


class AnnotationList(RecycleView):
    '''View the session's annotations.'''
    session_id = StringProperty('')
    def __init__(self, **kwargs):
        super(AnnotationList, self).__init__(**kwargs)
        self.refresh()

    def refresh(self):
        print('Refreshing...')
        data = db.find_where('annotations', 'session_id', self.session_id)
        data = sorted(data, key=lambda x: x['createdAt'], reverse=True)
        self.data = data


class BiomonitorApp(App):
    session_name = StringProperty('NO ACTIVE SESSION')
    session_color = ListProperty([0.476, 0.476, 0.476, 1])
    sessions = ListProperty([])
    session = ObjectProperty(None)
    streaming = BooleanProperty(False)
    recording = BooleanProperty(False)

    def create_session(self):
        session = {'hid': sixer()}
        session = db.insert('session', session)
        self.root.session_screen.session_list.refresh()
        self.set_session(session['_id'])

    def set_session(self, session_id):
        self.session_color = [1,1,1,1]
        self.session = db.find_by_id(session_id)
        self.session_name = self.session['hid'].upper()
        self.root.annotate_screen.annotation_list.session_id = \
                self.session['_id']
        self.root.annotate_screen.annotation_list.refresh()
        self.root.current='menu_screen'

    def delete_session(self, session_id):
        db.delete(session_id)
        self.root.session_screen.session_list.refresh()

    def delete_annotation(self, annotation_id):
        db.delete(annotation_id)
        self.root.annotate_screen.annotation_list.refresh()

    def add_annotation(self, annotation):
        '''Add annotation to the current session.'''
        print(self.root.pzt_screen)
        if not self.session:
            # Cannot annotate if there's no active session.
            self.root.current = 'session_screen'
        else:
            annotation['session_id'] = self.session['_id']
            annotation['date'] = time.strftime('%Y-%m-%d', time.localtime())
            annotation['time'] = time.strftime('%H:%M:%S', time.localtime())
            db.insert('annotation', annotation)
            self.root.annotate_screen.annotation_list.refresh()

    def data_available(self, data):
        # Data is available. Let's take a look.
        if data[0] == 0: # PZT
            self.pzt_chart.add_data(data)
        if data[0] == 1: # PPG
            self.ppg_chart.add_data(data)

    def start_recording(self):
        # Start recording PZT/PPG data to the disk.
        print('Starting to Record.')
        if self.session is not None:
            self.recording = True
            self.engine.start_recording(self.session['_id'])

    def stop_recording(self):
        # Stop recording data to the disk.
        print('Data Recording Stopped')
        self.recording = False
        self.engine.stop_recording()

    def toggle_recording(self):
        if self.recording:
            self.stop_recording()
        else:
            self.start_recording()

    def save_data(self, session_id):
        print('Saving session {}'.format(session_id))
        create_csv(session_id)

    def build(self):
        # Build application; set up chart updates.
        # Initialize the PZT chart
        self.pzt_chart = self.root.pzt_screen.pzt_chart
        self.pzt_chart.init()
        # Initialize the PPG chart
        self.ppg_chart = self.root.ppg_screen.ppg_chart
        self.ppg_chart.init()
        # Schedule updates.
        Clock.schedule_interval(self.pzt_chart.tick, 1.0 / 100.0)
        Clock.schedule_interval(self.ppg_chart.tick, 1.0 / 100.0)
        self.engine = Engine()
        self.engine.events.on_data += self.data_available


if __name__ == '__main__':
    BiomonitorApp().run()
