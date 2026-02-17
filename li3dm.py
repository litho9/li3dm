import bpy, numpy as np, os
from glob import glob

def inv_gi(vv): return -vv[0], -vv[2], vv[1]
def inv_zzz(vv): return -vv[0], vv[1], vv[2]
agmg_suffixes = ("Position.buf", "Texcoord.buf", "Blend.buf")

def char_import(buffers, name:str, renamap, inv):
    ib, vb0, vb1, vb2 = buffers
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata([inv(p[0]) for p in vb0], [], [list(reversed(p)) for p in ib])
    mesh.polygons.foreach_set("use_smooth", [True] * len(mesh.polygons))
    mesh.normals_split_custom_set_from_vertices([inv(p[1]) for p in vb0])
    obj = bpy.data.objects.new(mesh.name, mesh)
    bpy.context.scene.collection.objects.link(obj)

    data = [vb1[l.vertex_index] for l in mesh.loops]
    mesh.vertex_colors.new().data.foreach_set("color", [c for d in data for c in d[0] / 255])
    for i in range(1, len(vb1[0])):
        mesh.uv_layers.new().data.foreach_set("uv", [c for d in data for c in (d[i][0], d[i][1])])
    c = [(v, w, i) for v, b in enumerate(vb2) for w, i in zip(*b) if w]
    for i in range(max([x[2] for x in c]) + 1): obj.vertex_groups.new(name=renamap[i])
    for v, w, i in c: obj.vertex_groups[i].add((v,), w, 'REPLACE')

# def buffers_gi_agmg(path:str, name:str, fmts):
#     os.chdir(path)
#     vb = [np.fromfile(f"{name}{n}", f) for n, f in zip(agmg_suffixes, fmts[1:])]
#     for ib in glob("*.ib"): yield np.fromfile(ib, fmts[0]), *vb
def zzz_agmg_char_import(agmg_name:str, fmts, name:str, renamap):
    char_import(zzz_agmg_buffers(agmg_name, fmts), name, renamap, inv_zzz)
