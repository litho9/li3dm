import bpy, numpy as np, os
from glob import glob

def inv(vv): return -vv[0], vv[1], vv[2]

def import_char_from_zzz_analysis(vb1_hash:str, name:str, vb1_fmt="4u1,2f2,2f,2f2"):
    vb1_files = glob(f"*vb1={vb1_hash}*.buf")
    draw = vb1_files[0][:6]
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)

    vb0 = np.fromfile(glob(f"{draw}-vb0=*.buf")[0], np.dtype("3f,3f,4f"))
    ib = np.fromfile(glob(f"{vb1_files[1][:6]}-ib=*.buf")[0], np.dtype("3u2"))
    mesh.from_pydata([inv(p[0]) for p in vb0], [], [list(reversed(p)) for p in ib])
    mesh.polygons.foreach_set("use_smooth", [True] * len(mesh.polygons))
    mesh.normals_split_custom_set_from_vertices([inv(p[1]) for p in vb0])

    vb1 = np.fromfile(glob(f"{draw}-vb1=*.buf")[0], np.dtype(vb1_fmt))
    color_layer = mesh.vertex_colors.new()
    for _ in range(len(vb1[0])-1):
        mesh.uv_layers.new()
    for l in mesh.loops:
        color_layer.data[l.index].color = [c/256 for c in vb1[l.vertex_index][0]]
        for i, uv_layer in enumerate(mesh.uv_layers):
            uv_layer.data[l.index].uv = vb1[l.vertex_index][i+1]

    bld = np.fromfile(glob(f"{draw}-vb2=*.buf")[0], np.dtype("4f, 4i"))
    c = [(v, w, i) for v in range(len(bld)) for w, i in zip(bld[v][0], bld[v][1]) if w != 0]
    for i in range(max([x[2] for x in c]) + 1):
        obj.vertex_groups.new(name=str(i))
    for v, w, i in c:
        obj.vertex_groups[i].add((v,), w, 'REPLACE')

    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.remove_doubles(threshold=.000001, use_sharp_edge_from_normals=True)
    bpy.ops.object.mode_set(mode='OBJECT')

    for diffuse in glob(f"{name}*.png"):
        mat = bpy.data.materials.new(name=f"LynMaterial")
        obj.data.materials.append(mat)
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes["Principled BSDF"]
        tex_image = mat.node_tree.nodes.new('ShaderNodeTexImage')
        tex_image.image = bpy.data.images.load(diffuse)
        mat.node_tree.links.new(bsdf.inputs['Base Color'], tex_image.outputs['Color'])

# noinspection PyTypeChecker
def export_zzz_char(name, obj, vb1_fmt="4u1,2f2,2f,2f2"):
    agh, index_map, idx = [], {}, 0
    for loop in [obj.data.loops[i+2-i%3*2] for i in range(len(obj.data.loops))]:
        h = (loop.vertex_index, *obj.data.uv_layers[0].data[loop.index].uv, *loop.normal)
        b = h not in index_map
        if b: index_map[h] = idx; idx += 1  # stoopid python has no 'idx++' syntax
        vert = obj.data.vertices[loop.vertex_index] if b else None
        agh.append((loop, index_map[h], vert))
    print(f"drawindexed = {idx}")

    np.fromiter([a[1] for a in agh], np.uint16).tofile(f"{name}-ib.buf")

    obj.data.calc_tangents()
    agh2 = [(l, v) for l, _, v in agh if v]
    a = [(inv(v.co), inv(l.normal), inv(l.tangent), -l.bitangent_sign) for l, v in agh2]
    np.fromiter(a, np.dtype("3f,3f,3f,f")).tofile(f"{name}-vb0.buf")

    color = obj.data.vertex_colors[0].data
    t = [([int(i * 256) for i in color[l.index].color],
         *[tex.data[l.index].uv for tex in obj.data.uv_layers]) for l, _ in agh2]
    np.fromiter(t, np.dtype(vb1_fmt)).tofile(f"{name}-vb1.buf")

    r = [([v.groups[i].weight if i < len(v.groups) else .0 for i in range(4)],
          [v.groups[i].group if i < len(v.groups) else 0 for i in range(4)]) for l, v in agh2]
    np.fromiter(r, np.dtype("4f, 4i")).tofile(f"{name}-vb2.buf")

os.chdir(r"C:\mod\zzmi\FrameAnalysis-2024-12-25-094405")  # ellen
import_char_from_zzz_analysis("5ac6d5ee", "EllenBody", "4u1,2f2,2f,2f2,2f2")

os.chdir(r"C:\mod\zzmi\Mods\EllenMod")
obj0 = bpy.context.selected_objects[0]
export_zzz_char("EllenBody", obj0, "4u1,2f2,2f,2f2,2f2")