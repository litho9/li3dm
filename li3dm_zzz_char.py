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
    mesh.vertex_colors.new().data.foreach_set("color", [c for d in data for c in d[0] / 255])
    for i in range(1, len(vb1[0])):
        mesh.uv_layers.new().data.foreach_set("uv", [c for d in data for c in d[i]])

    vb2 = np.fromfile(glob(f"{draw}-vb2=*.buf")[0], np.dtype("4f, 4i"))
    c = [(v, w, i) for v, b in enumerate(vb2) for w, i in zip(*b) if w]
    for i in range(max([x[2] for x in c]) + 1): obj.vertex_groups.new(name=str(i))
    for v, w, i in c: obj.vertex_groups[i].add((v,), w, 'REPLACE')

    with open("log.txt", encoding='utf-8') as log_file:
        while not log_file.readline().startswith(f"{draw} CopyResource"): continue
        line = log_file.readline()
    sk_ids = [f[:6] for f in glob(f"*u0={line[line.rfind('=') + 1:-1]}*.buf")]
    shape_keys = [np.fromfile(sk, "i,i,f,f")[0] for sk_id in sk_ids
                  for sk in glob(f"{sk_id}-cs-cb0*.buf")] # offset, count, multiplier, garbage
    cs_t0 = np.fromfile(glob(f"{sk_ids[0]}-cs-t0*.buf")[0], "i,3f,3f,3f") # vertex_index, pos, normal, tangent
    for (offset, count, mult, garbage) in shape_keys:
        for i in range(offset, offset+count):
            mesh.vertices[cs_t0[i][0]].co[0] += cs_t0[i][1][0]*mult
            mesh.vertices[cs_t0[i][0]].co[1] -= cs_t0[i][1][1]*mult
            mesh.vertices[cs_t0[i][0]].co[2] -= cs_t0[i][1][2]*mult
    obj.shape_key_add(name="Basis", from_mix=False)
    sk = obj.shape_key_add(name="0", from_mix=False)
    last_idx = -1
    for offset, (idx, pos, *_) in enumerate(cs_t0):
        if idx <= last_idx:
            sk = obj.shape_key_add(name=str(offset), from_mix=False)
        sk.data[idx].co[0] -= pos[0]
        sk.data[idx].co[1] += pos[1]
        sk.data[idx].co[2] += pos[2]
        last_idx = idx
    # for sk in shape_keys:
    #     obj.data.shape_keys.key_blocks[str(sk[0])].value = sk[2]

    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.remove_doubles(threshold=1e-6, use_sharp_edge_from_normals=True)
    bpy.ops.object.mode_set(mode='OBJECT')

    mat = bpy.data.materials.new(f"{name}Material")
    obj.data.materials.append(mat)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    tex_image = mat.node_tree.nodes.new('ShaderNodeTexImage')
    img = bpy.data.images.load(os.path.abspath(glob(f"{draw2}-ps-t3=*.dds")[0]), check_existing=True)
    tex_image.image = img
    mat.node_tree.links.new(bsdf.inputs['Base Color'], tex_image.outputs['Color'])
    with bpy.context.temp_override(edit_image=img):
        bpy.ops.image.flip(use_flip_y=True)

def export_shape_key(obj, sk_idx=0):
    z = zip(obj.data.vertices, obj.data.shape_keys.key_blocks[sk_idx].data)
    cst0 = [(v.index, inv(skv.co - v.co), (0.,)*6) for (v, skv) in z if v.co != skv.co]
    np.fromiter(cst0, "i,3f,6f").tofile("Soukaku1Face-cs-t0.buf")
#os.chdir(r"C:\mod\zzmi\Mods\SoukakuHalf")
#export_shape_key(bpy.data.objects['Aokaku_Face.001'], 54)

def zzz_char_export(name, objs, vb1_fmt="4u1,2f2,2f,2f2"):
    ib, vb0, vb1, vb2, index_map = [], [], [], [], {}
    for mesh in [obj.data for obj in objs]:
        mesh.calc_tangents()
        print(f"; {mesh.name}\ndrawindexed = {len(mesh.loops)}, {len(ib)}, 0")
        # mesh.polygons.map{reverse(it.loop_indices)}.flatMap{mesh.loops[it]}
        for loop in [mesh.loops[i] for p in mesh.polygons for i in reversed(p.loop_indices)]:
        # for loop in [mesh.loops[i + 2 - i % 3 * 2] for i in range(len(mesh.loops))]:
            h = (loop.vertex_index, *mesh.uv_layers[0].data[loop.index].uv, *loop.normal)
            if h not in index_map:
                index_map[h] = len(vb0)
                v = mesh.vertices[loop.vertex_index]
                vb0.append((inv(v.co), inv(loop.normal), inv(loop.tangent), -loop.bitangent_sign))
                vb1.append(([int(i * 255) for i in mesh.vertex_colors[0].data[loop.index].color],
                            *[tex.data[loop.index].uv for tex in mesh.uv_layers]))
                vb2.append(zip(*(list((g.weight,g.group) for g in v.groups) + [(.0,0)]*(4-len(v.groups)))))
            ib.append(index_map[h])
    print(f"draw = {len(vb0)}, 0")

    np.fromiter(ib, np.uint16).tofile(f"{name}-ib.buf")
    np.fromiter(vb0, "3f,3f,3f,f").tofile(f"{name}-vb0.buf")
    np.fromiter(vb1, vb1_fmt).tofile(f"{name}-vb1.buf")
    np.fromiter(vb2, "4f, 4i").tofile(f"{name}-vb2.buf")

