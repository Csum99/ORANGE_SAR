# Testing Backprojection with Simulated SAR Data

This guide explains how to test the backprojection algorithm using the provided Marathon simulated SAR datasets.

## 1. Download the Marathon Test Data

Download all Marathon simulation files from:

https://drive.google.com/drive/folders/1kU5SUv6a0zA-vyFztf8ydc8uSUS-_Odo?usp=drive_link

## 2. Create the Marathon Directory

Inside the `backprojection` directory, create a folder named `marathon`:

```
ORANGE_SAR/
└── backprojection/
    └── marathon/
```

Copy all downloaded `.pkl` files into this folder.

## 3. Navigate to the Backprojection Directory

```bash
cd ORANGE_SAR/backprojection
```

## 4. Run Backprojection

Run backprojection on any Marathon dataset using:

```bash
python3 backprojection.py marathon/marathon_#.pkl x_min x_max x_resolution y_min y_max y_resolution -p
```

For example:

```bash
python3 backprojection.py marathon/marathon_21.pkl -100 100 0.5 -100 100 0.5 -p
```

where:

- `x_min` – minimum x-coordinate (m)
- `x_max` – maximum x-coordinate (m)
- `x_resolution` – x-axis pixel spacing (m)
- `y_min` – minimum y-coordinate (m)
- `y_max` – maximum y-coordinate (m)
- `y_resolution` – y-axis pixel spacing (m)
- `-p` – displays the reconstruction progress bar

## Notes

- Each Marathon dataset contains a different hidden image located at a different position in the scene.
- If the reconstructed image appears blank, the target is likely outside the selected reconstruction window.
- Start with a **large search area** (e.g., `-100` to `100` m) and then reduce the bounds once the target has been located.
- The five-point scatter dataset is a good sanity check to verify that the backprojection pipeline is functioning correctly before testing the Marathon datasets.
- The reconstructed image may appear to have low contrast. Reducing the display's color dynamic range can make the hidden image easier to see without affecting the reconstruction itself.
