"""
Kodun işlevi:
scene.json'u okuyup, pLDDT veya RMSD sapma verisine göre renklendirilmiş
bir protein render'i üretir.

Bu script normal Python'la değil, BLENDER'IN KENDİ İÇİNDEKİ Python
yorumlayıcısıyla çalışır. Terminalden değil, Blender üzerinden çalıştırılır.

Kullanım (terminalden, Blender kurulu olduğu varsayılarak):
    blender --background --python blender_render.py -- data/scene_P69905.json [plddt|deviation]

--background : Blender'i arayüz açmadan, arka planda çalıştırır
--python     : bu dosyayı Blender'in Python yorumlayıcısıyla çalıştır
--           : bundan sonraki argümanlar Blender'a değil, bu script'e gider
"""

import json
import sys
from pathlib import Path

import bpy


def parse_args() -> tuple[Path, str]:
    # Komut satırındaki '--' işaretinden sonraki argümanları okur: scene.json yolu + renk_modu
    if "--" not in sys.argv:
        raise ValueError("Kullanim: blender --background --python blender_render.py -- <scene.json> [plddt|deviation]")
    args_after_dashdash = sys.argv[sys.argv.index("--") + 1:]
    if not args_after_dashdash:
        raise ValueError("Scene dosyasinin yolunu belirtmelisin.")

    # .resolve() göreli yolu (örn. ..\data\scene.json) MUTLAK yola çevirir --
    # yoksa çıktı dosyası Blender'ın kendi çalışma dizinine göre kaydedilebilir
    # (bu, daha önce "render'ı bulamıyorum" hatasına sebep olan şeydi)
    scene_path = Path(args_after_dashdash[0]).resolve()
    color_mode = args_after_dashdash[1] if len(args_after_dashdash) > 1 else "plddt"  # verilmezse varsayılan plddt

    if color_mode not in ("plddt", "deviation"):
        raise ValueError(f"Bilinmeyen renk modu: {color_mode!r} (plddt veya deviation olmali)")

    return scene_path, color_mode


def clear_scene() -> None:
    # Blender'ın varsayılan sahnesindeki küp/ışık/kamerayı temizler.
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)


def add_residue_sphere(position: list[float], color: list[float], name: str) -> bpy.types.Object:
    # Bir residü için, verilen konumda ve renkte küçük bir küre oluşturur.
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.4, location=position, segments=32, ring_count=16)
    sphere = bpy.context.active_object
    sphere.name = name
    bpy.ops.object.shade_smooth()  # yüzeyi pürüzsüz gösterir, köşeli/faceted görünümü kaldırır

    # Materyal, Principled BSDF node'u üzerinden kuruluyor (basit diffuse_color
    # ATAMASI DEĞİL) -- bu, gerçek ışık/gölge/yansıma hesaplarına giren asıl
    # parametre. Düşük roughness + biraz specular = "cilalı seramik" görünümü.
    material = bpy.data.materials.new(name=f"mat_{name}")
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.25
    bsdf.inputs["Metallic"].default_value = 0.0
    for spec_key in ("Specular IOR Level", "Specular"):  # Blender sürümüne göre isim değişiyor, ikisini de dene
        if spec_key in bsdf.inputs:
            bsdf.inputs[spec_key].default_value = 0.6
            break

    sphere.data.materials.append(material)
    return sphere


