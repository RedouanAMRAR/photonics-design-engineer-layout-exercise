import csv
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4
import gdsfactory as gf
from gdsfactory.generic_tech import get_generic_pdk
#from gdsfactory.gpdk import get_generic_pdk

# Activate the generic public PDK
get_generic_pdk().activate()
gf.clear_cache()

# ----------------------------
# Global design assumptions
# ----------------------------
WAVEGUIDE_XS = "strip"
GC = gf.components.grating_coupler_elliptical_te
ANNOTATION_LAYER = "TEXT"
FLOORPLAN_LAYER = "FLOORPLAN"
FLOORPLAN_MARGIN_UM = 50.0

DOE_MANIFEST_CSV = "doe_variants_manifest.csv"
WORKSPACE_ROOT_MANIFEST_CSV = str(Path("..") / DOE_MANIFEST_CSV)
STRUCTURE_LABEL_INSET_X_UM = 0.0
STRUCTURE_LABEL_INSET_Y_UM = 10.0

# Layout presets (single-point edits)
LAYOUT_PRESETS = {
    "compact": dict(
        DOE_PACK_SPACING_UM=40.0,
        DOE_LABEL_OFFSET_Y_UM=10.0,
        GAP_DUT_TO_REF_UM=140.0,
        GAP_REF_TO_DOE_UM=180.0,
        TITLE_OFFSET_FROM_DUT_UM=180.0,
        NOTE3_OFFSET_FROM_DOE_UM=95.0,
        NOTE4_OFFSET_FROM_DOE_UM=65.0,
        TITLE_TEXT_SIZE=18,
        NOTE_TEXT_SIZE=9,
        LEGEND_TEXT_SIZE=7,
        DOE_LABEL_TEXT_SIZE=5,
    ),
    "spacious": dict(
        DOE_PACK_SPACING_UM=60.0,
        DOE_LABEL_OFFSET_Y_UM=14.0,
        GAP_DUT_TO_REF_UM=220.0,
        GAP_REF_TO_DOE_UM=280.0,
        TITLE_OFFSET_FROM_DUT_UM=260.0,
        NOTE3_OFFSET_FROM_DOE_UM=140.0,
        NOTE4_OFFSET_FROM_DOE_UM=95.0,
        TITLE_TEXT_SIZE=22,
        NOTE_TEXT_SIZE=11,
        LEGEND_TEXT_SIZE=9,
        DOE_LABEL_TEXT_SIZE=6,
    ),
}

LAYOUT_PRESET = "compact"
_p = LAYOUT_PRESETS[LAYOUT_PRESET]

DOE_PACK_SPACING_UM = _p["DOE_PACK_SPACING_UM"]
DOE_LABEL_OFFSET_Y_UM = _p["DOE_LABEL_OFFSET_Y_UM"]
GAP_DUT_TO_REF_UM = _p["GAP_DUT_TO_REF_UM"]
GAP_REF_TO_DOE_UM = _p["GAP_REF_TO_DOE_UM"]
TITLE_OFFSET_FROM_DUT_UM = _p["TITLE_OFFSET_FROM_DUT_UM"]
NOTE3_OFFSET_FROM_DOE_UM = _p["NOTE3_OFFSET_FROM_DOE_UM"]
NOTE4_OFFSET_FROM_DOE_UM = _p["NOTE4_OFFSET_FROM_DOE_UM"]
TITLE_TEXT_SIZE = _p["TITLE_TEXT_SIZE"]
NOTE_TEXT_SIZE = _p["NOTE_TEXT_SIZE"]
LEGEND_TEXT_SIZE = _p["LEGEND_TEXT_SIZE"]
DOE_LABEL_TEXT_SIZE = _p["DOE_LABEL_TEXT_SIZE"]

MMI_NOMINAL = dict(
    width_taper=1.0,
    length_taper=10.0,
    length_mmi=5.5,
    width_mmi=2.5,
    gap_mmi=0.25,
    cross_section=WAVEGUIDE_XS,
)


def build_doe_manifest_rows(exported_at_utc: str = "", export_id: str = ""):
    rows = []
    length_deltas = [-0.30, -0.15, 0.00, 0.15, 0.30]
    width_deltas = [-0.10, 0.00, 0.10]
    index = 0

    for wd in width_deltas:
        for ld in length_deltas:
            length_mmi = MMI_NOMINAL["length_mmi"] + ld
            width_mmi = MMI_NOMINAL["width_mmi"] + wd
            rows.append(
                dict(
                    index=index,
                    length_delta_um=ld,
                    width_delta_um=wd,
                    length_mmi_um=length_mmi,
                    width_mmi_um=width_mmi,
                    variant_name=f"mmi2x2_Ld{ld:+.2f}_Wd{wd:+.2f}".replace(".", "p"),
                    exported_at_utc=exported_at_utc,
                    export_id=export_id,
                )
            )
            index += 1
    return rows


