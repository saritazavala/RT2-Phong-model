#Universidad del Valle de Guatemala
#Sara Zavala 18893
#RT2
#Graficas

import struct
from collections import namedtuple
import math
from lib import *




# Struct Functions ---------------------------------
def char(c):
    return struct.pack('=c', c.encode('ascii'))

# 2 bytes
def word(c):
    return struct.pack('=h', c)

# 4 bytes
def dword(c):
    return struct.pack('=l', c)

# --------------------------------------------------

class color(object):
  def __init__(self,r,g,b):
    self.r = r
    self.g = g
    self.b = b

  def __add__(self, other_color):
    r = self.r + other_color.r
    g = self.g + other_color.g
    b = self.b + other_color.b

    return color(r,g,b)

  def __mul__(self, other):
    r = self.r * other
    g = self.g * other
    b = self.b * other

    return color(r,g,b)
  __rmul__ = __mul__

  def __repr__(self):
    return "color(%s, %s, %s)" % (self.r, self.g,self.b)

  def toBytes(self):
    self.r = int(max(min(self.r, 255), 0))
    self.g = int(max(min(self.g, 255), 0))
    self.b = int(max(min(self.b, 255), 0))
    return bytes([self.b,self.g,self.r])

class Light(object):
  def __init__(self, color =color(255,255,255),position =V3(0,0,0), intensity = 1):
    self.color = color
    self.position = position
    self.intensity = intensity


class Material(object):
  def __init__(self, diffuse =color(255,255,255), albedo=(1,0), spec=0):
    self.diffuse = diffuse
    self.albedo = albedo
    self.spec = spec

class Intersect(object):
  def __init__(self, distance=0, point=None, normal= None):
    self.distance = distance
    self.point = point
    self.normal = normal


# Sphere class
class Sphere(object):
  def __init__(self, center, radius, material):
    self.center = center
    self.radius = radius
    self.material = material

  def ray_intersect(self, orig, direction):
    L = sub(self.center, orig)
    tca = dot(L, direction)
    l = length(L)
    d2 = l ** 2 - tca ** 2

    if d2 > self.radius ** 2:
      return None

    thc = (self.radius ** 2 - d2) ** 1 / 2
    t0 = tca - thc
    t1 = tca + thc

    if t0 < 0:
      t0 = t1

    if t0 < 0:
      return None

    hit = sum(orig, mul(direction,t0))
    normal = norm(sub(hit, self.center))

    return Intersect(
      distance=t0,
      point = hit,
      normal=normal
    )

# Write a BMP file ---------------------------------
class Render(object):

    # Initial values -------------------------------

    def __init__(self, filename):
      self.scene = []
      self.width = 0
      self.light = None
      self.height = 0
      self.framebuffer = []
      self.change_color = color(236,235,234)
      self.filename = filename
      self.x_position = 0
      self.y_position = 0
      self.ViewPort_height = 0
      self.ViewPort_width = 0
      self.glClear()

    # File Header ----------------------------------

    def header(self):
      doc = open(self.filename, 'bw')
      doc.write(char('B'))
      doc.write(char('M'))
      doc.write(dword(54 + self.width * self.height * 3))
      doc.write(dword(0))
      doc.write(dword(54))
      self.info(doc)

    # Info header ----------------------------------

    def info(self, doc):
      doc.write(dword(40))
      doc.write(dword(self.width))
      doc.write(dword(self.height))
      doc.write(word(1))
      doc.write(word(24))
      doc.write(dword(0))
      doc.write(dword(self.width * self.height * 3))
      doc.write(dword(0))
      doc.write(dword(0))
      doc.write(dword(0))
      doc.write(dword(0))

      # Image ----------------------------------
      for x in range(self.height):
        for y in range(self.width):
          doc.write(self.framebuffer[x][y].toBytes())
      doc.close()

    # Writes all the doc
    def glFinish(self):
      self.header()


