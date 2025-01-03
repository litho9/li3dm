import bpy, numpy as np, os
from glob import glob

def inv(vv): return -vv[0], vv[1], vv[2]

def zzz_char_import(name:str, vb1_hash:str, vb1_fmt="4u1,2f2,2f,2f2"):
    vb1_files = glob(f"*vb1={vb1_hash}*.buf")
    draw, draw2 = vb1_files[0][:6], vb1_files[1][:6]
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)

    vb0 = np.fromfile(glob(f"{draw}-vb0=*.buf")[0], np.dtype("3f,3f,4f"))
    ib = np.fromfile(glob(f"{draw2}-ib=*.buf")[0], np.dtype("3u2"))
    mesh.from_pydata([inv(p[0]) for p in vb0], [], [list(reversed(p)) for p in ib])
    mesh.polygons.foreach_set("use_smooth", [True] * len(mesh.polygons))
    mesh.normals_split_custom_set_from_vertices([inv(p[1]) for p in vb0])

    vb1 = np.fromfile(glob(f"{draw}-vb1=*.buf")[0], np.dtype(vb1_fmt))
    data = [vb1[l.vertex_index] for l in mesh.loops]
    mesh.vertex_colors.new().data.foreach_set("color", [c for d in data for c in d[0] / 256])
    for i in range(1, len(vb1[0])):
        mesh.uv_layers.new().data.foreach_set("uv", [c for d in data for c in d[i]])

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

    # for chunk in t0_chunks:
    #     for j in range(chunk['offset'], chunk['count'] + chunk['offset']):
    #         vb['pos'][t0[j]['vertindex']] -= t0[j]['pos']
    # for chunk in t0_chunks:
    #     co = np.zeros(len(mesh.vertices), dtype=(np.float32,3))
    #     for j in range(chunk['offset'], chunk['count'] + chunk['offset']):
    #         co[t0[j]['vertindex']] = t0[j]['pos']
    #     obj.shape_key_add().data.foreach_set('co', co.ravel()+vb['pos'].ravel())

    mat = bpy.data.materials.new(f"{name}Diffuse")
    obj.data.materials.append(mat)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    tex_image = mat.node_tree.nodes.new('ShaderNodeTexImage')
    img = bpy.data.images.load(os.path.abspath(glob(f"{draw2}-ps-t3=*.dds")[0]), check_existing=True)
    tex_image.image = img
    mat.node_tree.links.new(bsdf.inputs['Base Color'], tex_image.outputs['Color'])
    with bpy.context.temp_override(edit_image=img):
        bpy.ops.image.flip(use_flip_y=True)

# noinspection PyTypeChecker
def zzz_char_export(name, mesh, vb1_fmt="4u1,2f2,2f,2f2"):
    mesh.calc_tangents()
    ib, vb0, vb1, vb2, index_map, idx = [], [], [], [], {}, 0
    for loop in [mesh.loops[i+2-i%3*2] for i in range(len(mesh.loops))]:
        h = (loop.vertex_index, *mesh.uv_layers[0].data[loop.index].uv, *loop.normal)
        if h not in index_map:
            index_map[h] = idx; idx += 1  # stoopid python has no 'idx++' syntax
            v = mesh.vertices[loop.vertex_index]
            vb0.append((inv(v.co), inv(loop.normal), inv(loop.tangent), -loop.bitangent_sign))
            vb1.append(([int(i * 256) for i in mesh.vertex_colors[0].data[loop.index].color],
                        *[tex.data[loop.index].uv for tex in mesh.uv_layers]))
            vb2.append(([v.groups[i].weight if i < len(v.groups) else .0 for i in range(4)],
                        [v.groups[i].group if i < len(v.groups) else 0 for i in range(4)]))
        ib.append(index_map[h])
    print(f"drawindexed = {idx}")

    np.fromiter(ib, np.uint16).tofile(f"{name}-ib.buf")
    np.fromiter(vb0, np.dtype("3f,3f,3f,f")).tofile(f"{name}-vb0.buf")
    np.fromiter(vb1, np.dtype(vb1_fmt)).tofile(f"{name}-vb1.buf")
    np.fromiter(vb2, np.dtype("4f, 4i")).tofile(f"{name}-vb2.buf")

os.chdir(r"C:\mod\zzmi\FrameAnalysis-2024-12-25-094405")  # ellen
#zzz_char_import("EllenBody", "5ac6d5ee", "4u1,2f2,2f,2f2,2f2")
#zzz_char_import("EllenHead", "a27a8e1a", "4u1,2f2,2f,2f2,2f2")
zzz_char_import("EllenFace", "d6890fb1", "4u1,2f,2f,2f,2f")

os.chdir(r"C:\mod\zzmi\Mods\EllenMod")
obj0 = bpy.context.selected_objects[0]
zzz_char_export("EllenBody", obj0.data, "4u1,2f2,2f,2f2,2f2")