def add_backbone_curve(positions: list[list[float]]) -> None:
    # Residü merkezlerini birbirine bağlayan, PÜRÜZSÜZ bir omurga eğrisi çizer.
    # NURBS spline kullanıyoruz (düz çizgi/POLY değil) -- heliks gibi kıvrımlı
    # bölgelerde düz çizgiler "zikzak" gibi görünüyordu, NURBS yumuşak bir tüp verir.
    curve_data = bpy.data.curves.new("backbone", type="CURVE")
    curve_data.dimensions = "3D"
    curve_data.bevel_depth = 0.15  # eğriye kalınlık verir
    curve_data.resolution_u = 12   # noktalar arası kaç ara adım hesaplanacak (yumuşaklık)

    spline = curve_data.splines.new("NURBS")
    spline.points.add(len(positions) - 1)
    for i, pos in enumerate(positions):
        spline.points[i].co = (*pos, 1.0)  # 4. değer (w) spline ağırlığı, NURBS için gerekli

    spline.use_endpoint_u = True             # eğrinin ilk/son noktadan başlayıp bitmesini sağlar
    spline.order_u = min(4, len(positions))  # yumuşatma derecesi

    curve_obj = bpy.data.objects.new("backbone_curve", curve_data)
    bpy.context.collection.objects.link(curve_obj)

    # omurgaya nötr, hafif metalik-gri bir materyal ver -- kürelerin
    # rengiyle yarışmasın, sadece yapıyı "taşıyan" bir iskelet gibi dursun
    material = bpy.data.materials.new(name="mat_backbone")
    material.use_nodes = True
    bsdf = material.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (0.75, 0.76, 0.78, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.35
    bsdf.inputs["Metallic"].default_value = 0.15
    curve_obj.data.materials.append(material)


def setup_camera(center: list[float], positions: list[list[float]]) -> float:
    # Proteinin gerçek boyutuna göre otomatik uzaklıkta, ORTOGRAFIK bir kamera
    # kurar (perspektif çarpıtması yapmaz -- uzaktaki/yakındaki residüler aynı
    # ölçekte görünür, bilimsel görsellerde tercih edilen sunum şekli).
    #
    # Dönen "span" değeri, ışık kurulumunda da mesafe hesaplamak için dışarı
    # veriliyor -- böylece ışık/kamera hep proteinin boyutuna orantılı kalır,
    # protein değiştiğinde elle ayar yapmaya gerek kalmaz.
    import mathutils

    xs = [p[0] for p in positions]
    ys = [p[1] for p in positions]
    zs = [p[2] for p in positions]
    span = max(max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs))

    distance = span * 1.5 + 10
    # kamera yönü: -Y (önden) + X (sağdan) + Z (üstten) karışımı --
    # bu üç sayıyı değiştirerek açıdan oynayabilirsin (normalize ediliyor, sadece ORANLAR önemli)
    direction_vector = mathutils.Vector((0.45, -0.75, 0.55)).normalized()
    camera_location = mathutils.Vector(center) + direction_vector * distance

    bpy.ops.object.camera_add(location=camera_location)
    camera = bpy.context.active_object
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = span * 1.3
    bpy.context.scene.camera = camera

    direction = mathutils.Vector(center) - camera_location
    camera.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()  # kamerayı merkeze doğru çevir

    return span


