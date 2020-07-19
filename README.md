# Image Superimoposer for CreateML

A tool to generate superimposed images randomly from a subject and background to feed into Apple's CreateML machine learning application.

## Setup

Mirror the following for correct setup.

### Directory Structure
```
Image-Superimoposer
├── README.md
├── image_create.py
├── img
│   ├── annotations.json (auto-generated; overwritten on run)
│   ├── background
│   │   └── ...
│   ├── generated (auto-generated; conflicting filenames will be overwritten)
│   │   └── ...
│   └── subject
│       └── ...
└── requirements.txt
```

### Install
1. Setup your virtual environment.
2. Install requirements with `pip`:
```
python3 -m pip install -r requirements.txt
```
