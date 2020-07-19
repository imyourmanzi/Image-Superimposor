#!/usr/bin/env python3
"""
Author: Matt Manzi
Created: 2020-07-17

Description:
Overlay each subject image on each background N times, at random positions and
sizes, and generate the relevant annotation for Apple's CreateML.  The generated
image file will have the format of the background image that is used.

Usage:
./image_create.py [-h]
                  [--color-temp {1000,1500,2000,2500,3000,3500,4000,4500,5000,5500,6000,6500,7000,7500,8000,8500,9000,9500,10000}]
                  [-f OUTPUT_FMT] [--inset-bottom INSET_BOTTOM]
                  [--inset-left INSET_LEFT] [--inset-right INSET_RIGHT]
                  [--inset-top INSET_TOP] [-n VARIATIONS] [--no-scale] [-q] [-v]
                  label

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

TODOS:
    - (future) multiprocessing for speed (split photo batches by background)
    - (future) subject image rotation
"""

import logging, os, time, copy, random, json
from argparse import ArgumentParser
from PIL import Image




################################## CONSTANTS ##################################


# generation params
N = 10
SCALE_MAX = 80
SCALE_MIN = 5
COLOR_TEMPS = {
    1000: (255,56,0),
    1500: (255,109,0),
    2000: (255,137,18),
    2500: (255,161,72),
    3000: (255,180,107),
    3500: (255,196,137),
    4000: (255,209,163),
    4500: (255,219,186),
    5000: (255,228,206),
    5500: (255,236,224),
    6000: (255,243,239),
    6500: (255,249,253),
    7000: (245,243,255),
    7500: (235,238,255),
    8000: (227,233,255),
    8500: (220,229,255),
    9000: (214,225,255),
    9500: (208,222,255),
    10000: (204,219,255)
} # from http://www.vendian.org/mncharity/dir3/blackbody/


# fs structure
IMG_DIR = "img"
IMG_SUBJ = "subject"
IMG_BKGD = "background"
IMG_DEST = "generated"
ANO_FILE = "annotations.json"


# inset indicies
TOP = 0
RIGHT = 1
BOTTOM = 2
LEFT = 3


# other
VERBOSITY = logging.WARNING



#################################### CODE ####################################




#### MARK: Globals Init

logging.basicConfig(
    level=VERBOSITY,
    format="%(levelname)s: %(message)s"
)
log = logging.getLogger("Image-Superimposer")

parser = ArgumentParser(description="""
Generates composite photos for CreateML object recognition from subject and
background images.""")
parser.add_argument("label",
    help="the name of the label for the subject's annotation")
parser.add_argument("--color-temp",
    choices=COLOR_TEMPS.keys(),
    type=int,
    help="the color temperature to convert all images to")
parser.add_argument("-f", "--output-fmt",
    default=None,
    help="a string representing the Pillow library format to save the \
    generated composite image as")
parser.add_argument("--inset-bottom",
    type=int,
    help="percentage of the subject image's height to exclude in the \
    annotation from the bottom of the image (range: 1–99%%)")
parser.add_argument("--inset-left",
    type=int,
    help="percentage of the subject image's width to exclude in the \
    annotation from the left of the image (range: 1–99%%)")
parser.add_argument("--inset-right",
    type=int,
    help="percentage of the subject image's width to exclude in the \
    annotation from the right of the image (range: 1–99%%)")
parser.add_argument("--inset-top",
    type=int,
    help="percentage of the subject image's height to exclude in the \
    annotation from the top of the image (range: 1–99%%)")
parser.add_argument("-n", "--variations",
    type=int,
    default=N,
    help="the number of variations to make with each image and background pair")
parser.add_argument("--no-scale",
    action="store_true",
    help="do not change the scale of the subject image (unexepected behavior \
    for subject image larger than background image)")
parser.add_argument("-q", "--quiet",
    action="count",
    default=0,
    help="decrease the verbosity of log output (--verbose takes precedence)")
parser.add_argument("-v", "--verbose",
    action="count",
    default=0,
    help="increase the verbosity of log output (takes precedence over --quiet)")
args = parser.parse_args()


# set user log level
if args.verbose:
    # max is to ensure that granularity does not cross into NOTSET
    log.setLevel(max(VERBOSITY - (args.verbose * logging.DEBUG), logging.DEBUG))
elif args.quiet:
    log.setLevel(VERBOSITY + (args.quiet * logging.DEBUG))