def zzz_export_char_materials(name:str, obj, vb1_fmt="4f2,4i1,4i1,2f2"):
    mesh = obj.data
    mesh.calc_tangents()
    ib, vb0, vb1, vb2, index_map, offset = [], [], [], [], {}, 0
    for m in obj.material_slots:
        for loop in [mesh.loops[i] for p in mesh.polygons for i in reversed(p.loop_indices) if p.material_index == m.slot_index]:
            h = (loop.vertex_index, *mesh.uv_layers[0].data[loop.index].uv, *loop.normal)
            if h not in index_map:
                index_map[h] = len(vb0)
                v = mesh.vertices[loop.vertex_index]
                vb0.append((inv(v.co), inv(loop.normal), inv(loop.tangent), -loop.bitangent_sign))
                vb1.append(([int(i * 255) for i in mesh.vertex_colors[0].data[loop.index].color],
                            *[tex.data[loop.index].uv for tex in mesh.uv_layers]))
                vb2.append(([v.groups[i].weight if i < len(v.groups) else .0 for i in range(4)],
                            [v.groups[i].group if i < len(v.groups) else 0 for i in range(4)]))
            ib.append(index_map[h])
        print(f"; {m.name}\ndrawindexed = {len(ib) - offset}, {offset}, 0")
        offset = len(ib)
    print(f"draw = {len(vb0)}")

    np.fromiter(ib, np.uint32).tofile(f"{name}IB.buf")
    np.fromiter(vb0, "3f,3f,3f,f").tofile(f"{name}VB0.buf")
    np.fromiter(vb1, vb1_fmt).tofile(f"{name}VB1.buf")
    np.fromiter(vb2, "4f, 4i").tofile(f"{name}VB2.buf")

def read_buffers(vb1_hash:str, ib="3u2", vb0="3f,3f,4f", vb1="4u1,2f2,2f,2f2", vb2="i4"):
    vb1_files = glob(f"*vb1={vb1_hash}*.buf")
    d1, d2 = vb1_files[0][:6], vb1_files[1][:6]
    def r(draw, buf, fmt): np.fromfile(glob(f"{draw}-{buf}=*.buf")[0], np.dtype(fmt))
    return r(d2, "ib", ib), r(d1, "vb0", vb0), r(d1, "vb1", vb1), r(d1, "vb2", vb2)

def zzz_weapon_import(name:str, vb1_hash:str, vb1_fmt="4u1,2f2,2f,2f2", vb2_fmt="i4"):
    vb1_files = glob(f"*vb1={vb1_hash}*.buf")
    draw, draw2 = vb1_files[0][:6], vb1_files[1][:6]
    ib = np.fromfile(glob(f"{draw2}-ib=*.buf")[0], np.dtype("3u2"))
    vb0 = np.fromfile(glob(f"{draw}-vb0=*.buf")[0], np.dtype("3f,3f,4f"))
    vb1 = np.fromfile(glob(f"{draw}-vb1=*.buf")[0], np.dtype(vb1_fmt))
    vb2 = np.fromfile(glob(f"{draw}-vb2=*.buf")[0], np.dtype(vb2_fmt))

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

os.chdir(r"C:\mod\zzmi\FrameAnalysis-2024-12-25-094405")  # ellen
#zzz_char_import("EllenBody", "5ac6d5ee", "4u1,2f2,2f,2f2,2f2")
#zzz_char_import("EllenHead", "a27a8e1a", "4u1,2f2,2f,2f2,2f2")
zzz_char_import("EllenFace", "d6890fb1", "4u1,2f,2f,2f,2f")

os.chdir(r"C:\mod\zzmi\Mods\EllenMod")
obj0 = bpy.context.selected_objects[0]
zzz_char_export("EllenBody", obj0.data, "4u1,2f2,2f,2f2,2f2")

def get_ini_text(part, n:str, vb_len:int, vb1_stride=20):
    o, r = f"TextureOverride_{n}", f"Resource{n}"
    return f"""
[{o}.Position]\n;hash = {part['vb0']}\nvb0 = {r}VB0\nvb2 = {r}VB2\ndraw = {vb_len},0"
[{o}.Texcoord]\nhash = {part['vb1']}\nvb1 = {r}VB1
[{o}.VertexLimitRaise]\nhash = {part['vb00']}
[{o}.IB]\nhash = {part['ib']}\nhandling = skip\nib = {r}IB\ndrawindexed = auto
[{r}VB0]\ntype = Buffer\nstride = 40\nfilename = {n}-vb0.buf
[{r}VB1]\ntype = Buffer\nstride = {vb1_stride}\nfilename = {n}-vb1.buf
[{r}VB2]\ntype = Buffer\nstride = 32\nfilename = {n}-vb2.buf
[{r}IB]\ntype = Buffer\nformat = DXGI_FORMAT_R16_UINT\nfilename = {n}-ib.buf"""
