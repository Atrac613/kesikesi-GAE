# -*- coding: utf-8 -*-

from google.appengine.api import images

def convert_square(image_src, width, height):
    image = images.Image(image_src)
            
    org_width = float(image.width)
    org_height = float(image.height)

    scale_w = width / org_width
    scale_h = height / org_height
    scale = scale_h if scale_w < scale_h else scale_w

    thumb_width = int(org_width * scale)
    thumb_height = int(org_height * scale)
    image.resize(thumb_width, thumb_height)

    x = (thumb_width - width) / 2.0
    y = (thumb_height - height) / 2.0
    image.crop(x/thumb_width, y/thumb_height, 1.0-(x/thumb_width), 1.0-(y/thumb_height))
            
    return image.execute_transforms(output_encoding=images.PNG)