# Image Superimoposer for CreateML

A tool to generate superimposed images randomly from a subject and background to feed into Apple's CreateML machine learning application.

## Setup

Mirror the following for correct setup.

### Directory Structure
```
Image Superimoposer
 |-- image_create.py
 |-- requirements.txt
 |
 |-- img/
 |    |-- annotations.json (auto-generated/overwritten)
 |    |
 |    |-- subject/
 |    |    | ...
 |    |
 |    |-- background/
 |    |    | ...
 |    |
 |    |-- generated/
```

### Install
1. Setup your virtual environment.
2. Install requirements with `pip`:
```
python3 -m pip install -r requirements.txt
```