def export_doe_manifest_csv(csv_path: str = DOE_MANIFEST_CSV, rows=None):
    rows_to_write = rows
    if rows_to_write is None:
        exported_at_utc = (
            datetime.now(timezone.utc)
            .isoformat(timespec="seconds")
            .replace("+00:00", "Z")
        )
        export_id = str(uuid4())
        rows_to_write = build_doe_manifest_rows(
            exported_at_utc=exported_at_utc,
            export_id=export_id,
        )

    path = Path(csv_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "index",
        "length_delta_um",
        "width_delta_um",
        "length_mmi_um",
        "width_mmi_um",
        "variant_name",
        "exported_at_utc",
        "export_id",
    ]
    with open(path, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows_to_write)

    return rows_to_write, str(path.resolve())


def place_label_in_instance_bbox(parent, target_ref, text, size, layer, inset_x_um=0.0, inset_y_um=10.0):
    """Place a label above the target instance bbox, centered horizontally."""
    label = parent << gf.components.text(
        text=text,
        size=size,
        layer=layer,
    )
    target_center_x = (target_ref.dxmin + target_ref.dxmax) / 2
    label_width = label.dxmax - label.dxmin
    label.movex(target_center_x - label_width / 2 + inset_x_um)
    label.movey(target_ref.dymax + inset_y_um)
    return label


@gf.cell
def mmi2x2_nominal():
    c = gf.Component("mmi2x2_nominal")
    mmi = c << gf.components.mmi2x2(**MMI_NOMINAL)
    c.add_ports(mmi.ports)
    c.info["device"] = "2x2 MMI"
    c.info["target_wavelength_nm"] = 1550
    c.info["purpose"] = "Nominal 2x2 50:50 beamsplitter"
    return c


@gf.cell
def splitter_test_structure():
    base = gf.routing.add_fiber_array(
        component=mmi2x2_nominal(),
        grating_coupler=GC,
        with_loopback=False,
    )
    c = gf.Component("splitter_test_structure")
    base_ref = c << base
    c.add_ports(base_ref.ports)
    c.info["measurement"] = (
        "Drive one input; measure both output powers for split ratio. "
        "Unused input can be terminated in the experiment if needed."
    )
    return c


@gf.cell
def reference_structure(length: float = 300.0):
    base = gf.routing.add_fiber_array(
        component=gf.components.straight(length=length, cross_section=WAVEGUIDE_XS),
        grating_coupler=GC,
        with_loopback=False,
    )
    c = gf.Component(f"reference_wg_L{int(length)}")
    base_ref = c << base
    c.add_ports(base_ref.ports)
    c.info["measurement"] = "Reference transmission structure"
    c.info["wg_length_um"] = length
    return c


@gf.cell
def mmi2x2_variant(length_delta: float = 0.0, width_delta: float = 0.0):
    params = dict(MMI_NOMINAL)
    params["length_mmi"] = MMI_NOMINAL["length_mmi"] + length_delta
    params["width_mmi"] = MMI_NOMINAL["width_mmi"] + width_delta

    c = gf.Component(
        f"mmi2x2_Ld{length_delta:+.2f}_Wd{width_delta:+.2f}".replace(".", "p")
    )
    mmi = c << gf.components.mmi2x2(**params)
    c.add_ports(mmi.ports)
    c.info["device"] = "2x2 MMI DOE"
    c.info["target_wavelength_nm"] = 1550
    c.info["length_delta_um"] = length_delta
    c.info["width_delta_um"] = width_delta
    c.info["length_mmi_um"] = params["length_mmi"]
    c.info["width_mmi_um"] = params["width_mmi"]
    return c


@gf.cell
def doe_array():
    c = gf.Component("mmi2x2_doe_array")
    manifest_rows = build_doe_manifest_rows()

    devices = []
    for row in manifest_rows:
        ld = row["length_delta_um"]
        wd = row["width_delta_um"]
        label_text = (
            f"dL={ld:+.2f}um dW={wd:+.2f}um | "
            f"L={row['length_mmi_um']:.2f}um W={row['width_mmi_um']:.2f}um"
        )

        base = gf.routing.add_fiber_array(
            component=mmi2x2_variant(length_delta=ld, width_delta=wd),
            grating_coupler=GC,
            with_loopback=False,
        )

        unit = gf.Component(f"doe_unit_Ld{ld:+.2f}_Wd{wd:+.2f}".replace(".", "p"))
        base_ref = unit << base
        place_label_in_instance_bbox(
            parent=unit,
            target_ref=base_ref,
            text=label_text,
            size=DOE_LABEL_TEXT_SIZE,
            layer=ANNOTATION_LAYER,
            inset_x_um=0.0,
            inset_y_um=DOE_LABEL_OFFSET_Y_UM,
        )
        devices.append(unit)

    packed = gf.pack(
        devices,
        spacing=DOE_PACK_SPACING_UM,
        sort_by_area=False,
    )[0]
    ref = c << packed
    c.add_ports(ref.ports)
    c.info["doe"] = "MMI length/width sweep around nominal public design"
    c.info["doe_count"] = len(manifest_rows)
    c.info["doe_manifest_csv"] = DOE_MANIFEST_CSV
    return c


