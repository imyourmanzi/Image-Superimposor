# Image Superimoposer for CreateML

A tool to generate superimposed images randomly from a subject and background to feed into Apple's CreateML machine learning application.  This tool creates the image folder with annotations in the format that CreateML expects.

This tool is built with [Pillow](https://pypi.org/project/Pillow/) and supports its file [formats](https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html).  By default, the composite image format is saved in format detected from the background image at the time.  This setting, and others, can changed via command line options listed [below](#usage).

## Setup

Mirror the following for correct setup.

### Directory Structure
```
Image-Superimoposer
├── README.md
├── image_create.py
├── img
│   ├── [annotations.json] (auto-generated; overwritten on run)
│   ├── background
│   │   └── ...
│   ├── [generated] (auto-generated; conflicting filenames will be overwritten)
│   │   └── ...
│   └── subject
│       └── ...
└── requirements.txt
```

### Install
1. Setup your virtual environment (optional).
2. Install requirements with `pip`:
```shell
python3 -m pip install -r requirements.txt
```

## Usage

Ensure the that the script is executable with:
```shell
chmod u+x image_create.py
```

### Command Line Options

```
usage: image_create.py [-h] [-n VARIATIONS] [--no-scale] [-f OUTPUT_FMT] [-v]
                       [-q]
                       label

Generates composite photos for CreateML object recognition from subject and
background images.

positional arguments:
  label                 the name of the label for the subject's annotation

optional arguments:
  -h, --help            show this help message and exit
  -n VARIATIONS, --variations VARIATIONS
                        the number of variations to make with each image and
                        background pair
  --no-scale            do not change the scale of the subject image
                        (unexepected behavior for subject image larger than
                        background image)
  -f OUTPUT_FMT, --output-fmt OUTPUT_FMT
                        a string representing the Pillow library format to
                        save the generated composite image as
  -v, --verbose         increase the verbosity of log output (takes precedence
                        over --quiet)
  -q, --quiet           decrease the verbosity of log output (--verbose takes
                        precedence)
```