def zzz_agmg_char_import_parts(agmg_name:str, fmts, name:str, renamap, parts):
    ib, *vb = zzz_agmg_buffers(agmg_name, fmts)
    for n, length, offset in parts:
        buffers = (ib[offset//3:(offset+length)//3], *vb)
        char_import(buffers, f"{name}.{n}", renamap, inv_zzz)
def zzz_agmg_buffers(name:str, fmts):
    return [np.fromfile(f"{name}{b}", f) for b, f in zip(("A.ib", *agmg_suffixes), fmts)]
def zzz_3dm_char_import(vb1_hash, fmts, name:str, renamap):
    vb1_files = glob(f"*vb1={vb1_hash}*.buf")
    ib = (np.fromfile(glob(f"{vb1_files[3][:6]}-ib=*.buf")[0], fmts[0]))
    vb = [np.fromfile(glob(f"{vb1_files[0][:6]}-vb{i}=*.buf")[0], fmts[i + 1]) for i in range(3)]
    char_import((ib, *vb), name, renamap, inv_zzz)

#def zzz_weapon_import(name:str, vb1_hash:str, vb1_fmt="4u1,2f2,2f,2f2"):
#    for i in range(max(vb2) + 1): obj.vertex_groups.new(name=str(i))
#    for v, i in enumerate(vb2): obj.vertex_groups[i].add((v,), 1, 'REPLACE')

jufufu_renamap = {
    "Body": ['B_Spine_3', 'B_Clavicle_L', 'T_Clavicle_2_L', 'T_Clavivle_3_L', 'T_UpArm_1_L', 'T_Clavicle_1_L', 'B_Neck', 'C_Jacket_1_B', 'C_Jacket_C1_L', 'C_Jacket_C2_L', 'C_Jacket_B1_L', 'C_Jacket_B2_L', 'B_Chest_L', 'C_Jacket_2_B', 'C_Jacket_A1_L', 'C_Jacket_A2_L', 'C_Sleeve_L', 'C_Jacket_C2_R', 'C_Jacket_C1_R', 'B_Clavicle_R', 'T_Clavicle_2_R', 'T_Clavivle_3_R', 'T_Clavicle_1_R', 'T_UpArm_1_R', 'C_Jacket_B2_R', 'C_Jacket_B1_R', 'B_Chest_R', 'C_Jacket_A1_R', 'C_Jacket_A2_R', 'C_Sleeve_R', 'C_Sleeve_A1_L', 'C_Sleeve_B1_L', 'C_Sleeve_B2_L', 'C_Sleeve_A2_L', 'C_Sleeve_C1_L', 'C_Sleeve_C2_L', 'C_Sleeve_D1_L', 'C_Sleeve_D2_L', 'C_Sleeve_A1_R', 'C_Sleeve_A2_R', 'C_Sleeve_B1_R', 'C_Sleeve_B2_R', 'C_Sleeve_C1_R', 'C_Sleeve_C2_R', 'C_Sleeve_D1_R', 'C_Sleeve_D2_R', 'B_Spine_1', 'B_Spine_2', 'T_Thigh_L', 'B_Thigh_L', 'T_Thigh_2_L', 'B_Pelvis', 'T_Pelvis_3_L', 'T_Pelvis_4_L', 'T_Pelvis_2_L', 'T_Pelvis_1_L', 'T_Thigh_1_R', 'T_ThighShake_L', 'T_Pelvis_4_R', 'T_Pelvis_3_R', 'T_Pelvis_2_R', 'T_Pelvis_1_R', 'T_Thigh_2_R', 'B_Thigh_R', 'T_ThighShake_R', 'B_Head', 'T_Calf_L', 'T_Knee_2_L', 'T_Knee_1_L', 'T_CalfShake_L', 'T_Calf_R', 'T_Knee_2_R', 'T_Knee_1_R', 'T_CalfShake_R', 'T_Foot_L', 'B_Foot_L', 'T_Foot_R', 'B_Foot_R', 'C_HairBall_1_L', 'C_HairBall_7_L', 'C_HairBall_3_L', 'C_HairBall_6_L', 'C_HairBall_4_L', 'C_Bag_L', 'C_Bag_R', 'C_BagRope_1', 'C_BagRope_2', 'C_BagRope_3', 'C_BagRope_4', 'C_Bell', 'B_UpperArm_L', 'T_Elbow_2_L', 'T_UpArm_2_L', 'T_Forearm_1_L', 'T_Forearm_2_L', 'T_Forearm_3_L', 'T_Wrist_L', 'B_Hand_L', 'B_Finger_1_1_L', 'B_Finger_1_2_L', 'B_Finger_2_1_L', 'B_Finger_3_1_L', 'B_Finger_4_1_L', 'B_Finger_5_1_L', 'T_Elbow_1_L', 'B_Finger_1_3_L', 'B_Finger_3_2_L', 'B_Finger_3_3_L', 'B_Finger_2_2_L', 'B_Finger_2_3_L', 'B_Finger_4_2_L', 'B_Finger_4_3_L', 'B_Finger_5_2_L', 'B_Finger_5_3_L', 'B_UpperArm_R', 'T_Elbow_2_R', 'T_UpArm_2_R', 'T_Forearm_1_R', 'T_Forearm_2_R', 'T_Forearm_3_R', 'T_Wrist_R', 'B_Hand_R', 'B_Finger_1_1_R', 'B_Finger_1_2_R', 'B_Finger_2_1_R', 'B_Finger_3_1_R', 'B_Finger_4_1_R', 'B_Finger_5_1_R', 'T_Elbow_1_R', 'B_Finger_1_3_R', 'B_Finger_3_2_R', 'B_Finger_3_3_R', 'B_Finger_2_2_R', 'B_Finger_2_3_R', 'B_Finger_4_2_R', 'B_Finger_4_3_R', 'B_Finger_5_2_R', 'B_Finger_5_3_R', 'B_Toes_L', 'B_Toes_R', 'C_Card_2', 'C_Card_1'],
    "Hair": ['B_Head', 'Hair_D1_B', 'Hair_F1_B', 'Hair_D2_B', 'Hair_E1_B', 'Hair_D3_B', 'Hair_G1_B', 'Hair_G2_B', 'Hair_F2_B', 'Hair_G3_B', 'Hair_G4_B', 'Hair_G5_B', 'Hair_G7_B', 'Hair_B1_B', 'Hair_C1_B', 'Hair_A1_B', 'Hair_A2_B', 'Hair_B2_B', 'Hair_A3_B', 'Hair_A4_B', 'Hair_A5_B', 'Hair_A7_B', 'Hair_D4_B', 'Hair_D5_B', 'Hair_D7_B', 'Hair_D9_B', 'Hair_C2_B', 'Hair_C3_B', 'Hair_C5_B', 'Hair_E2_B', 'Hair_E3_B', 'Hair_E5_B', 'Hair_F3_B', 'Hair_F4_B', 'Hair_F6_B', 'Hair_F8_B', 'Hair_B3_B', 'Hair_B4_B', 'Hair_B6_B', 'Hair_B01_L', 'Hair_B02_L', 'Hair_B03_L', 'Hair_A01_L', 'Hair_B01_R', 'Hair_B02_R', 'Hair_B03_R', 'Hair_A01_R', 'Hair_1_M', 'Hair_2_M', 'B_Ear_1_L', 'B_Ear_2_L', 'B_Ear_1_R', 'B_Ear_2_R', 'Hair_A02_L', 'Hair_D02_F', 'Hair_A03_L', 'Hair_A08_L', 'Hair_A09_L', 'Hair_A10_L', 'Hair_A04_L', 'Hair_A06_L', 'Hair_A02_R', 'Hair_A03_R', 'Hair_A08_R', 'Hair_A09_R', 'Hair_A10_R', 'Hair_A04_R', 'Hair_A06_R', 'Hair_A01_F', 'Hair_1_F', 'Hair_B02_F', 'Hair_B03_F', 'Hair_B05_F', 'Hair_B07_F', 'Hair_D04_F', 'Hair_D06_F', 'Hair_B08_F', 'Hair_C02_F', 'Hair_C03_F'], # vb0=77d02cb1 vb2=c9c19a97 idx=3
    "Tail": ['C_Gourd_1', 'C_Gourd_2', 'B_Tail_1', 'B_Pelvis', 'B_Tail_2', 'B_Tail_3', 'B_Tail_4', 'B_Tail_5', 'B_Tail_6', 'B_Tail_7', 'C_TailBow_1', 'C_TailBow_4', 'C_TailBow_5', 'C_TailBow_6', 'C_TailBow_7', 'C_TailBow_2', 'C_TailBow_3'],
}

jufufu_sportwear_body = (
    ("nips", 9582, 0),
    ("nude", 248823, 9582),
    ("nudeWombTattoo", 248823, 258405),
    ("feetBodysuit", 41928, 507228),
    ("handsBodysuit", 32088, 549156),
    ("neckBodysuit", 6117, 581244),
    ("bodysuit", 265863, 587361),
    ("bodysuitWombTattoo", 265857, 1119081),
    ("bodysuitNips", 215931, 1650795),
    ("bodysuitWombTattooTornNipples", 215931, 2082657),
    ("bodysuitTorn", 265857, 853224),
    ("bodysuitWombTattooTorn", 265857, 1384938),
    ("bodysuitTornNips", 215931, 1866726),
    ("bodysuitWombTattooNips", 215931, 2298588),
    ("hoodie", 56478, 2514519),
    ("fingernails", 2904, 2570997),
    ("glasses", 1350, 2573901),
    ("nipplePiercings", 12264, 2575251),
    ("shoes", 5376, 2587515),
    ("socks", 6336, 2592891),
    ("visorCap", 2220, 2599227),
    ("visorCapTransparent", 804, 2601447),
)
os.chdir(r"C:\mod\zzmi\Mods\[_DISABLED_]\JuFufuSportswear\resources")
fmt0 = ("3u4", "3f,3f,4f", "4u1,2f2,2f,2f2", "4f,4i")
# ib0, *vb0 = zzz_agmg_buffers("JuFufuBody", fmt0)
# for n, length, offset in jufufu_sportwear_body:
#     char_import(((ib0[offset // 3:(offset + length) // 3]), *vb0),
#                 f"JuFufu_Sportswear_Body.{n}", jufufu_renamap["Body"], inv_zzz)
zzz_agmg_char_import_parts("JuFufuBody", fmt0, "JuFufu_Sportswear_Body", jufufu_renamap["Body"], jufufu_sportwear_body)

os.chdir(r"C:\mod\zzmi\FrameAnalysis-2026-01-03-224707")
fmts0 = ("3u2", "3f,3f,4f", "4u1,2f2,2f,2f2", "4f,4i")
zzz_3dm_char_import("2e086db7", fmts0, "JuFufu_3dm_Body", jufufu_renamap["Body"])
# ("Hair", None, "fbca830d"), # vb0=77d02cb1 vb2=c9c19a97 idx=3
# ("Tail", None, "9a198bcf"),

parts_redo = [
    "JuFufu_Sportswear_Body.socks", "JuFufu_Sportswear_Body.shoes", "JuFufu_Sportswear_Body_fingernails", "JuFufu_Sportswear_Body.nude", "JuFufu_Sportswear_Body.nudeNips", "JuFufu_Sportswear_Body.nudeWombTattoo", "JuFufu_Sportswear_Body_feetBodysuit", "JuFufu_Sportswear_Body_handsBodysuit", "JuFufu_Sportswear_Body_neckBodysuit", "JuFufu_Sportswear_Body.suit",  "JuFufu_Sportswear_Body.suitNips","JuFufu_Sportswear_Body.suitGro", "JuFufu_Sportswear_Body.suitTorn", "JuFufu_Sportswear_Body.suitWombTattoo", "JuFufu_Sportswear_Body_glasses", "JuFufu_Sportswear_Body_hoodie", "JuFufu_Sportswear_Body_nipplePiercings", "JuFufu_Sportswear_Body_visorCap", "JuFufu_Sportswear_Body_visorCapTransparent"]

def zzz_char_export(name, objs, fmts=(np.uint32, "3f,3f,4f", "4u1,2f2,2f,2f2", "4f,4i")):
    def inv(vv): return -vv[0], vv[1], vv[2]
    ib, vb, index_map = [], ([], [], []), {}
    for mesh in [obj.data for obj in objs]:
        print(f"; {mesh.name}\ndrawindexed = {len(mesh.loops)}, {len(ib)}, 0")
        mesh.calc_tangents()
        for loop in [mesh.loops[i] for p in mesh.polygons for i in reversed(p.loop_indices)]:
            h = (loop.vertex_index, *mesh.uv_layers[0].data[loop.index].uv, *loop.normal)
            if h not in index_map:
                index_map[h] = len(vb[0])
                v = mesh.vertices[loop.vertex_index]
                vb[0].append((inv(v.co), inv(loop.normal), inv(loop.tangent), -loop.bitangent_sign))
                vb[1].append(([int(i * 255) for i in mesh.vertex_colors[0].data[loop.index].color],
                            *[tex.data[loop.index].uv for tex in mesh.uv_layers]))
                vb[2].append(([v.groups[i].weight if i < len(v.groups) else .0 for i in range(4)],
                            [v.groups[i].group if i < len(v.groups) else 0 for i in range(4)]))
            ib.append(index_map[h])
    print(f"draw = {len(vb[0])}, 0")
    for buffer, fmt, b_name in zip((ib, *vb), fmts, ("ib", "vb0", "vb1", "vb2")):
        np.fromiter(buffer, fmt).tofile(f"{name}_{b_name}.buf")

os.chdir(r"C:\mod\zzmi\Mods\JuFufu Sportswear byRhiannon")
objs0 = [bpy.data.objects[n] for n in parts_redo]
fmts0 = (np.uint32, "3f,3f,4f", "4u1,2f2,2f,2f2", "4f,4i")
zzz_char_export("JuFufu_Sportswear_Body", objs0, fmts0)