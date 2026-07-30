"""
Faz 1 - Adim 5: scene.json'u okuyup, pLDDT'ye gore renklendirilmis
bir protein render'i uretir.

Bu script normal Python'la degil, BLENDER'IN KENDI ICINDEKI Python
yorumlayicisiyla calisir. Terminalden degil, Blender uzerinden
calistirilir -- asagidaki komuta bak.

Kullanim (terminalden, Blender kurulu oldugu varsayilarak):
    blender --background --python blender_render.py -- data/scene_P69905.json

--background : Blender'i arayuz acmadan, arka planda calistirir
--python     : bu dosyayi Blender'in Python yorumlayicisiyla calistir
--           : bundan sonraki argumanlar Blender'a degil, bu script'e gider
"""

import json
import sys
from pathlib import Path

import bpy


def parse_args() -> Path:
    """Komut satirindaki '--' isaretinden sonraki argumani (scene.json yolu) okur."""
    if "--" not in sys.argv:
        raise ValueError("Kullanim: blender --background --python blender_render.py -- <scene.json>")
    args_after_dashdash = sys.argv[sys.argv.index("--") + 1:]
    if not args_after_dashdash:
        raise ValueError("Scene dosyasinin yolunu belirtmelisin.")
    # .resolve() goreli yolu (orn. ..\data\scene.json) MUTLAK yola cevirir.
    # Bunu yapmazsak, cikti dosyasi Blender'in kendi calisma dizinine gore
    # kaydedilir -- bu da terminaldeki bulundugun klasorden FARKLI olabilir
    # ve dosyayi "kaybetmis" gibi hissettirir.
    return Path(args_after_dashdash[0]).resolve()


def clear_scene() -> None:
    """Blender'in varsayilan sahnesindeki kup/isik/kamerayi temizler."""
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)


def add_residue_sphere(position: list[float], color: list[float], name: str) -> bpy.types.Object:
    """Bir rezidu icin, verilen konumda ve renkte kucuk bir kure olusturur."""
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.4, location=position, segments=32, ring_count=16)
    sphere = bpy.context.active_object
    sphere.name = name
    bpy.ops.object.shade_smooth()  # kure yuzeyini pürüzsüz gösterir (facet gorunumunu kaldirir)

    material = bpy.data.materials.new(name=f"mat_{name}")
    material.diffuse_color = (*color, 1.0)  # (R, G, B, Alpha)
    sphere.data.materials.append(material)

    return sphere


def add_backbone_curve(positions: list[list[float]]) -> None:
    """
    Rezidu merkezlerini birbirine baglayan, PURUZSUZ bir omurga eğrisi cizer.

    Onceki versiyon duz cizgilerle (POLY spline) baglıyordu -- bu, heliks
    gibi kivrimli bolgelerde "zikzak" gibi gorunuyordu. NURBS spline,
    noktalar arasindan yumusak bir egri gecirerek daha gercekci bir
    "tup" gorunumu verir.
    """
    curve_data = bpy.data.curves.new("backbone", type="CURVE")
    curve_data.dimensions = "3D"
    curve_data.bevel_depth = 0.15  # egriye kalinlik verir
    curve_data.resolution_u = 12   # noktalar arasi kac ara adim hesaplanacak (yumusaklik)

    spline = curve_data.splines.new("NURBS")
    spline.points.add(len(positions) - 1)
    for i, pos in enumerate(positions):
        spline.points[i].co = (*pos, 1.0)  # 4. deger (w) spline agirligi

    spline.use_endpoint_u = True   # egrinin ilk/son noktadan baslayip bitmesini saglar
    spline.order_u = min(4, len(positions))  # yumusatma derecesi

    curve_obj = bpy.data.objects.new("backbone_curve", curve_data)
    bpy.context.collection.objects.link(curve_obj)


def setup_camera_and_light(center: list[float], positions: list[list[float]]) -> None:
    """
    Proteinin gercek boyutuna gore otomatik uzaklikta, ORTOGRAFIK bir
    kamera kurar. Ortografik kamera perspektif carpitmasi yapmaz -- uzaktaki
    ve yakindaki rezidular ayni olcekte gorunur, bu da bilimsel gorsellerde
    tercih edilen bir sunum sekli.
    """
    import mathutils

    # proteinin en genis oldugu eksendeki (x, y veya z) yayilimini bul
    xs = [p[0] for p in positions]
    ys = [p[1] for p in positions]
    zs = [p[2] for p in positions]
    span = max(max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs))

    # kamerayi bu yayilimin yeterince disinda, -Y ekseninde konumlandir
    distance = span * 1.5 + 10
    camera_location = mathutils.Vector((center[0], center[1] - distance, center[2]))

    bpy.ops.object.camera_add(location=camera_location)
    camera = bpy.context.active_object
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = span * 1.3
    bpy.context.scene.camera = camera

    # kamerayi merkeze dogru cevir
    direction = mathutils.Vector(center) - camera_location
    camera.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()

    bpy.ops.object.light_add(type="SUN", location=(center[0], center[1], center[2] + span))


def render_scene(scene_path: Path, output_path: Path) -> None:
    with open(scene_path) as f:
        scene_data = json.load(f)

    residues = scene_data["residues"]
    positions = [r["position"] for r in residues]

    clear_scene()

    for residue in residues:
        add_residue_sphere(
            position=residue["position"],
            color=residue["color"],
            name=f"res_{residue['residue_number']}",
        )

    add_backbone_curve(positions)

    # sahnenin ortalama konumunu bul, kamerayi ona gore kur
    center = [sum(p[i] for p in positions) / len(positions) for i in range(3)]
    setup_camera_and_light(center, positions)

    bpy.context.scene.render.filepath = str(output_path)
    bpy.context.scene.render.resolution_x = 1200
    bpy.context.scene.render.resolution_y = 900
    bpy.ops.render.render(write_still=True)
    print(f"Render kaydedildi: {output_path}")


def main():
    scene_path = parse_args()
    output_path = scene_path.parent / f"{scene_path.stem}_render.png"
    render_scene(scene_path, output_path)


if __name__ == "__main__":
    main()
