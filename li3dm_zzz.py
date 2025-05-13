import bpy, numpy as np, os
from glob import glob

def inv(vv): return -vv[0], vv[1], vv[2]

def read_buffers(vb1_hash:str, ib="3u2", vb0="3f,3f,4f", vb1="4u1,2f2,2f,2f2", vb2="i4"):
    vb1_files = glob(f"*vb1={vb1_hash}*.buf")
    d1, d2 = vb1_files[0][:6], vb1_files[1][:6]
    def r(draw, buf, fmt): return np.fromfile(glob(f"{draw}-{buf}=*.buf")[0], np.dtype(fmt))
    return r(d2, "ib", ib), r(d1, "vb0", vb0), r(d1, "vb1", vb1), r(d1, "vb2", vb2)

def zzz_char_import(name:str, vb1_hash:str, vb1_fmt="4u1,2f2,2f,2f2"):
    ib, vb0, vb1, vb2 = read_buffers(vb1_hash, vb1=vb1_fmt)

    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    mesh.from_pydata([inv(p[0]) for p in vb0], [], [list(reversed(p)) for p in ib])
    mesh.polygons.foreach_set("use_smooth", [True] * len(mesh.polygons))
    mesh.normals_split_custom_set_from_vertices([inv(p[1]) for p in vb0])

    data = [vb1[l.vertex_index] for l in mesh.loops]
    mesh.vertex_colors.new().data.foreach_set("color", [c for d in data for c in d[0] / 255])
    for i in range(1, len(vb1[0])):
        mesh.uv_layers.new().data.foreach_set("uv", [c for d in data for c in d[i]])
    c = [(v, w, i) for v, b in enumerate(vb2) for w, i in zip(*b) if w]
    for i in range(max([x[2] for x in c]) + 1): obj.vertex_groups.new(name=str(i))
    for v, w, i in c: obj.vertex_groups[i].add((v,), w, 'REPLACE')

def zzz_weapon_import(name:str, vb1_hash:str, vb1_fmt="4u1,2f2,2f,2f2", vb2_fmt="i4"):
    ib, vb0, vb1, vb2 = read_buffers(vb1_hash, vb1=vb1_fmt, vb2=vb2_fmt)

    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    mesh.from_pydata([inv(p[0]) for p in vb0], [], [list(reversed(p)) for p in ib])
    mesh.polygons.foreach_set("use_smooth", [True] * len(mesh.polygons))
    mesh.normals_split_custom_set_from_vertices([inv(p[1]) for p in vb0])

    data = [vb1[l.vertex_index] for l in mesh.loops]
    mesh.vertex_colors.new().data.foreach_set("color", [c for d in data for c in d[0] / 255])
    for i in range(1, len(vb1[0])):
        mesh.uv_layers.new().data.foreach_set("uv", [c for d in data for c in d[i]])
    for i in range(max(vb2) + 1): obj.vertex_groups.new(name=str(i))
    for v, i in enumerate(vb2): obj.vertex_groups[i].add((v,), 1, 'REPLACE')
