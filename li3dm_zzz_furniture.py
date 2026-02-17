import bpy, bmesh, numpy as np, os
from glob import glob

# https://gist.github.com/litho9/bacf2eb1de1367d2803f7116749df86f

def import_collected_furniture(name:str, vb0_hash:str, vb_fmt="4f2,4i1,4i1,2f2"):
    vb_file = glob(f"*vb0={vb0_hash}*.buf")[0]
    vb = np.fromfile(vb_file, np.dtype(vb_fmt))
    ib = np.fromfile(glob(f"{vb_file[:6]}-ib=*.buf")[0], np.dtype("3u2"))

    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(mesh.name, mesh)
    bpy.context.scene.collection.objects.link(obj)

    def inf(vv): return -vv[0], -vv[2], vv[1]
    mesh.from_pydata([inf(p[0]) for p in vb], [], [list(reversed(p)) for p in ib])
    mesh.polygons.foreach_set("use_smooth", [True] * len(mesh.polygons))
    mesh.normals_split_custom_set_from_vertices([inf(p[1] / 127) for p in vb])
    for i in range(3, len(vb[0])):
        uv_data = [uv for l in mesh.loops for uv in vb[l.vertex_index][i]]
        mesh.uv_layers.new().data.foreach_set("uv", uv_data)

    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.remove_doubles(threshold=.000001, use_sharp_edge_from_normals=True)
    bpy.ops.object.mode_set(mode='OBJECT')

    mat = bpy.data.materials.new(f"{name}Diffuse")
    obj.data.materials.append(mat)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    tex_image = mat.node_tree.nodes.new('ShaderNodeTexImage')
    img = bpy.data.images.load(os.path.abspath(glob(f"{vb_file[:6]}-ps-t2=*.dds")[0]), check_existing=True)
    tex_image.image = img
    mat.node_tree.links.new(bsdf.inputs['Base Color'], tex_image.outputs['Color'])
    with bpy.context.temp_override(edit_image=img):
        bpy.ops.image.flip(use_flip_y=True)

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

        bm = bmesh.new()  # eu me bmesho muito, eu me bmesho muito, eu me bmesho muito, bmesho... MUITO!
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

def export_furniture(name:str, mesh, vb_fmt="4f2,4i1,4i1,2f2"):
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
#import_collected_furniture("StandNoviluna", "e478f8f0", "4f2,4i1,4i1,2f2")

os.chdir(r"C:\mod\zzmi\Mods\StandNoviluna")
mesh0 = bpy.context.selected_objects[0].data
export_furniture("StandNoviluna", mesh0, "4f2,4i1,4i1,2f2")

def zzz_export_furniture_data(objs, frames=100):
    ib, idx, m = [], 0, []
    for obj in objs:
        index_map = {}
        m.append([])
        mesh = obj.data
        print(f"; {obj.name}\ndrawindexed = {len(mesh.loops)}, {len(ib)}, 0")
        mesh.calc_tangents()
        for loop in [mesh.loops[i] for p in mesh.polygons for i in reversed(p.loop_indices)]:
            h = (loop.vertex_index, *mesh.uv_layers[0].data[loop.index].uv, *loop.normal)
            if h not in index_map:
                index_map[h] = idx; idx += 1  # stoopid python has no i++ syntax
                m[-1].append(loop.index)
            ib.append(index_map[h])
    print(f"\n$vert_count={idx}\n")

    def inb(vv, q): return -vv[0], vv[2], -vv[1], q
    deps = bpy.context.evaluated_depsgraph_get()
    vb0 = []
    for i in range(1, frames + 1):
        print(f"creating frame {i}")
        bpy.context.scene.frame_set(i)
        for obj_idx, obj in enumerate(objs):
            bm = bmesh.new()
            bm.from_object(obj, deps)
            bm.faces.ensure_lookup_table()
            bm.transform(obj.matrix_world)
            print(f"{i} obj={obj.name}")

            agh = {}  # bmesh is dumb
            for face in bm.faces:
                for l in face.loops:
                    agh[l.index] = l

            # for loop in [l for face in bm.faces for l in reversed(face.loops)]:
            for loop in (agh[loop_idx] for loop_idx in m[obj_idx]):
                co = inb(loop.vert.co, 1.)
                nor = inb(loop.calc_normal() * 127., 0)
                bit = obj.data.loops[loop.index].bitangent_sign
                tan = inb(loop.calc_tangent() * 127., -bit * 127.)
                uv = obj.data.uv_layers[0].data[loop.index].uv
                vb0.append((co, nor, tan, (0,-256), uv, uv))
            bm.free()
    return ib, vb0

print("\n\n Coffee Table - S6 Maids!!")
os.chdir(r"C:\mod\zzmi\Mods\[obj] CoffeeTableS6Maids [lioh]")
naems = ["CoffeeTable", "Miyabi1Face", "Miyabi2Hair", "MiyabiMaidBody.bodyN", "Aokaku_Face.001", "Soukaku2Hair", "Soukaku3Body", "SoukakuN.nokeys", "MiyabiMaidBody.maid", "Maid.apron.raster", "Maid.shirt.raster", "Maid.thong.raster", "SoukakuMaid.socks.001", "Cum Anim.006"]
#naems = ["CoffeeTable"]
#objs = sorted(bpy.context.selected_objects, key=lambda x: x.name)
objs = list((bpy.data.objects[n] for n in naems))
ib, vb0 = zzz_export_furniture_data(objs, frames=100)
np.fromiter(ib, np.uint32).tofile("CoffeeTable-ib.buf")
np.fromiter(vb0, np.dtype("4f2,4i1,4i1,2i2,2f2,2f2")).tofile("CoffeeTable-vb0.buf")
print("abacou")