# Color gl Functions ---------------------------------

    # Cleans a full image with the color defined in "change_color"
    def glClear(self):
      self.framebuffer = [[self.change_color for x in range(self.width)] for y in range(self.height)]
      self.zbuffer = [[-float('inf') for x in range(self.width)] for y in range(self.height)]


    # Draws a point according ot frameBuffer
    def glpoint(self, x, y):
      self.framebuffer[y][x] = self.change_color

    # Creates a window
    def glCreateWindow(self, width, height):
      self.width = width
      self.height = height

    # Takes a new color
    def glClearColor(self, red, blue, green):
      self.change_color = color(red, blue, green)

    # Defines the area where will be able to draw
    def glViewPort(self, x_position, y_position, ViewPort_width, ViewPort_height):
      self.x_position = x_position
      self.y_position = y_position
      self.ViewPort_height = ViewPort_height
      self.ViewPort_width = ViewPort_width

    # Compuse el vertex por que me daba error el range
    def glVertex(self, x, y):
      x_temp = round((x + 1) * (self.ViewPort_width / 2) + self.x_position)
      y_temp = round((y + 1) * (self.ViewPort_height / 2) + self.y_position)
      self.glpoint(round(x_temp), round(y_temp))

    # This function creates a Line using the glpoint() function
    def glLine(self, x1, y1, x2, y2):
      dy = abs(y2 - y1)
      dx = abs(x2 - x1)
      steep = dy > dx

      if steep:
        x1, y1 = y1, x1
        x2, y2 = y2, x2
        dy = abs(y2 - y1)
        dx = abs(x2 - x1)

      if x1 > x2:
        x1, x2 = x2, x1
        y1, y2 = y2, y1

      offset = 0
      threshold = 1
      y = y1
      for x in range(x1, x2):
        if steep:
          self.glpoint(y, x)
        else:
          self.glpoint(x, y)

        offset += dy * 2

        if offset >= threshold:
          y += 1 if y1 < y2 else -1
          threshold += 2 * dx

    def cast_ray(self, orig, direction):
      material, impact = self.scene_intersect(orig, direction)

      if material is None:
        return self.change_color

      light_dir = norm(sub(self.light.position, impact.point))
      light_distance = length(sub(self.light.position, impact.point))


      offset_normal = mul(impact.normal, 1.1)

      if dot(light_dir, impact.normal) <0:
        shadow_origin = sub(impact.point, offset_normal)
      else:
        shadow_origin = sum(impact.point, offset_normal)


      shadow_material, shadow_intersect = self.scene_intersect(shadow_origin,light_dir)
      shadow_intensity = 0

      if shadow_intersect and length(sub(shadow_intersect.point, shadow_origin)) < light_distance:
        shadow_intensity = 0.9

      intensity = self.light.intensity * max(0, dot(light_dir, impact.normal))*(1 - shadow_intensity)

      reflection = reflect(light_dir, impact.normal)
      specular_intensity = self.light.intensity * (
              max(0, -dot(reflection, direction)) ** material.spec
      )

      diffuse = material.diffuse * intensity * material.albedo[0]
      specular = color(255, 255, 255) * specular_intensity * material.albedo[1]
      return diffuse + specular


    def scene_intersect(self, orig, dir):
      zbuffer = float('inf')
      material = None
      intersect = None

      for obj in self.scene:
        hit = obj.ray_intersect(orig, dir)
        if hit is not None:
          if hit.distance < zbuffer:
            zbuffer = hit.distance
            material = obj.material
            intersect = hit

      return material, intersect


    def render(self):
      fun = int(math.pi / 2)
      for y in range(self.height):
        for x in range(self.width):
          i = (2 * (x + 0.5) / self.width - 1) * math.tan(fun / 2) * self.width / self.height
          j = (2 * (y + 0.5) / self.height - 1) * math.tan(fun / 2)
          direction = norm(V3(i, j, -1))
          self.framebuffer[y][x] = self.cast_ray(V3(0, 0, 0), direction)



# Create --------------------------

ivory = Material(diffuse=color(100, 100, 80), albedo=(0.6,  0.3), spec=50)
rubber = Material(diffuse=color(80, 10, 0), albedo=(0.9,  0.1), spec=10)
brown = Material(diffuse=color(186,91,41), albedo=(0.4,0.2),spec=10)
light_brown = Material(diffuse=color(235,169,133), albedo=(0.4,0.2),spec=10)
red = Material(diffuse=color(217,41,41), albedo=(0.6,0.3), spec=10)
green = Material(diffuse=color(177,191,69), albedo=(0.6,0.3), spec=10)
grey = Material(diffuse=color(221,221,218), albedo=(0.4,0.6), spec=10)
white = Material(diffuse=color(255,254,255), albedo=(0.6,0.3), spec=10)


r = Render('Lab.bmp')
r.glCreateWindow(1000,600)
r.glClear()

r.light = Light(
  color=color(255,255,255),
  position = V3(-20, 20, 20),
  intensity = 1.85
)


r.scene = [
#Brown Bear
  #ears
  Sphere(V3(2, 3.5, -10), 0.75, brown),
  Sphere(V3(4.5, 3.5, -10), 0.75, brown),
  #
  # #Head
  Sphere(V3(3, 2.25, -10),1.5, light_brown),
  #
  # #body
  Sphere(V3(3, -1.15, -10),2.25, red),
  #
  # #Upper Paws
  Sphere(V3(4.5, 0, -8.5), 0.65, light_brown),
  Sphere(V3(0.85, 0, -8.5), 0.65, light_brown),
  #
  # #Lower paws
  Sphere(V3(3.85, -2, -7.5), 0.75, light_brown),
  Sphere(V3(0.85, -2, -7.5), 0.75, light_brown),

#White Bear

  # ears
  Sphere(V3(-6.5, 3.5, -10), 0.75, white),
  Sphere(V3(-3.5, 3.5, -10), 0.75, white),

  # Head
  Sphere(V3(-5, 2.25, -10), 1.5, white),

  # body
  Sphere(V3(-5, -1.15, -10), 2.25, grey),

  # Upper Paws
  Sphere(V3(-2.5, 0, -8.5), 0.65, white),
  Sphere(V3(-6.5, 0, -8.25), 0.65, white),

  # Lower paws
  Sphere(V3(-2.75, -2, -7.5), 0.75, white),
  Sphere(V3(-5.15, -2, -7.5), 0.75, white),


]
r.render()
r.glFinish()