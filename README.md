# Terminator HUD

A Desktop camera HUD that mimics famous Terminator franchise visuals using PySide6 and OpenCV. It presents a live camera feed with original black-and-red phosphor treatment. The color treatment is a visual effect, not thermal imaging.

## Features

- Captures frames from the USB camera
- Converts the camera image to red-phosphor/ember color palette like in the movies.
- Prints text into one of nine overlay slots with a timed character sequence, optional blinking, and automatic expiration for added immersion.
- Runs a XY grid scan animation and automatic expiration.

## Run

python3 src/main.py

This project is in early development. Issues and missing feature are expected :)

## Project Layout

- `src/main.py` Main application loop.
- `src/optical_unit.py` This is captures camera frames, acts as "Terminator visual feed".
- `src/hud.py` processes camera frames, renders the HUD and decorations.
