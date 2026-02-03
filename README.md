# PCB Trace Cross-Section Visualizer

A Python GUI application for generating BMP images of various PCB trace cross-sections with accurate geometric representations.

## Features

- **Five trace types supported:**
  - Microstrip
  - Stripline
  - Differential Pair
  - Coplanar Differential Pair
  - Coplanar Waveguide

- **Customizable dimensions:**
  - Trace width and thickness
  - Substrate height
  - Spacing (for differential pairs)
  - Ground gaps and widths
  - Solder mask thickness

- **Professional visualization:**
  - Color-coded materials (copper, substrate, solder mask)
  - Accurate cross-sectional geometry
  - Grid and dimensional labels
  - High-resolution BMP export (300 DPI)

## Installation

### Using Conda (Recommended)

1. Create the conda environment:
```bash
conda env create -f environment.yml
```

2. Activate the environment:
```bash
conda activate pcb-trace-viz
```

### Using pip (Alternative)

```bash
pip install numpy matplotlib pillow
```

## Usage

1. Run the application:
```bash
python pcb_trace_visualizer.py
```

2. Select a trace type from the radio buttons

3. Enter the desired dimensions (in millimeters)

4. Click "Generate" to visualize the cross-section

5. Click "Save BMP" to export the image

## Default Dimensions

The application provides sensible defaults for common PCB specifications:
- Trace width: 0.4-0.5 mm (typical for controlled impedance)
- Trace thickness: 0.035 mm (1 oz copper)
- Substrate height: 1.6 mm (standard FR-4)
- Solder mask: 0.025 mm

## Trace Types Explained

### Microstrip
Single-ended trace on the surface of a PCB with ground plane below.

### Stripline
Trace embedded between two ground planes within the PCB.

### Differential Pair
Two parallel traces for differential signaling (e.g., USB, Ethernet).

### Coplanar Differential Pair
Differential pair with ground planes on the same layer.

### Coplanar Waveguide
Single trace with ground planes on the same layer on both sides.

## Export Format

- Format: BMP (Bitmap)
- Resolution: 300 DPI
- Background: Light gray for clarity
- Color-coded layers for easy identification

## Requirements

- Python 3.11+
- NumPy
- Matplotlib
- Tkinter (usually included with Python)
- Pillow

## License

This tool is provided as-is for educational and engineering purposes.
