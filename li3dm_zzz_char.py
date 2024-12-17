import bpy, bmesh, numpy, itertools, os, time
from glob import glob
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
    posed_file = [f for f in vb0_files][1]
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
    path0 = "C:/Users/cyrog/Documents/create/mod/zzz/3dmigoto_dev"

    # collect_zzz(path0, "SoukakuHair", "5432bbb8", "FrameAnalysis-2024-07-21-162646") # vertex_count=5924
    # collect_zzz(path0, "SoukakuBody", "ff00994d", "FrameAnalysis-2024-07-21-162646")
    # collect_zzz(path0, "SoukakuFace", "d06e95fd", "FrameAnalysis-2024-07-21-162646") # vertex_count=2165

    collect_zzz(path0, "PiperHair", "da8a2564", "FrameAnalysis-2024-07-31-221208")
    collect_zzz(path0, "PiperBody", "d28231af", "FrameAnalysis-2024-07-31-221208")
    collect_zzz(path0, "PiperFace", "67362536", "FrameAnalysis-2024-07-31-221208")
    # 1f0dbd2b PiperAxe 731ab501 9c1cfb7d

    # collect_zzz(path0, "NpcGirl001Hair", "5b6ebc43", "FrameAnalysis-2024-07-25-192429")  # vertex count=3688
    # collect_zzz(path0, "NpcWoman001Hair", "6bcbf1c3", "FrameAnalysis-2024-07-25-192429")
    # collect_zzz(path0, "NpcSchoolgirl001Hair", "8c4b750e", "FrameAnalysis-2024-07-25-192429")

    #collect_zzz(path0, "Avocaboo", "38e7e949", "FrameAnalysis-2024-07-27-180010")
    #collect_zzz(path0, "AvocabooB", "b86a9738", "FrameAnalysis-2024-07-27-180010")

    #path0 = "C:/Users/cyrog/Documents/create/mod/3dmigoto_dev"
    #collect_zzz(path0, "ArabalikaBody", "f3e2d803", "FrameAnalysis-2024-07-27-181520", root_vs="653c63ba4a73ca8b") # vertex_count=782
    #collect_zzz(path0, "ArabalikaHair", "6ee36691", "FrameAnalysis-2024-07-27-181520", root_vs="653c63ba4a73ca8b")
    #collect_zzz(path0, "ArabalikaEars", "62a109a8", "FrameAnalysis-2024-07-27-181520", root_vs="653c63ba4a73ca8b")
    #collect_zzz(path0, "ArabalikaStaff", "e0da29d2", "FrameAnalysis-2024-07-27-181520", root_vs="653c63ba4a73ca8b")

    print(f"Operation completed in {int((time.time()-start)*1000)}ms")


