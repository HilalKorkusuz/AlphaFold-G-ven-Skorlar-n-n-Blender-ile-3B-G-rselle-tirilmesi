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


def parse_args() -> tuple[Path, str]:
    """
    Komut satirindaki '--' isaretinden sonraki argumanlari okur.

    Beklenen kullanim:
        blender --background --python blender_render.py -- <scene.json> [renk_modu]

    renk_modu: "plddt" (varsayilan) veya "deviation" -- hangi veriye gore
    renklendirme yapilacagini secer. "deviation" secilirse, scene.json'un
    align.py verisiyle uretilmis olmasi gerekir (yoksa tum kureler gri olur).
    """
    if "--" not in sys.argv:
        raise ValueError("Kullanim: blender --background --python blender_render.py -- <scene.json> [plddt|deviation]")
    args_after_dashdash = sys.argv[sys.argv.index("--") + 1:]
    if not args_after_dashdash:
        raise ValueError("Scene dosyasinin yolunu belirtmelisin.")

    # .resolve() goreli yolu (orn. ..\data\scene.json) MUTLAK yola cevirir.
    # Bunu yapmazsak, cikti dosyasi Blender'in kendi calisma dizinine gore
    # kaydedilir -- bu da terminaldeki bulundugun klasorden FARKLI olabilir
    # ve dosyayi "kaybetmis" gibi hissettirir.
    scene_path = Path(args_after_dashdash[0]).resolve()
    color_mode = args_after_dashdash[1] if len(args_after_dashdash) > 1 else "plddt"

    if color_mode not in ("plddt", "deviation"):
        raise ValueError(f"Bilinmeyen renk modu: {color_mode!r} (plddt veya deviation olmali)")

    return scene_path, color_mode


def clear_scene() -> None:
    """Blender'in varsayilan sahnesindeki kup/isik/kamerayi temizler."""
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)


def add_residue_sphere(position: list[float], color: list[float], name: str) -> bpy.types.Object:
    """
    Bir rezidu icin, verilen konumda ve renkte kucuk bir kure olusturur.

    Materyal, Principled BSDF node'u uzerinden kuruluyor (sadece
    diffuse_color degil) -- bu, gercek isik/golge/yansima hesaplarina
    giren asil parametre. Hafif parlak (dusuk roughness), metalik
    olmayan bir "cilali plastik/seramik" gorunumu hedefliyoruz --
    bilimsel molekul gorsellerinde yaygin bir stil.
    """
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.4, location=position, segments=32, ring_count=16)
    sphere = bpy.context.active_object
    sphere.name = name
    bpy.ops.object.shade_smooth()

    material = bpy.data.materials.new(name=f"mat_{name}")
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.25
    bsdf.inputs["Metallic"].default_value = 0.0
    # Bazi Blender surumlerinde "Specular"/"Specular IOR Level" adiyla gecer;
    # ikisini de dene, hangisi varsa onu kullan (surumler arasi uyumluluk).
    for spec_key in ("Specular IOR Level", "Specular"):
        if spec_key in bsdf.inputs:
            bsdf.inputs[spec_key].default_value = 0.6
            break

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

    # omurgaya notr, hafif metalik-gri bir materyal ver -- kurelerin
    # rengiyle yarismasin, sadece yapiyi "tasiyan" bir iskelet gibi dursun
    material = bpy.data.materials.new(name="mat_backbone")
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (0.75, 0.76, 0.78, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.35
    bsdf.inputs["Metallic"].default_value = 0.15
    curve_obj.data.materials.append(material)


def setup_camera(center: list[float], positions: list[list[float]]) -> float:
    """
    Proteinin gercek boyutuna gore otomatik uzaklikta, ORTOGRAFIK bir
    kamera kurar. Ortografik kamera perspektif carpitmasi yapmaz -- uzaktaki
    ve yakindaki rezidular ayni olcekte gorunur, bu da bilimsel gorsellerde
    tercih edilen bir sunum sekli.

    Donen "span" degeri, isik kurulumunda da mesafe hesaplamak icin
    disari veriliyor -- boylece isik/kamera hep proteinin boyutuna
    orantili kalir, protein degistiginde elle ayar yapmaya gerek kalmaz.
    """
    import mathutils

    xs = [p[0] for p in positions]
    ys = [p[1] for p in positions]
    zs = [p[2] for p in positions]
    span = max(max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs))

    # kamera yonu: -Y (onden), +X (sagdan), +Z (ustten) karisimi --
    # bu vektoru degistirerek acidan oynayabilirsin (normalize ediliyor,
    # sadece ORANLAR onemli)
    distance = span * 1.5 + 10
    direction_vector = mathutils.Vector((0.45, -0.75, 0.55)).normalized()
    camera_location = mathutils.Vector(center) + direction_vector * distance

    bpy.ops.object.camera_add(location=camera_location)
    camera = bpy.context.active_object
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = span * 1.3
    bpy.context.scene.camera = camera

    direction = mathutils.Vector(center) - camera_location
    camera.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()

    return span


