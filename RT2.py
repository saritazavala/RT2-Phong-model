#Universidad del Valle de Guatemala
#Sara Zavala 18893
#RT2
#Graficas

import struct
from collections import namedtuple
import math


V2 = namedtuple('Vertex2', ['x', 'y'])
V3 = namedtuple('Vertex3', ['x', 'y', 'z'])

# Struct Functions ---------------------------------
def char(c):
    return struct.pack('=c', c.encode('ascii'))

# 2 bytes
def word(c):
    return struct.pack('=h', c)

# 4 bytes
def dword(c):
    return struct.pack('=l', c)

def color(red, green, blue):
     return bytes([round(blue * 255), round(green * 255), round(red * 255)])

def color2(r, g, b):
  return bytes([b, g, r])
# --------------------------------------------------

# Math functions ------------------------------------

def sum(v0, v1):
  return V3(v0.x + v1.x, v0.y + v1.y, v0.z + v1.z)

def sub(v0, v1):
  return V3(v0.x - v1.x, v0.y - v1.y, v0.z - v1.z)

def mul(v0, k):
  return V3(v0.x * k, v0.y * k, v0.z *k)

def dot(v0, v1):
  return v0.x * v1.x + v0.y * v1.y + v0.z * v1.z

def cross(v1, v2):
  return V3(
    v1.y * v2.z - v1.z * v2.y,
    v1.z * v2.x - v1.x * v2.z,
    v1.x * v2.y - v1.y * v2.x,
  )

def length(v0):
  return (v0.x**2 + v0.y**2 + v0.z**2)**0.5

def norm(v0):
  v0length = length(v0)

  if not v0length:
    return V3(0, 0, 0)

  return V3(v0.x/v0length, v0.y/v0length, v0.z/v0length)

def bbox(*vertices):

  xs = [ vertex.x for vertex in vertices ]
  ys = [ vertex.y for vertex in vertices ]

  return (max(xs), max(ys), min(xs), min(ys))

def barycentric(A, B, C, P):
  cx, cy, cz = cross(
    V3(B.x - A.x, C.x - A.x, A.x - P.x),
    V3(B.y - A.y, C.y - A.y, A.y - P.y)
  )

  if abs(cz) < 1:
    return -1, -1, -1


  u = cx/cz
  v = cy/cz
  w = 1 - (cx + cy)/cz

  return w, v, u

# --------------------------------------------------

class Light(object):
  def __init__(self, position =V3(0,0,0), intensity = 1):
    self.position = position
    self.intensity = intensity

class Material(object):
  def __init__(self, diffuse):
    self.diffuse = diffuse

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
      self.width = 0
      self.height = 0
      self.framebuffer = []
      self.change_color = color(0, 0, 0)
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
          doc.write(self.framebuffer[x][y])
      doc.close()

    # Writes all the doc
    def glFinish(self):
      self.render_function()
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



# Functions for the snowMan
    def render_function(self):
      alfa = int( math.pi / 2)
      for y in range(self.height):
        for x in range(self.width):
          i = ( 2 *(x + 0.5) / self.width - 1) * self.width / self.height * math.tan(alfa / 2)
          j = ( 1 - 2 *(y + 0.5) / self.height) * math.tan(alfa / 2)
          direction = norm(V3(i, j, -1))
          self.framebuffer[y][x] = self.cast_ray(V3(0, 0, 0), direction)



    def cast_ray(self, origin, dir):
      impacted_material, impact = self.scene_intersect(origin, dir)

      #no le pega a nada
      if impacted_material is None:
        return self.change_color

      #Light
      light_dir = norm(sub(self.light.position, impact.point))
      intensity  = max(0,dot(light_dir, impact.normal))

      difusse_light = color2(
        int(impacted_material.diffuse[2] * intensity),
        int(impacted_material.diffuse[1] * intensity),
        int(impacted_material.diffuse[0] * intensity),
      )

      return difusse_light


    def scene_intersect(self, origin, dir):
      zbuffer = float('inf')
      material = None
      intersect = None

      for obj in self.scene:
        hit = obj.ray_intersect(origin,dir)
        if hit is not None:
          if hit.distance < zbuffer:
            zbuffer = hit.distance
            material = obj.material
            intersect = hit


      return material, intersect




# Create --------------------------
rubber = Material(diffuse=color(0.3, 0, 0))
ivory = Material(diffuse=color(0.4, 0.4, 0.3))

r = Render('Prueba.bmp')
r.glCreateWindow(800,600)
r.glClear()
r.light = Light(V3(0.5,0,0), 1)
r.scene = [
  Sphere(V3(0, -1.5, -10), 1.5, ivory),
  Sphere(V3(-2, -1, -12), 2, rubber),
  Sphere(V3(1, 1, -8), 1.7, rubber),
  Sphere(V3(0, 5, -20), 5, ivory)
]
r.glFinish()