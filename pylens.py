#!/usr/bin/env python
# PyLens is a free PicLens clone for Linux!
# It's uses Clutter, so it should work on Windows and OS X too.
# It's nowhere near finished yet.
#
# Run it like './pylens.py /full/path/to/your/images/folder'.
# Code was tested with Clutter 0.8.4 & pyclutter 0.8.2

import sys, os, gobject, clutter
from PIL import Image
from clutter import cogl

cache_dir = os.path.expanduser("~")+"/.pylens/"
thumb = [200, 150]

class TextureReflection (clutter.CloneTexture):
    """
    TextureReflection (clutter.CloneTexture)

    An actor that paints a reflection of a texture. The
    height of the reflection can be set in pixels. If set
    to a negative value, the same size of the parent texture
    will be used.

    The size of the TextureReflection actor is by default
    the same size of the parent texture.
    """
    __gtype_name__ = 'TextureReflection'

    def __init__ (self, parent):
        clutter.CloneTexture.__init__(self, parent)
        self._reflection_height = -1

    def set_reflection_height (self, height):
        self._reflection_height = height
        self.queue_redraw()

    def get_reflection_height (self):
        return self._reflection_height
        
    def do_paint (self):
        parent = self.get_parent_texture()
        if (parent is None):
            return

        # get the cogl handle for the parent texture
        cogl_tex = parent.get_cogl_texture()
        if (cogl_tex is None):
            return

        (width, height) = self.get_size()

        # clamp the reflection height if needed
        r_height = self._reflection_height
        if (r_height < 0 or r_height > height):
            r_height = height

        rty = float(r_height / height)

        opacity = self.get_paint_opacity()

        # the vertices are a 6-tuple composed of:
        #  x, y, z: coordinates inside Clutter modelview
        #  tx, ty: texture coordinates
        #  color: a clutter.Color for the vertex
        #
        # to paint the reflection of the parent texture we paint
        # the texture using four vertices in clockwise order, with
        # the upper left and the upper right at full opacity and
        # the lower right and lower left and 0 opacity; OpenGL will
        # do the gradient for us
        vertices = ( \
            (    0,        0, 0, 0.0, rty,   (255, 255, 255, opacity)), \
            (width,        0, 0, 1.0, rty,   (255, 255, 255, opacity)), \
            (width, r_height/2, 0, 1.0,   0.0, (255, 255, 255,       0)), \
            (    0, r_height/2, 0, 0.0,   0.0, (255, 255, 255,       0)), \
        )

        cogl.push_matrix()

        cogl_tex.texture_polygon(vertices=vertices, use_color=True)

        cogl.pop_matrix()
    
def do_focus(actor, event, group):
    group.set_opacity(255)
    
def do_show(actor, event, img):
    stage = actor.get_stage()
    stage_width, stage_height = stage.get_size()
    pic = clutter.Texture(img)
    pic_width, pic_height = pic.get_size()
    if pic_width > stage_width:
        pic.set_size(stage_width, pic_height)
    pic_width, pic_height = pic.get_size()
    if pic_height > stage_height:
        pic.set_size(pic_width, stage_height)
    pic_width, pic_height = pic.get_size()
    pic.set_reactive(True)
    pic.connect('leave-event', do_remove)
    pic.connect('button-press-event', do_remove)
    g = clutter.Group()
    g.add(pic)
    g.set_position((stage_width-pic_width)/2, (stage_height-pic_height)/2)
    stage.add(g)

def do_remove(actor, event):
    g = actor.get_parent()
    g.get_parent().remove(g)

def do_unfocus(actor, event, group):
    group.set_opacity(200)

def do_key(actor, event):
    if event.keyval == 65363: # right
        actor.get_children()[0].move_by(-200, 0)
    elif event.keyval == 65361: # left
        actor.get_children()[0].move_by(200, 0)
    elif event.keyval == 65362: # down
        actor.get_children()[0].move_by(0, 100)
    elif event.keyval == 65364: # up
        actor.get_children()[0].move_by(0, -100)
    elif event.keyval == 113: # q
        clutter.main_quit()
    actor.do_paint(actor)
    
def do_scroll(actor, event):
    if event.direction == clutter.SCROLL_DOWN:
        actor.set_depth(actor.get_depth()-20)
    elif event.direction == clutter.SCROLL_UP:
        actor.set_depth(actor.get_depth()+20)
    elif event.direction == clutter.SCROLL_RIGHT:
        actor.get_children()[0].move_by(-70, 0)
    elif event.direction == clutter.SCROLL_LEFT:
        actor.get_children()[0].move_by(70, 0)
    actor.do_paint(actor)

def main(args):
    try:
        os.mkdir(cache_dir)
    except:
        pass
    stage = clutter.Stage()
    stage.set_perspective(60.0, 1.0, 0.1, 100.0)
    #print stage.get_perspective()
    stage.fullscreen()
    stage.set_color(clutter.Color(0, 0, 0, 255))
    stage.connect('key-press-event', do_key)
    stage.connect('scroll-event', do_scroll)
    stage.connect('destroy', clutter.main_quit)
    stage_width, stage_height = stage.get_size()
    
    files = os.listdir(args[0])
    xpos = 20
    ypos = 40
    count = 1
    wall = clutter.Group()

    for f in files:
        try:
            img = args[0]+"/"+f
            im = Image.open(img)
            im.thumbnail( (thumb[0],thumb[1]), Image.ANTIALIAS)
            im.save(cache_dir+f)
            group = clutter.Group()
            wall.add(group)
            tex = clutter.Texture(cache_dir+f)
            reflect = TextureReflection(tex)
            reflect.set_opacity(120)
            xoffset = (thumb[0]-tex.get_size()[0])/2
            yoffset = (thumb[1]-tex.get_size()[1])/2
            group.add(tex, reflect)
            group.set_positionu(xpos+xoffset, ypos+yoffset)
            reflect.set_positionu(0.0, (tex.get_heightu()+5))
            group.set_reactive(True)
            tex.set_reactive(True)
            group.set_opacity(200)
            tex.connect('enter-event', do_focus, group)
            tex.connect('leave-event', do_unfocus, group)
            tex.connect('button-press-event', do_show, img)
            ypos = ypos+thumb[1]+80
            if count > 2:
                xpos = xpos+thumb[0]+60
                ypos = 40
                count = 0
            count = count+1
        except:
            pass
    stage.add(wall)

    stage.show()
    clutter.main()

    return 0

if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