# import bpy, glob, os, numpy as np, itertools
def import_collected_zzz(path:str, name:str, tex_fns):
    files = glob(f"{path}/{name}-b*.buf")
    pos, tex, ib, blend = [open(f, "rb") for f in files]
    vertex_count = os.path.getsize(os.path.join(path, files[0])) // 40
    positions, normals, colors, indices, weights = [], [], [], [], []
    uvs = [[] for _ in range(len(tex_fns))]
    for i in range(vertex_count):
        [px, py, pz, nx, ny, nz] = numpy.frombuffer(pos.read(24), numpy.float32)
        positions.append((-px, py, pz))
        normals.append((-nx, ny, nz))
        pos.read(16)  # throw tangent info away, it will be recalculated on export

        colors.append(np.frombuffer(tex.read(4), np.uint8))
        for j, fmt in enumerate(tex_fns):
            uvs[j].append(np.frombuffer(tex.read(np.dtype(fmt).itemsize * 2), fmt))

        weights.append(numpy.frombuffer(blend.read(16), numpy.float32))
        indices.append(numpy.frombuffer(blend.read(16), numpy.int32))

    ib_section = numpy.frombuffer(bytearray(ib.read()), numpy.uint16)
    faces = [list(reversed(ib_section[i*3:i*3+3])) for i in range(len(ib_section)//3)]

    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    mesh.from_pydata(positions, [], faces)
    bpy.context.scene.collection.objects.link(obj)

    mesh.polygons.foreach_set("use_smooth", [True] * len(mesh.polygons))
    mesh.calc_normals_split()
    mesh.use_auto_smooth = True
    mesh.normals_split_custom_set_from_vertices(normals)

    color_layer = mesh.vertex_colors.new()
    for l in mesh.loops:
        color_layer.data[l.index].color = colors[l.vertex_index]
    for uv in uvs:
        uv_layer = mesh.uv_layers.new()
        for l in mesh.loops:
            uv_layer.data[l.index].uv = uv[l.vertex_index]
    for i in range(max(itertools.chain(*indices)) + 1):
        obj.vertex_groups.new(name=str(i))
    for vid in range(len(weights)):
        for w, i in zip(weights[vid], indices[vid]):
            if w != 0:
                obj.vertex_groups[i].add((vid,), w, 'REPLACE')

    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.remove_doubles(threshold=.000001, use_sharp_edge_from_normals=True)
    bpy.ops.object.mode_set(mode='OBJECT')

    for diffuse in glob(f"{path}/{name}*.png"):
        mat = bpy.data.materials.new(name=f"LynMaterial")
        obj.data.materials.append(mat)
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes["Principled BSDF"]
        tex_image = mat.node_tree.nodes.new('ShaderNodeTexImage')
        tex_image.image = bpy.data.images.load(diffuse)
        mat.node_tree.links.new(bsdf.inputs['Base Color'], tex_image.outputs['Color'])

path0 = "C:/Users/cyrog/Documents/create/mod/zzz/3dmigoto_dev/collected"
#import_collected_zzz(path0, "SoukakuFace", [f32,f32,f32,f32])
#import_collected_zzz(path0, "SoukakuHair")
#import_collected_zzz(path0, "SoukakuBody")
import_collected_zzz(path0, "LucyCloth", (np.float16, np.float32, np.float16))

def export_zzz_char(path, name, text_fns=(numpy.float16, numpy.float32, numpy.float16)):
    with open(f"{path}/{name}Position.li.buf", "wb") as bufPos, \
            open(f"{path}/{name}Blend.li.buf", "wb") as bufBlend, \
            open(f"{path}/{name}Texcoord.li.buf", "wb") as bufTex:
        offset = 0
        for obj in sorted(bpy.context.selected_objects, key=lambda x: x.name):  # list selected objects by index
            # log(f"processing object {obj.name}. there are {len(obj.data.loops)} loops...")
            obj.data.calc_tangents()
            color = obj.data.vertex_colors[0].data
            with open(f"{path}/{name}-{obj.name.split('.')[0]}.li.ib", "wb") as ib:
                index_map = {}
                idx = 0
                for loop in obj.data.loops:
                    co = obj.data.vertices[loop.vertex_index].co
                    [u, v] = obj.data.uv_layers[0].data[loop.index].uv
                    nor = numpy.fromiter(loop.normal, numpy.float32)
                    tan = numpy.fromiter(loop.tangent, numpy.float32)

                    h = (loop.vertex_index, u, v, nor[0], nor[1], nor[2])
                    if h in index_map:
                        ib.write(numpy.uint32(index_map[h] + offset))
                        continue
                    index_map[h] = idx
                    ib.write(numpy.uint32(idx + offset))  # ib.write(numpy.uint32(index_map[h]))
                    idx += 1

                    arr = [-co.x, co.y, co.z, nor[0], -nor[1], nor[2]]
                    arr += [-tan[0], -tan[1], tan[2], loop.bitangent_sign]
                    bufPos.write(numpy.fromiter(arr, numpy.float32))  # 32 bits each

                    c = numpy.fromiter(color[loop.index].color, numpy.float32)
                    bufTex.write(numpy.around(c * 255.0).astype(numpy.uint8))
                    for i, uv in enumerate([tex.data[loop.index].uv for tex in obj.data.uv_layers]):
                        bufTex.write(numpy.fromiter([uv[0], 1 - uv[1]], text_fns[i]))

                    g = obj.data.vertices[loop.vertex_index].groups
                    weight = [g[i].weight if i < len(g) else .0 for i in range(4)]
                    index = [g[i].group if i < len(g) else 0 for i in range(4)]
                    bufBlend.write(numpy.fromiter(weight, numpy.float32))
                    bufBlend.write(numpy.fromiter(index, numpy.int32))

                offset += idx + 1
                log(f"drawindexed = {idx}")