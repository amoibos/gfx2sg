#!/usr/bin/env python
# coding: utf-8

#license: ISC
#copyright: darktrym

import os
from os import path
import sys
import struct
from PIL import Image, ImageOps
from collections import defaultdict 

# 32 x 24 tiles filling a screen where a tile 8x8 tile dimension
# for the SG the color depth is 1bit = 2 colors per tile line
PAL_COLORS = 1  # in bits
MAX_X = 256
MAX_Y = 192

TILE_WIDTH = 8
TILE_HEIGHT = 8

# first color is used for transparent
SG_COLOR_PALETTE = [(0x00, 0x00, 0x00), (0x00, 0x00, 0x00), (0x21, 0xC8, 0x42), (0x5E, 0xDC, 0x78),
                    (0x54, 0x55, 0xED), (0x7D, 0x76, 0xFC), (0xD4, 0x52, 0x4D), (0x42, 0xEB, 0xF5),
                    (0xFC, 0x55, 0x54), (0xFF, 0x79, 0x78), (0xD4, 0xC1, 0x54), (0xE6, 0xCE, 0x80),
                    (0x21, 0xB0, 0x3B), (0xC9, 0x5B, 0xBA), (0xCC, 0xCC, 0xCC), (0xFF, 0xFF, 0xFF)]


def check_color_limit(img, limit):
    width, height = img.size
    for tile_y in range(height // TILE_HEIGHT):
        for tile_x in range(width // TILE_WIDTH):
            region = img.crop((tile_x * TILE_WIDTH, tile_y * TILE_HEIGHT, (tile_x + 1) * TILE_WIDTH,
                                       (tile_y + 1) * TILE_HEIGHT))
            #There is no check if there are more than 2 color per tile row!
            #In this case, the 2 colors that occur most frequently are used
            if len(region.getcolors()) > limit:
                return False
    return True


def nearest_color(subjects, query):
    return min(subjects, key=lambda subject: sum((s - q) ** 2 for s, q in zip(subject, query)))

def convert(output_name):
    with Image.open(output_name) as img:
        width, height = img.size
        #import pdb; pdb.set_trace()
        color_cnt = len(img.getcolors(img.size[0]*img.size[1]))
        
        # do not use transparency color
        if not check_color_limit(img, 15):
            print("too many colors in one tile, platform supports only 15 colors per tile", file=sys.stderr)
            return

        if width > MAX_X or height > MAX_Y:
            print("invalid image dimensions, platform supports maximal resolution 256x192", file=sys.stderr)
            return

        # convert single band color representation to RGB
        if "".join(img.getbands()) != "RGB":
            img = img.convert('RGB')

        # store color palette information
        color_map = {}
        # translate color information to corresponding index of color palette
        color_index = {(0, 0, 0): 0}

        for idx, color in enumerate(img.getcolors()):
            #import pdb; pdb.set_trace()
            color_index[color[-1]] = SG_COLOR_PALETTE.index(nearest_color(SG_COLOR_PALETTE, color[-1]))

        filename = path.splitext(output_name)[0]
        # write tiles data
        with open(filename + " (tiles).bin", "wb") as tile_writer, open(filename + " (palette).bin", "wb") as palette_writer:
            for tile_y in range(height // TILE_HEIGHT):
                for tile_x in range(width // TILE_WIDTH):
                    region = img.crop((tile_x * TILE_WIDTH, tile_y * TILE_HEIGHT, (tile_x + 1) * TILE_WIDTH,
                                       (tile_y + 1) * TILE_HEIGHT))
                    # no idea why I have to mirror the tile
                    region = ImageOps.mirror(region)
                    data = [color_index[item] for item in region.getdata()]
                    for pos in range(0, len(data), TILE_HEIGHT):                        
                        colors_in_line = defaultdict(int)
                        # get color distribution in line of the current tile
                        for column in range(TILE_WIDTH):
                            colors_in_line[data[pos + column]] += 1
                        # color with the highest amount in line is background color, 
                        # second place is foreground color 
                        # if there is no second place then use transparent color    
                        #colors = sorted(colors_in_line.items(), key=lambda x: x[-1])
                        
                        # use color index for ordering
                        colors = sorted(colors_in_line.items(), key=lambda x: x[-1])
                        colors.insert(0, (0, 0))    
                        foreground = colors[-1][0]
                        background = colors[-2][0]
                        
                        val = 0
                        for column in range(TILE_WIDTH):
                            val += (int(data[pos + column] == background)) << column
                            
                        tile_writer.write(struct.pack('B', val)) 
                        palette_writer.write(struct.pack('B', (background << 4) + foreground))
        

def process(args):
    if os.path.exists(args[1]):
        convert(args[1])


def main():
    if len(sys.argv) > 1:
        if path.exists(sys.argv[1]):
            process(sys.argv)
        else:
            print("file %s doesn't exist" % (sys.argv[1]), file=sys.stderr)
    else:
        print("not enough arguments, filename is missing", file=sys.stderr)


if __name__ == '__main__':
    main()
