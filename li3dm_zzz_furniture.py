import bpy, bmesh, numpy as np, os
from glob import glob

def import_collected_furniture(name:str, vb0_hash:str, vb_fmt="4f2,4i1,4u1,2f2,2f2"):
    vb_file = glob(f"*vb0={vb0_hash}*.buf")[0]
    vb = np.fromfile(vb_file, np.dtype(vb_fmt))
    ib = np.fromfile(glob(f"{vb_file[:6]}-ib=*.buf")[0], np.dtype("3u2"))

    def inf(vv): return -vv[0], -vv[2], vv[1]
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(mesh.name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    mesh.from_pydata([inf(p[0]) for p in vb], [], [list(reversed(p)) for p in ib])
    mesh.polygons.foreach_set("use_smooth", [True] * len(mesh.polygons))
    mesh.normals_split_custom_set_from_vertices([inf(p[1] / 127.) for p in vb])

    data = [vb[l.vertex_index] for l in mesh.loops]
    mesh.vertex_colors.new().data.foreach_set("color", [c for d in data for c in d[2] / 256])
    for i in range(3, len(vb[0])):
        mesh.uv_layers.new().data.foreach_set("uv", [c for d in data for c in d[i]])

    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.remove_doubles(threshold=.000001, use_sharp_edge_from_normals=True)
    bpy.ops.object.mode_set(mode='OBJECT')

def join_meshes(name:str, objs, names, scale=.25):
    for obj in objs:
        for mod in [m for m in obj.modifiers if m.type == 'SOLIDIFY' or m.type == 'NODES']:
            mod.show_viewport = False
    bm0 = bmesh.new()
    deps = bpy.context.evaluated_depsgraph_get()
    for obj in objs:
        [char, part_str, *_] = obj.name.split("_")
        pivot = np.fromiter((int(part_str), names.index(char)), np.float32)
        print(f"parsing {obj.name} (pivot={pivot},scale={scale})")

        bm = bmesh.new()
        bm.from_object(obj, deps)
        bm.transform(obj.matrix_world)
        bmesh.ops.triangulate(bm, faces=bm.faces)
        # bm.faces.flatMap { it.loops }.map { it[bm.loops.layers.uv[0]] }
        for layer in [loop[bm.loops.layers.uv[0]] for face in bm.faces for loop in face.loops]:
            layer.uv = (pivot + layer.uv) * scale

        mesh = bpy.data.meshes.new("Temp")
        bm.to_mesh(mesh)  # bmesh doesn't have a "from_bmesh" method
        mesh.uv_layers[0].name = "joined"
        while len(mesh.uv_layers) > 1:
            mesh.uv_layers.remove(mesh.uv_layers[1])
        bm0.from_mesh(mesh)
        bpy.data.meshes.remove(mesh)
        bm.free()

    mesh0 = bpy.data.meshes.new(name)
    bm0.to_mesh(mesh0)
    obj0 = bpy.data.objects.new(name, mesh0)
    bpy.context.scene.collection.objects.link(obj0)
    bm0.free()

def export_furniture(name:str, mesh, vb_fmt="3f2,f2,3i1,i1,3i1,i1,2f2"):
    def inb(vv, q): return -vv[0], vv[2], -vv[1], q
    ib, vb0, index_map = [], [], {}
    for l in [mesh.loops[i+2-i%3*2] for i in range(len(mesh.loops))]:
        uvs = [layer.data[l.index].uv for layer in mesh.uv_layers]
        h = (l.vertex_index, *uvs[0], *l.normal)
        if h not in index_map:
            index_map[h] = len(vb0)
            vb0.append((inb(mesh.vertices[l.vertex_index].co, 1.),
                        inb(l.normal * 127., 0),
                        inb(l.tangent * 127., -l.bitangent_sign),
                        *[(uv[0], 1 - uv[1]) for uv in uvs]))
        ib.append(index_map[h])

    np.fromiter(ib, np.uint16).tofile(f"{name}-ib.buf")
    np.fromiter(vb0, np.dtype(vb_fmt)).tofile(f"{name}-vb0.buf")
# export_furniture("Furnitest", ["", "Soukaku", "Yanagi", "Unagi"], objs, vb_fmt="4f2,4i1,4i1,2f2,2f2")

#os.chdir(r"C:\mod\zzmi\FrameAnalysis-2024-12-29-210904")
#import_collected_furniture("StandNoviluna", "e478f8f0", "4f2,4i1,4u1,2f2")

os.chdir(r"C:\mod\zzmi\Mods\StandNoviluna")
mesh0 = bpy.context.selected_objects[0].data
export_furniture("StandNoviluna", mesh0, "4f2,4i1,4u1,2f2")