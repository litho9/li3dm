import bpy, os, numpy as np
from glob import glob

def inv(vv): return -vv[0], -vv[2], vv[1]

def gi_char_import(name:str, idx, part, diffuseName, vb1_fmt="4u1,2f,2f"):
    ib = np.fromfile(glob(f"{name}*ib")[idx], np.dtype("3u4"))
    vb0 = np.fromfile(glob(f"{name}Position*.buf")[0], np.dtype("3f,3f,4f"))
    vb1 = np.fromfile(glob(f"{name}Texcoord*.buf")[0], np.dtype(vb1_fmt))
    vb2 = np.fromfile(glob(f"{name}Blend*.buf")[0], np.dtype("4f, 4i"))

    for n, length, offset in part:
        section = ib[offset//3:(offset+length)//3]
        mesh = bpy.data.meshes.new(n)
        obj = bpy.data.objects.new(n, mesh)
        bpy.context.scene.collection.objects.link(obj)
        mesh.from_pydata([inv(p[0]) for p in vb0], [], [list(reversed(p)) for p in section])
        mesh.polygons.foreach_set("use_smooth", [True] * len(mesh.polygons))
        mesh.normals_split_custom_set_from_vertices([inv(p[1]) for p in vb0])

        data = [vb1[l.vertex_index] for l in mesh.loops]
        mesh.vertex_colors.new().data.foreach_set("color", [c for d in data for c in d[0] / 255])
        for i in range(1, len(vb1[0])):
            mesh.uv_layers.new().data.foreach_set("uv", [c for d in data for c in (d[i][0], 1-d[i][1])])

        c = [(v, w, i) for v, b in enumerate(vb2) for w, i in zip(*b) if w]
        for i in range(max([x[2] for x in c]) + 1): obj.vertex_groups.new(name=str(i))
        for v, w, i in c: obj.vertex_groups[i].add((v,), w, 'REPLACE')

        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.remove_doubles(threshold=.000001, use_sharp_edge_from_normals=True)
        bpy.ops.mesh.delete_loose()
        bpy.ops.object.mode_set(mode='OBJECT')

        mat = bpy.data.materials.new(f"{name}Diffuse")
        obj.data.materials.append(mat)
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes["Principled BSDF"]
        tex_image = mat.node_tree.nodes.new('ShaderNodeTexImage')
        img = bpy.data.images.load(os.path.abspath(glob(f"{name}{diffuseName}*.jpg")[0]), check_existing=True)
        tex_image.image = img
        mat.node_tree.links.new(bsdf.inputs['Base Color'], tex_image.outputs['Color'])

os.chdir(r"C:\mod\gimi\Mods\EulaMod")
#gi_char_import("Eula", 1, part3, "DressDiffuse") # dress
gi_char_import("Eula", 0, part2, "BodyDiffuse3") # body
#gi_char_import("Eula", 2, part1, "BodyHead") # head