@gf.cell
def top_mask():
    c = gf.Component("photonics_design_engineer_layout_exercise")

    dut = c << splitter_test_structure()
    ref = c << reference_structure(length=300.0)
    doe = c << doe_array()

    ref.movey((dut.dymin - GAP_DUT_TO_REF_UM) - ref.dymax)
    doe.movey((ref.dymin - GAP_REF_TO_DOE_UM) - doe.dymax)

    target_cx = (doe.dxmin + doe.dxmax) / 2
    dut.movex(target_cx - (dut.dxmin + dut.dxmax) / 2)
    ref.movex(target_cx - (ref.dxmin + ref.dxmax) / 2)

    title = c << gf.components.text(
        text="Photonics Design Engineer (Layout) Exercise",
        size=TITLE_TEXT_SIZE,
        layer=ANNOTATION_LAYER,
    )
    title.movey(dut.dymax + TITLE_OFFSET_FROM_DUT_UM)
    title.movex(target_cx - (title.dxmin + title.dxmax) / 2)

    place_label_in_instance_bbox(
        parent=c,
        target_ref=dut,
        text="Nominal 2x2 MMI splitter test structure",
        size=NOTE_TEXT_SIZE,
        layer=ANNOTATION_LAYER,
        inset_x_um=STRUCTURE_LABEL_INSET_X_UM,
        inset_y_um=STRUCTURE_LABEL_INSET_Y_UM,
    )

    place_label_in_instance_bbox(
        parent=c,
        target_ref=ref,
        text="Reference straight waveguide",
        size=NOTE_TEXT_SIZE,
        layer=ANNOTATION_LAYER,
        inset_x_um=STRUCTURE_LABEL_INSET_X_UM,
        inset_y_um=STRUCTURE_LABEL_INSET_Y_UM,
    )

    note3 = c << gf.components.text(
        text="DOE: sweep MMI length and width around nominal for 1550 nm targeting",
        size=NOTE_TEXT_SIZE,
        layer=ANNOTATION_LAYER,
    )
    note3.movey(doe.dymax + NOTE3_OFFSET_FROM_DOE_UM)
    note3.movex(target_cx - (note3.dxmin + note3.dxmax) / 2)

    note4 = c << gf.components.text(
        text="DOE labels: dL/dW are deltas from nominal; L/W are absolute MMI dimensions",
        size=LEGEND_TEXT_SIZE,
        layer=ANNOTATION_LAYER,
    )
    note4.movey(doe.dymax + NOTE4_OFFSET_FROM_DOE_UM)
    note4.movex(target_cx - (note4.dxmin + note4.dxmax) / 2)

    x0 = c.dxmin - FLOORPLAN_MARGIN_UM
    y0 = c.dymin - FLOORPLAN_MARGIN_UM
    x1 = c.dxmax + FLOORPLAN_MARGIN_UM
    y1 = c.dymax + FLOORPLAN_MARGIN_UM
    c.add_polygon(
        [(x0, y0), (x1, y0), (x1, y1), (x0, y1)],
        layer=FLOORPLAN_LAYER,
    )

    c.info["floorplan_layer"] = FLOORPLAN_LAYER
    c.info["floorplan_margin_um"] = FLOORPLAN_MARGIN_UM
    c.info["author_note"] = (
        "Uses public GDSFactory generic-PDK MMI concept and compact DOE only."
    )
    return c


if __name__ == "__main__":
    manifest_rows, manifest_path = export_doe_manifest_csv(DOE_MANIFEST_CSV)
    export_run_id = manifest_rows[0]["export_id"] if manifest_rows else ""
    _, workspace_manifest_path = export_doe_manifest_csv(
        WORKSPACE_ROOT_MANIFEST_CSV,
        rows=manifest_rows,
    )

    print(f"DOE manifest written to {manifest_path} with {len(manifest_rows)} rows")
    print(f"DOE manifest copy written to {workspace_manifest_path}")
    print(f"DOE export_id: {export_run_id}")

    c = top_mask()

    gds_path = "photonics_design_engineer_layout_exercise.gds"
    c.write_gds(gds_path)
    print(f"GDS written to {Path(gds_path).resolve()}")

    netlist_path = Path("photonics_design_engineer_layout_exercise.netlist.yml").resolve()

    if hasattr(c, "get_netlist") and hasattr(c, "write_netlist") and callable(c.write_netlist):
        try:
            netlist = c.get_netlist()
            c.write_netlist(netlist, netlist_path)
            print(f"Netlist written to {netlist_path} (traceability enabled)")
            print(f"Netlist exists after write: {netlist_path.exists()}")
        except Exception as error:
            print(f"Netlist export skipped: {error}")
    else:
        print("Netlist export not supported in this installed gdsfactory version.")

    c.show()