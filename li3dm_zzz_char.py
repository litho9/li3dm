import bpy, bmesh, numpy as np, os, time; from glob import glob
from shutil import copyfile

def log(data):
    for window in bpy.context.window_manager.windows:
        screen = window.screen
        for area in screen.areas:
            if area.type == 'CONSOLE':
                override = {'window': window, 'screen': screen, 'area': area}
                bpy.ops.console.scrollback_append(override, text=str(data), type="OUTPUT")


def prop(file:str, key:str): idx = file.index(key) + len(key) + 1; return file[idx:idx+8]

def collect_zzz(path:str, name:str, vb:str, in_dir:str, out_dir="collected", root_vs="e8425f64cfb887cd", blend_vb="vb2"):
    os.chdir(path)
    in_dir = in_dir or glob("FrameAnalysis*")[-1]
    print(f"From folder: {in_dir} to folder {out_dir}...")

    vb0_files = glob(f"{in_dir}/*-vb0={vb}*.buf")
    posed_file = [f for f in vb0_files][0]
    draw_id = os.path.split(posed_file)[-1][:6]
    print(f"draw_id={draw_id}")
    tex_file = glob(f"{in_dir}/{draw_id}-vb1=*.buf")[0]
    ib_file = glob(f"{in_dir}/{draw_id}-ib=*.buf")[0]

    pos_file_size = os.path.getsize(posed_file)  # the matching pointlist has the same size
    pointlist_vb0 = [f for f in glob(f"{in_dir}/*vb0*{root_vs}.buf") if os.path.getsize(f) == pos_file_size][0]
    blend_file = glob(f"{in_dir}/{os.path.split(pointlist_vb0)[-1][:6]}-{blend_vb}=*.buf")[0]

    for tex in [f for f in glob(f"{in_dir}/{draw_id}-ps-t*") if "!" not in f]:
        copyfile(tex, f"{out_dir}/{name}-{tex[42:53]}.{tex[-3:]}")
    copyfile(pointlist_vb0, f"{out_dir}/{name}-b0pos={prop(pointlist_vb0, 'vb0')}-draw={vb}.buf")
    copyfile(tex_file, f"{out_dir}/{name}-b1tex={prop(tex_file, 'vb1')}.buf")
    copyfile(ib_file, f"{out_dir}/{name}-b2ib={prop(ib_file, 'ib')}.buf")
    copyfile(blend_file, f"{out_dir}/{name}-b3blend={prop(blend_file, blend_vb)}.buf")

if __name__ == "__main__":
    start = time.time()
    path0 = "C:/Users/urmom/Documents/create/mod/zzz/3dmigoto_dev"

    # collect_zzz(path0, "SoukakuHair", "5432bbb8", "FrameAnalysis-2024-07-21-162646") # vertex_count=5924
    # collect_zzz(path0, "SoukakuBody", "ff00994d", "FrameAnalysis-2024-07-21-162646")
    # collect_zzz(path0, "SoukakuFace", "d06e95fd", "FrameAnalysis-2024-07-21-162646") # vertex_count=2165

    # collect_zzz(path0, "PiperHair", "da8a2564", "FrameAnalysis-2024-07-31-221208")
    collect_zzz(path0, "PiperBody", "d28231af", "FrameAnalysis-2024-10-22-100552")
    # collect_zzz(path0, "PiperFace", "67362536", "FrameAnalysis-2024-07-31-221208")
    # 1f0dbd2b PiperAxe 731ab501 9c1cfb7d

    # collect_zzz(path0, "NekomataFace", "c719aab9", "FrameAnalysis-2024-08-12-142640") # 5cfcac2d 8972f558
    # collect_zzz(path0, "NekomataHair", "a00df230", "FrameAnalysis-2024-08-12-142640") #f16498bf
    # collect_zzz(path0, "NekomataBody", "0c01e6a5", "FrameAnalysis-2024-08-12-145047") # tex=b5a4c084
    # collect_zzz(path0, "NekomataFace", "c719aab9", "FrameAnalysis-2024-08-12-142640") # 5cfcac2d 8972f558
    # collect_zzz(path0, "NekomataHair", "a00df230", "FrameAnalysis-2024-08-12-142640") #f16498bf
    # collect_zzz(path0, "NekomataBodyV1-1", "0c01e6a5", "FrameAnalysis-2024-08-14-083233") # 99132d05 is boots
    # collect_zzz(path0, "NekomataBootsV1-1", "99132d05", "FrameAnalysis-2024-08-14-083233") # 99132d05 is boots

    #collect_zzz(path0, "LucyBody", "da79199a", "FrameAnalysis-2024-08-25-084636")

    # collect_zzz(path0, "JaneFace", "5661afc3", "FrameAnalysis-2024-08-14-111119")  # 5661afc3 91846a84 cbdb9506
    # collect_zzz(path0, "JaneHair", "5721e4e7", "FrameAnalysis-2024-08-14-111119") # 0a10c747 5721e4e7 c8ad344e
    #collect_zzz(path0, "JaneBody", "d1aa4b85", "FrameAnalysis-2024-08-14-111119") # 8b85c03e 9727a184 d1aa4b85

    # collect_zzz(path0, "NpcGirl001Hair", "5b6ebc43", "FrameAnalysis-2024-07-25-192429")  # vertex count=3688
    # collect_zzz(path0, "NpcWoman001Hair", "6bcbf1c3", "FrameAnalysis-2024-07-25-192429")
    # collect_zzz(path0, "NpcSchoolgirl001Hair", "8c4b750e", "FrameAnalysis-2024-07-25-192429")

    #collect_zzz(path0, "Avocaboo", "38e7e949", "FrameAnalysis-2024-07-27-180010")
    #collect_zzz(path0, "AvocabooB", "b86a9738", "FrameAnalysis-2024-07-27-180010")

    #path0 = "C:/Users/urmom/Documents/create/mod/3dmigoto_dev"
    #collect_zzz(path0, "ArabalikaBody", "f3e2d803", "FrameAnalysis-2024-07-27-181520", root_vs="653c63ba4a73ca8b") # vertex_count=782
    #collect_zzz(path0, "ArabalikaHair", "6ee36691", "FrameAnalysis-2024-07-27-181520", root_vs="653c63ba4a73ca8b")
    #collect_zzz(path0, "ArabalikaEars", "62a109a8", "FrameAnalysis-2024-07-27-181520", root_vs="653c63ba4a73ca8b")
    #collect_zzz(path0, "ArabalikaStaff", "e0da29d2", "FrameAnalysis-2024-07-27-181520", root_vs="653c63ba4a73ca8b")

    print(f"Operation completed in {int((time.time()-start)*1000)}ms")