def setup_lighting(center: list[float], span: float) -> None:
    """
    Uc noktali (three-point) isiklandirma kurar -- fotografcilikta
    standart bir teknik:
      - KEY   : ana isik, guclu, yandan-ustten geliyor, ana golgeleri olusturur
      - FILL  : karsi yondan gelen, daha zayif bir isik -- key'in olusturdugu
                sert golgeleri yumusatir, tum sahnenin "duz karanlik" kalan
                tarafini hafifce aydinlatir
      - RIM   : arkadan gelen isik -- objenin kenarlarini hafifce
                aydinlatip arka plandan ayristirir ("kontur isigi")

    Tek bir SUN isigina kiyasla, bu kurulum golgeleri daha yumusak ve
    molekulun 3B hacmini daha okunakli hale getirir.
    """
    # KEY: ana isik, sag-ust-onden -- baskin isik kaynagi, ana golgeleri o olusturur
    bpy.ops.object.light_add(
        type="AREA",
        location=(center[0] + span * 0.8, center[1] - span * 0.6, center[2] + span * 0.9),
    )
    key_light = bpy.context.active_object
    key_light.data.energy = span * 90
    key_light.data.size = span * 0.35
    _point_light_at(key_light, center)

    # FILL: cok zayif isik, sol-alttan -- sadece key'in golgelerini tamamen
    # karanliga gomulmekten kurtarir, kendi golgesini olusturmayacak kadar zayif
    bpy.ops.object.light_add(
        type="AREA",
        location=(center[0] - span * 0.9, center[1] - span * 0.3, center[2] - span * 0.2),
    )
    fill_light = bpy.context.active_object
    fill_light.data.energy = span * 8
    fill_light.data.size = span * 0.8
    _point_light_at(fill_light, center)

    # RIM: arkadan, kenarlari hafifce aydinlatmak icin -- yine zayif
    bpy.ops.object.light_add(
        type="AREA",
        location=(center[0], center[1] + span * 1.2, center[2] + span * 0.4),
    )
    rim_light = bpy.context.active_object
    rim_light.data.energy = span * 15
    rim_light.data.size = span * 0.3
    _point_light_at(rim_light, center)

    # arka plani duz siyah yerine hafif koyu-gri/mavimsi bir tona getir --
    # tamamen siyah, molekulun koyu renkli kenarlarini yutabiliyor
    world = bpy.context.scene.world
    if world is None:
        world = bpy.data.worlds.new("World")
        bpy.context.scene.world = world
    world.use_nodes = True
    bg_node = world.node_tree.nodes.get("Background")
    if bg_node:
        bg_node.inputs["Color"].default_value = (0.35, 0.36, 0.38, 1.0)
        bg_node.inputs["Strength"].default_value = 1.0


def _point_light_at(light_object: bpy.types.Object, target: list[float]) -> None:
    """Verilen isik objesini, target konumuna bakacak sekilde dondurur."""
    import mathutils
    direction = mathutils.Vector(target) - light_object.location
    light_object.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def configure_render_quality() -> None:
    """
    Render motorunu ve kalite ayarlarini yapilandirir.

    EEVEE kullaniyoruz -- Cycles'a gore cok daha hizli (ekran karti
    hizlandirmali, gercek zamanli render motoru). Kalite farki tek kare
    statik render'larda gozle pek fark edilmiyordu ama render suresi
    onemli olcude artiyordu, bu yuzden performansi onceliklendirdik.
    """
    scene = bpy.context.scene
    # Blender surumune gore EEVEE'nin adi degisebiliyor (4.2+ 'BLENDER_EEVEE_NEXT')
    available_engines = {e.identifier for e in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items}
    if "BLENDER_EEVEE_NEXT" in available_engines:
        scene.render.engine = "BLENDER_EEVEE_NEXT"
    else:
        scene.render.engine = "BLENDER_EEVEE"


def render_scene(scene_path: Path, output_path: Path, color_mode: str = "plddt") -> None:
    with open(scene_path) as f:
        scene_data = json.load(f)

    residues = scene_data["residues"]
    positions = [r["position"] for r in residues]

    # renk modu "deviation" ise ve o rezidu icin sapma verisi yoksa (deneysel
    # karsiligi bulunamamis), scene.py'nin atadigi gri renk zaten kullanilir
    color_field = "color" if color_mode == "plddt" else "deviation_color"

    clear_scene()

    for residue in residues:
        add_residue_sphere(
            position=residue["position"],
            color=residue[color_field],
            name=f"res_{residue['residue_number']}",
        )

    add_backbone_curve(positions)

    center = [sum(p[i] for p in positions) / len(positions) for i in range(3)]
    span = setup_camera(center, positions)
    setup_lighting(center, span)
    configure_render_quality()

    bpy.context.scene.render.filepath = str(output_path)
    bpy.context.scene.render.resolution_x = 1200
    bpy.context.scene.render.resolution_y = 900
    bpy.ops.render.render(write_still=True)
    print(f"Render kaydedildi: {output_path}")


def main():
    scene_path, color_mode = parse_args()
    output_path = scene_path.parent / f"{scene_path.stem}_render_{color_mode}.png"
    render_scene(scene_path, output_path, color_mode)


if __name__ == "__main__":
    main()
