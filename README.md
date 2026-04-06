# Photonics Design Engineer (Layout) Exercise

## Summary
This submission implements a public 2x2 MMI-based silicon beamsplitter in GDSFactory using the generic public PDK.

The layout includes:
- a nominal 2x2 MMI splitter test structure,
- a straight-waveguide reference structure,
- a compact DOE targeting 50:50 splitting at 1550 nm.

## Design choices
I selected a 2x2 MMI coupler because it is a standard public passive splitter topology, compact, and appropriate for a first-pass 50:50 design near 1550 nm.

## Measurement concept
The DUT is fiber-coupled using grating couplers. A reference straight-waveguide structure is included to provide a baseline transmission path.

The intended measurement outputs are:
- splitting ratio from the two DUT output powers,
- first-pass excess-loss estimation relative to the reference structure.

For one driven input, if the measured DUT output powers are P1 and P2, the splitting ratios are:

- eta1 = P1 / (P1 + P2)
- eta2 = P2 / (P1 + P2)

A first-pass excess-loss estimate relative to the reference transmission Pref is:

- EL ≈ -10 log10((P1 + P2) / Pref)

## DOE
The DOE sweeps:
- length_mmi: [-0.30, -0.15, 0.00, +0.15, +0.30] um
- width_mmi:  [-0.10,  0.00, +0.10] um

Total DOE count: 15 variants.

A CSV manifest is exported to map each variant name to its geometry.

## Files
- photonics_design_engineer_layout_exercise.py
- photonics_design_engineer_layout_exercise.gds
- doe_variants_manifest.csv
- photonics_design_engineer_layout_exercise.netlist.yml
- optional_screenshot.png

## Notes
This design uses only public GDSFactory components and the generic public PDK.

## Run
To generate the layout and exported files, run:

```bash
python photonics_design_engineer_layout_exercise.py