# sanitize insets
if args.inset_top and (args.inset_top > 99 or args.inset_top < 1):
    log.warning("Ignoring top inset of %d%%", args.inset_top)
    args.inset_top = None

if args.inset_right and (args.inset_right > 99 or args.inset_right < 1):
    log.warning("Ignoring right inset of %d%%", args.inset_right)
    args.inset_right = None

if args.inset_bottom and (args.inset_bottom > 99 or args.inset_bottom < 1):
    log.warning("Ignoring bottom inset of %d%%", args.inset_bottom)
    args.inset_bottom = None

if args.inset_left and (args.inset_left > 99 or args.inset_left < 1):
    log.warning("Ignoring left inset of %d%%", args.inset_left)
    args.inset_left = None




#### MARK: Script Execution

def main():


    # set annotation label
    ano_tmp = {
        "annotation": [
            {
                "label": args.label,
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
    annotations = []
    log.debug("Using label: %s", args.label)

    insets = (
        args.inset_top,
        args.inset_right,
        args.inset_bottom,
        args.inset_left
    )
    log.debug("Using insets: %s", insets)


    # load image folders
    img_dir = os.path.join(os.getcwd(), IMG_DIR)
    subj_dir = os.path.join(img_dir, IMG_SUBJ)
    background_dir = os.path.join(img_dir, IMG_BKGD)
    dest_dir = os.path.join(img_dir, IMG_DEST)


    # ensure dest directory exists
    try:
        os.mkdir(dest_dir)

    except FileExistsError:
        log.debug("Destination directory %s exists, no action", dest_dir)


    log.info("===================Begin Image Processing===================")
    started = time.time()


    # for each background
    for bkgd_file in os.listdir(background_dir):
        log.debug("Opening background file: %s", bkgd_file)

        bkgd_p = Image.open(os.path.join(background_dir, bkgd_file))
        log.debug("Opened background: %s", bkgd_file)

        bkgd_ext = bkgd_file.split(".")[-1]
        bkgd_file = bkgd_file.rstrip("." + bkgd_ext)
        log.debug("Stripped background ext: %s", bkgd_ext)

        # convert background color temp
        if args.color_temp:
            bkgd_tmp = convertColorTemperature(bkgd_p, args.color_temp)
            bkgd_p.close()
            bkgd_p = bkgd_tmp


        # for each subject
        for subj_file in os.listdir(subj_dir):
            log.debug("Opening subject file: %s", subj_file)

            subj_p = Image.open(os.path.join(subj_dir, subj_file))
            log.debug("Opened subject: %s", subj_file)

            subj_ext = subj_file.split(".")[-1]
            subj_file = subj_file.rstrip("." + subj_ext)
            log.debug("Stripped subject ext: %s", subj_ext)

            # convert background color temp
            if args.color_temp:
                subj_tmp = convertColorTemperature(subj_p, args.color_temp)
                subj_p.close()
                subj_p = subj_tmp


            # for N variations
            for i in range(args.variations):
                log.debug("Started variation: %d", i)

                ano = copy.deepcopy(ano_tmp)
                log.debug("Created template annotation deep copy")


                # compose filename
                gen_ext = args.output_fmt.lower() \
                    if args.output_fmt \
                    else bkgd_ext
                gen_filename = ".".join([subj_file, bkgd_file, str(i), gen_ext])
                ano["imagefilename"] = gen_filename
                log.debug("Set generated filename: %s", gen_filename)


                # create composite image
                subj_tmp = subj_p
                # temporary subject (points to original) #
                if not args.no_scale:
                    log.debug("Will scale subject")
                    subj_tmp = scaleToBackground(subj_tmp, bkgd_p, ano, insets)
                    # temporary subject is now separate, original untouched #

                pos_x, pos_y = placeOnBackground(subj_tmp, bkgd_p, ano, insets)

                bkgd_tmp = bkgd_p.copy()
                # temporary background copied for paste, original untouched #
                bkgd_tmp.paste(subj_tmp, (pos_x, pos_y))


                # save new image and annotation
                try:
                    bkgd_tmp.save(os.path.join(dest_dir, gen_filename),
                        format=args.output_fmt)
                    annotations.append(ano)

                except ValueError:
                    log.info("Unable to determine file format")
                    log.warning("Skipping: %s", gen_filename)

                except OSError:
                    log.info("Unable to write composite image to disk: %s",
                        gen_filename)
                    log.warning("Skipping: %s", gen_filename)

                finally:
                    # close temporary images
                    bkgd_tmp.close()
                    if subj_tmp != subj_p:
                        subj_tmp.close()
                    log.debug("Closed temporary images")


            # done with this subject
            subj_p.close()
            log.debug("Closed subject: %s", subj_file)


        # done with this background
        bkgd_p.close()
        log.debug("Closed background: %s", bkgd_file)


    log.info("====================End Image Processing====================")
    log.info("Elapsed Time: %0.4fs", (time.time() - started))


    # store annotations
    annotations_file = open(os.path.join(dest_dir, ANO_FILE), "w")
    annotations_file.write(json.dumps(annotations))
    annotations_file.close()
    log.debug("Wrote annotations to file: %s", ANO_FILE)




#### MARK: Helper functions

def scaleToBackground(subj_p, bkgd_p, annotation, insets):
    """Scale the subject image up or down, relative to the background

    Returns:
        Image
        in the new size
    """
    subj_w, subj_h = subj_p.size
    bkgd_w, bkgd_h = bkgd_p.size

    # pick a random scale (height as percent of background image size)
    scale = random.randint(SCALE_MIN, SCALE_MAX) / 100
    log.debug("Set subject scale: %f", scale)
    subj_w = int(subj_w * (bkgd_h * scale) / subj_h)
    subj_h = int(bkgd_h * scale)
    log.debug("Set subject sizes (w x h): (%d, %d)", subj_w, subj_h)

    image = subj_p.resize((subj_w, subj_h))

    # update annotation
    if insets[RIGHT]:
        subj_w -= int((insets[RIGHT] / 100) * subj_w)
        log.debug("Applied right-side inset of %d%%", insets[RIGHT])

    if insets[LEFT]:
        subj_w -= int((insets[LEFT] / 100) * subj_w)
        log.debug("Applied left-side inset of %d%% to width", insets[LEFT])

    if insets[TOP]:
        subj_h -= int((insets[TOP] / 100) * subj_h)
        log.debug("Applied top-side inset of %d%% to height", insets[TOP])

    if insets[BOTTOM]:
        subj_h -= int((insets[BOTTOM] / 100) * subj_h)
        log.debug("Applied bottom-side inset of %d%%", insets[BOTTOM])

    annotation["annotation"][0]["coordinates"]["width"] = subj_w
    annotation["annotation"][0]["coordinates"]["height"] = subj_h
    log.debug("Updated annotation sizes")

    return image




def convertColorTemperature(img_p, temp):
    """Adjusts the image to match the chosen color temperature

    This function was inspired by this StackOverflow answer:
    https://stackoverflow.com/a/11888449

    Returns:
        Image
        the color-temperature-adjusted image
    """
    r, g, b = COLOR_TEMPS[temp]
    matrix = (
        r/255.0, 0.0,     0.0,     0.0,
        0.0,     g/255.0, 0.0,     0.0,
        0.0,     0.0,     b/255.0, 0.0
    )
    return img_p.convert('RGB', matrix)




def placeOnBackground(subj_p, bkgd_p, annotation, insets):
    """Chooses a position for the subject image on the background

    Returns:
        (int, int)
        the (x, y) coordinates of the top-left subject image corner
    """
    subj_w, subj_h = subj_p.size
    bkgd_w, bkgd_h = bkgd_p.size

    # pick a random position for top-left corner (ensure subject stays
    # in bounds of background)
    position_x = random.randint(0, bkgd_w - subj_w)
    position_y = random.randint(0, bkgd_h - subj_h)
    log.debug("Set subject position (x, y): (%d, %d)", position_x, position_y)

    image_x, image_y = (position_x, position_y)

    # update annotation
    if insets[LEFT]:
        position_x += int((insets[LEFT] / 100) * subj_w)
        log.debug("Applied left-side inset of %d%% to x-coord", insets[LEFT])

    if insets[TOP]:
        position_y -= int((insets[TOP] / 100) * subj_h)
        log.debug("Applied top-side inset of %d%% to y-coord", insets[TOP])

    annotation["annotation"][0]["coordinates"]["y"] = position_y
    annotation["annotation"][0]["coordinates"]["x"] = position_x
    log.debug("Updated annotation position")

    return (image_x, image_y)



if __name__ == "__main__":
    main()
