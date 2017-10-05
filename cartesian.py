from kivy.app import App
from kivy.properties import NumericProperty, StringProperty, BooleanProperty
from kivy.properties import ObjectProperty, ListProperty
from kivy.uix.widget import Widget
from kivy.graphics import Color, Ellipse, Line, Rectangle
from kivy.clock import Clock
from random import random


class Axis(object):
    '''An axis class for easy mapping of numeric domain to pixel range.'''

    def __call__(self, x):
        # Map value x in domain to y in range.
        if self.x1 == self.x2: return x
        self.s = (self.y2 - self.y1)/(self.x2 - self.x1)
        return (self.s * (x - self.x1) + self.y1)

    def invert(self, y):
        # Map value y in range to corresponding value x in domain.
        self.s = (self.y2 - self.y1)/(self.x2 - self.x1)
        return (1/self.s) * (y - self.y1) + self.x1

    def domain(self, domain_in):
        # Set the domain of the axis.
        self.x1 = domain_in[0]
        self.x2 = domain_in[1]

    def range(self, range_out):
        # Set the range of the axis mapping.
        self.y1 = range_out[0]
        self.y2 = range_out[1]


class Cartesian(Widget):
    xax = ObjectProperty(Axis())
    yax = ObjectProperty(Axis())
    last_point = NumericProperty(500)
    line_data = ListProperty([])

    def init(self):
        # Construct axes for this plot.
        self.update_axes()

    def update_axes(self):
        # Update the x/y axes
        biomonitor = self.parent

        # x-axis
        x_domain = [-biomonitor.chart_width, 0]
        x_range = [self.x, self.right]
        self.xax.domain(x_domain)
        self.xax.range(x_range)

        # y-axis
        y_domain = [biomonitor.chart_min, biomonitor.chart_max]
        y_range = [self.y, self.y + self.height]
        self.yax.domain(y_domain)
        self.yax.range (y_range)

    def draw(self, t_, v_):
        # Add updated time series to the canvas
        t_pix = self.xax(t_).astype(int)
        v_pix = self.yax(v_).astype(int)
        self.line_data = zip(t_pix, v_pix)
        self.last_point = int(self.yax(v_[-1])) - 10


class CartesianApp(App):

    def build(self):
        cartesian = Cartesian()
        cartesian.init()
        return cartesian


if __name__ == '__main__':

    # Build a cartesian canvas.
    CartesianApp().run()