def inv(vv): return -vv[0], vv[1], vv[2]

# import bpy, glob, os, numpy as np, itertools
# noinspection PyTypeChecker
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
        color_layer.data[l.index].color = vb1[l.vertex_index][0]
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

path0 = "C:/Users/urmom/Documents/create/mod/zzz/3dmigoto_dev/collected"
#import_collected_zzz(path0, "SoukakuFace", [f32,f32,f32,f32])
#import_collected_zzz(path0, "SoukakuHair")
#import_collected_zzz(path0, "SoukakuBody")
import_collected_zzz(path0, "LucyCloth", (np.float16, np.float32, np.float16))


# noinspection PyTypeChecker
def export_zzz_char(name, obj, text_fns=(np.float16, np.float32, np.float16)):
    with open(f"{name}-vb0.buf", "wb") as vb0, \
            open(f"{name}-vb1.buf", "wb") as vb1, \
            open(f"{name}-ib.buf", "wb") as ib, \
            open(f"{name}-vb2.buf", "wb") as vb2:
        # log(f"processing object {obj.name}. there are {len(obj.data.loops)} loops...")
        obj.data.calc_tangents()
        color = obj.data.vertex_colors[0].data
        index_map = {}
        idx = 0
        for loop in [obj.data.loops[i+2-i%3*2] for i in range(len(obj.data.loops))]:
            [u, v] = obj.data.uv_layers[0].data[loop.index].uv
            nor = inv(loop.normal)
            h = (loop.vertex_index, u, v) + nor
            if h in index_map:
                ib.write(np.uint32(index_map[h]))
                continue
            index_map[h] = idx
            ib.write(np.uint32(idx))  # ib.write(np.uint32(index_map[h]))
            idx += 1

            co = inv(obj.data.vertices[loop.vertex_index].co)
            vb0.write(np.fromiter(co + nor + inv(loop.tangent) + (-loop.bitangent_sign,), np.float32))

            c = np.fromiter(color[loop.index].color, np.float32)
            vb1.write(np.around(c * 255.0).astype(np.uint8))
            for i, uv in enumerate([tex.data[loop.index].uv for tex in obj.data.uv_layers]):
                vb1.write(np.fromiter([uv[0], uv[1]], text_fns[i]))

            g = obj.data.vertices[loop.vertex_index].groups
            weight = [g[i].weight if i < len(g) else .0 for i in range(4)]
            index = [g[i].group if i < len(g) else 0 for i in range(4)]
            vb2.write(np.fromiter(weight, np.float32))
            vb2.write(np.fromiter(index, np.int32))

        print(f"drawindexed = {idx}")

os.chdir(r"C:\mod\downloads")
obj0 = bpy.context.selected_objects[0]
export_zzz_char("EllenHead", obj0)