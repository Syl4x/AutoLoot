# PixelClicker

PixelClicker is an automated Python script designed to perform clicks based on simultaneous multi-color matching conditions and real-time screen scanning. It is ideal for automating repetitive tasks and game interactions (such as the Albion Online Client).

---

## Features

- **Auto-Dependency Installation:** Automatically checks and installs all missing required Python libraries (`pyautogui`, `keyboard`, `mss`, `numpy`, `pillow`, etc.) upon startup.
- **Triple Color Detection:** Clicks the target location only when all three (3) color detectors match simultaneously.
- **Visual Overlay Boxes:** Displays transparent GUI boundary boxes on the screen to visualize detector positions.
- **Config Auto-Saving:** Automatically saves your configured detector positions and RGB color codes to your local user directory.
- **Safe Mouse Control:** Features an optional mouse-locking mechanism during clicks to prevent manual cursor interference.

---

## Requirements

- Python 3.x installed on your system[cite: 1].
- Windows Operating System (required for Windows API / `ctypes` support)[cite: 1].

---

## Hotkeys & Controls

| Key | Action / Function | Description |
| :--- | :--- | :--- |
| **F3** | Start / Pause | Toggles the automated clicking script on or off[cite: 1]. |
| **F4** | Show / Hide Boxes | Toggles the visual overlay boxes *(Note: Keys F5–F8 only work when boxes are shown)*[cite: 1]. |
| **F5** | Lock Position | Locks the currently selected detector to the mouse cursor's current position[cite: 1]. |
| **F6** | Change Detector | Switches the active detector selection sequentially (Detector 1 -> 2 -> 3)[cite: 1]. |
| **F7** | Type RGB | Opens a console prompt to manually enter an RGB color code for the active detector[cite: 1]. |
| **F8** | Pick Color | Automatically captures and sets the color of the pixel underneath the mouse pointer[cite: 1]. |

---

## How to Check a Pixel Color Code
If you need to find exact color codes for your detectors, follow these steps[cite: 1]:

Take a screenshot of the exact target area where you want to detect the color[cite: 1].

Open MS Paint (or any image editor) and paste the screenshot into it[cite: 1].

Select the Color Picker (Eyedropper) tool and click on your target color[cite: 1].

Go to Edit Colors to view and copy the exact RGB color code values[cite: 1].

Disclaimer
This script is created strictly for educational and automation testing purposes[cite: 1]. Using automation scripts may violate the terms of service of certain applications or games; use it at your own discretion[cite: 1].
## Configuration Settings

You can customize core behavior settings at the top of the script[cite: 1]:

```python
GAME_WINDOW_TITLE = "Albion Online Client"  # Target game or application window title
TOLERANCE = 30                              # Color matching range/deviation threshold (RGB)
SCAN_WIDTH = 80                             # Width of the detector scan box
SCAN_HEIGHT = 30                            # Height of the detector scan box
