#### Matt Manzi
#### Created: 2020-07-17
#### Overlay each subject image on each background N times, at random
#### positions and sizes, and generate the relevant annotation for Apple's
#### CreateML.

import os
from PIL import Image
import random
import json
import copy

# TODO: add multi-proccessing
# TODO: add command line options

"""
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

N = 1

SCALE_MAX = 80
SCALE_MIN = 5

IMG_TYPE = ".jpg"
IMG_TYPE_PIL = "JPEG"

IMG_DIR = "img"
IMG_SUBJ = "subject"
IMG_BKGD = "background"
IMG_DEST = "generated"
ANO_FILE = "annotations.json"

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

# load image folders
img_dir = os.path.join(os.getcwd(), IMG_DIR)
subj_dir = os.path.join(img_dir, IMG_SUBJ)
background_dir = os.path.join(img_dir, IMG_BKGD)
dest_dir = os.path.join(img_dir, IMG_DEST)

annotations = []

## for each subject
for subj_file in os.listdir(subj_dir):

    ## for each background
    for bkgd_file in os.listdir(background_dir):

        ## N times
        for i in range(N):

            gen_filename = subj_file.rstrip(IMG_TYPE) + "_" + bkgd_file.rstrip(IMG_TYPE) + "-" + str(i) + IMG_TYPE

            # open photos
            subj = Image.open(os.path.join(subj_dir, subj_file))
            bkgd = Image.open(os.path.join(background_dir, bkgd_file))
            subj_w, subj_h = subj.size
            bkgd_w, bkgd_h = bkgd.size

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
                bkgd.save(os.path.join(dest_dir, gen_filename), IMG_TYPE_PIL)
            except IOError:
                print("Cannot save generated image: {}".format(gen_filename))

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
