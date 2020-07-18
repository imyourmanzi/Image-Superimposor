#!/usr/bin/env python3
"""
Matt Manzi
Created: 2020-07-17

Overlay each subject image on each background N times, at random
positions and sizes, and generate the relevant annotation for Apple's
CreateML.

Annotation Format:
[
    {
        "annotation": [
            {
                "label": "%LABEL%",
                "coordinates": {
                    "y": %TOP-LEFT-Y%,
                    "x": %TOP-LEFT-X%,
                    "width": %WIDTH%,
                    "height": %HEIGHT%
                }
            }
        ],
        "imagefilename": "%FILENAME%"
    }
]
"""

import logging
from argparse import ArgumentParser

import os
from PIL import Image
import random
import json
import copy

########### TODO: add multi-proccessing


#### MARK: Constants

# generation params
N = 1
SCALE_MAX = 80
SCALE_MIN = 5

# fs structure
IMG_DIR = "img"
IMG_SUBJ = "subject"
IMG_BKGD = "background"
IMG_DEST = "generated"
ANO_FILE = "annotations.json"

# annotations
ANO_TMP = {
    "annotation": [
        {
            "label": "hand-grab",
            "coordinates": {
                "y": None,
                "x": None,
                "width": None,
                "height": None
            }
        }
    ],
    "imagefilename": None
}


#### MARK: Code

# globals init
log = logging.getLogger()

parser = ArgumentParser(description="""
Generates composite photos for CreateML object recognition from subject and
background images.""")
parser.add_argument("label",
    help="the name of the label for the subject's annotation")
parser.add_argument("-n", "--variations",
    help="the number of variations to make with each image and background pair")
parser.add_argument("--no-scale", action="store_true",
    help="do not change the scale of the subject image (unexepected behavior \
    for subject image larger than background image)")


# load image folders
img_dir = os.path.join(os.getcwd(), IMG_DIR)
subj_dir = os.path.join(img_dir, IMG_SUBJ)
background_dir = os.path.join(img_dir, IMG_BKGD)
dest_dir = os.path.join(img_dir, IMG_DEST)

annotations = []

## for each subject
for subj_file in os.listdir(subj_dir):
    subj = Image.open(os.path.join(subj_dir, subj_file))
    subj_w, subj_h = subj.size

    ## for each background
    for bkgd_file in os.listdir(background_dir):
        bkgd = Image.open(os.path.join(background_dir, bkgd_file))
        bkgd_w, bkgd_h = bkgd.size

        ## N times
        for i in range(N):

            gen_filename = subj_file.rstrip(IMG_IN_TYPE) + "_" + bkgd_file.rstrip(IMG_IN_TYPE) + "-" + str(i) + IMG_IN_TYPE

            # pick a random scale (height as percent of background image size)
            scale = random.randint(SCALE_MIN, SCALE_MAX) / 100
            subj_w = int(subj_w * (bkgd_h * scale) / subj_h)
            subj_h = int(bkgd_h * scale)
            subj = subj.resize((subj_w, subj_h))

            # pick a random position for top-left corner (ensure subject stays
            # in bounds of background)
            position_y = random.randint(0, bkgd.size[1] - subj.size[1])
            position_x = random.randint(0, bkgd.size[0] - subj.size[0])

            # save new image
            try:
                bkgd.paste(subj, (position_x, position_y))
                bkgd.save(os.path.join(dest_dir, gen_filename))
            except IOError:
                print("Cannot save generated image: {}".format(gen_filename))

            hand.close()
            bkgd.close()

            # save image annotation
            ano = copy.deepcopy(ANO_TMP)
            ano["imagefilename"] = gen_filename
            ano["annotation"][0]["coordinates"]["y"] = position_y
            ano["annotation"][0]["coordinates"]["x"] = position_x
            ano["annotation"][0]["coordinates"]["width"] = subj_w
            ano["annotation"][0]["coordinates"]["height"] = subj_h
            annotations.append(ano)

# store and close annotations
annotations_file = open(os.path.join(IMG_DIR, ANO_FILE), "w")
annotations_file.write(json.dumps(annotations))
annotations_file.close()


def main():
    init()


main()