def _point_light_at(light_object: bpy.types.Object, target: list[float]) -> None:
    # Verilen ışık objesini, target konumuna bakacak şekilde döndürür.
    import mathutils
    direction = mathutils.Vector(target) - light_object.location
    light_object.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def setup_lighting(center: list[float], span: float) -> None:
    # Üç noktalı (three-point) ışıklandırma kurar -- fotoğrafçılıkta standart bir teknik:
    #   KEY  : ana ışık, güçlü, ana gölgeleri o oluşturur
    #   FILL : karşı yönden gelen zayıf ışık, key'in sert gölgelerini yumuşatır
    #   RIM  : arkadan gelen ışık, kenarları arka plandan ayrıştırır
    # Tek bir SUN ışığına kıyasla, bu kurulum gölgeleri daha yumuşak ve
    # molekülün 3B hacmini daha okunaklı hale getirir.

    # KEY: ana ışık, sağ-üst-önden -- baskın kaynak, ana gölgeleri o oluşturur
    bpy.ops.object.light_add(
        type="AREA",
        location=(center[0] + span * 0.8, center[1] - span * 0.6, center[2] + span * 0.9),
    )
    key_light = bpy.context.active_object
    key_light.data.energy = span * 90
    key_light.data.size = span * 0.35
    _point_light_at(key_light, center)

    # FILL: çok zayıf ışık, sol-alttan -- kendi gölgesini oluşturmayacak kadar
    # zayıf, sadece key'in gölgelerinin tamamen karanlığa gömülmesini önler
    bpy.ops.object.light_add(
        type="AREA",
        location=(center[0] - span * 0.9, center[1] - span * 0.3, center[2] - span * 0.2),
    )
    fill_light = bpy.context.active_object
    fill_light.data.energy = span * 8
    fill_light.data.size = span * 0.8
    _point_light_at(fill_light, center)

    # RIM: arkadan, kenarları hafifçe aydınlatmak için -- yine zayıf
    bpy.ops.object.light_add(
        type="AREA",
        location=(center[0], center[1] + span * 1.2, center[2] + span * 0.4),
    )
    rim_light = bpy.context.active_object
    rim_light.data.energy = span * 15
    rim_light.data.size = span * 0.3
    _point_light_at(rim_light, center)

    # arka planı düz siyah yerine orta tonlu gri yaptık -- tamamen siyah,
    # molekülün koyu renkli kenarlarını görünmez kılıyordu
    world = bpy.context.scene.world
    if world is None:
        world = bpy.data.worlds.new("World")
        bpy.context.scene.world = world
    world.use_nodes = True
    bg_node = world.node_tree.nodes.get("Background")
    if bg_node:
        bg_node.inputs["Color"].default_value = (0.35, 0.36, 0.38, 1.0)
        bg_node.inputs["Strength"].default_value = 1.0


def configure_render_quality() -> None:
    # Render motorunu seçer. EEVEE kullanıyoruz -- Cycles'a göre çok daha
    # hızlı (ekran kartı hızlandırmalı, gerçek zamanlı motor). Cycles'ı
    # denedik, kalite farkı tek kare statik render'da gözle pek fark
    # edilmiyordu ama süre belirgin arttığı için performansı önceliklendirdik.
    scene = bpy.context.scene
    available_engines = {e.identifier for e in bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items}
    if "BLENDER_EEVEE_NEXT" in available_engines:  # Blender surumune gore EEVEE'nin adi degisiyor (4.2+)
        scene.render.engine = "BLENDER_EEVEE_NEXT"
    else:
        scene.render.engine = "BLENDER_EEVEE"


def render_scene(scene_path: Path, output_path: Path, color_mode: str = "plddt") -> None:
    # Tüm parçaları bir araya getirip render alan ana fonksiyon.
    with open(scene_path) as f:
        scene_data = json.load(f)

    residues = scene_data["residues"]
    positions = [r["position"] for r in residues]

    # renk modu "deviation" ise ve o residü için sapma verisi yoksa (deneysel
    # karşılığı bulunamamış), scene.py'nin atadığı gri renk zaten kullanılır
    color_field = "color" if color_mode == "plddt" else "deviation_color"

    clear_scene()

    for residue in residues:
        add_residue_sphere(
            position=residue["position"],
            color=residue[color_field],
            name=f"res_{residue['residue_number']}",
        )

    add_backbone_curve(positions)

    center = [sum(p[i] for p in positions) / len(positions) for i in range(3)]  # residü konumlarının ortalaması
    span = setup_camera(center, positions)
    setup_lighting(center, span)
    configure_render_quality()

    bpy.context.scene.render.filepath = str(output_path)
    bpy.context.scene.render.resolution_x = 1200
    bpy.context.scene.render.resolution_y = 900
    bpy.ops.render.render(write_still=True)
    print(f"Render kaydedildi: {output_path}")


def main():  # TERMINALDEN DOGRUDAN calistirildiginda devreye giren kisim
    scene_path, color_mode = parse_args()
    output_path = scene_path.parent / f"{scene_path.stem}_render_{color_mode}.png"  # dosya adına renk modunu ekliyoruz, plddt/deviation render'ları birbirinin üzerine yazmasın diye
    render_scene(scene_path, output_path, color_mode)


if __name__ == "__main__":
    main()