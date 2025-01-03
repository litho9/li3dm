import os, shutil, time
from glob import glob

def prop(file:str, key:str): idx = file.index(key) + len(key) + 1; return file[idx:idx+8]
def collect(name:str, vb:str, in_dir=None, out_dir="collected"):
    in_dir = in_dir or glob("FrameAnalysis*")[-1]
    print(f"From folder: {in_dir} to folder {out_dir}...")
    pos_file = glob(f"{in_dir}/*-vb0={vb}*.buf")[0]
    draw_id = os.path.split(pos_file)[-1][:6]
    ib_file = glob(f"{in_dir}/{draw_id}-ib=*.buf")[0]

    tex_files = [f for f in glob(f"{in_dir}/{draw_id}-ps-t*") if "!" not in f]
    for tex in tex_files:
        shutil.copyfile(tex, f"{out_dir}/{name}-{tex[42:53]}.{tex[-3:]}")

    shutil.copyfile(pos_file, f"{out_dir}/{name}-b0pos={vb}.buf")
    shutil.copyfile(ib_file, f"{out_dir}/{name}-b2ib={prop(ib_file, 'ib')}.buf")


if __name__ == "__main__":
    start = time.time()

    os.chdir("C:/Users/urmom/Documents/create/mod/zzz/3dmigoto_dev")
    # collect(path0, "HIABox", "d4c6ca97")
    # collect("VideoArchiveSofa", "df7ddf5e")
    # collect("BellesRoomCouch", "dea91269")
    # collect("WengineNoviluna", "4dd63d3e", "FrameAnalysis-2024-09-21-141910")
    collect("RandomPlayCounter", "85b1774d", "FrameAnalysis-2024-11-04-150314")

    print(f"Operation completed in {int((time.time()-start)*1000)}ms")

import bpy, numpy as np

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
    mesh.normals_split_custom_set_from_vertices([inf(p[1] / 127.0) for p in vb])

    data = [vb[l.vertex_index] for l in mesh.loops]
    mesh.vertex_colors.new().data.foreach_set("color", [c for d in data for c in d[2] / 256])
    for i in range(3, len(vb[0])):
        mesh.uv_layers.new().data.foreach_set("uv", [c for d in data for c in d[i]])

    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.remove_doubles(threshold=.000001, use_sharp_edge_from_normals=True)
    bpy.ops.object.mode_set(mode='OBJECT')

def export_furniture(name:str, mesh, vb_fmt="4f2,4i1,4u1,2f2"):
    index_buffer, loop_buffer, index_map, idx = [], [], {}, 0
    for loop in [mesh.loops[i+2-i%3*2] for i in range(len(mesh.loops))]:
        h = (loop.vertex_index, *mesh.uv_layers[0].data[loop.index].uv, *loop.normal)
        if h not in index_map:
            index_map[h] = idx; idx += 1
            loop_buffer.append((loop, mesh.vertices[loop.vertex_index]))
        index_buffer.append(index_map[h])

    np.fromiter(index_buffer, np.uint16).tofile(f"{name}-ib.buf")

    def inb(vv, q): return -vv[0], vv[2], -vv[1], q
    mesh.calc_tangents()
    a = [(inb(v.co, 1.), inb(l.normal * 128.0, 0), inb(l.tangent * 256.0, -l.bitangent_sign),
          *[tex.data[l.index].uv for tex in mesh.uv_layers]) for l, v in loop_buffer]
    np.fromiter(a, np.dtype(vb_fmt)).tofile(f"{name}-vb0.buf")

#os.chdir(r"C:\mod\zzmi\FrameAnalysis-2024-12-29-210904")
#import_collected_furniture("StandNoviluna", "e478f8f0", "4f2,4i1,4u1,2f2")

os.chdir(r"C:\mod\zzmi\Mods\StandNoviluna")
mesh0 = bpy.context.selected_objects[0].data
export_furniture("StandNoviluna", mesh0, "4f2,4i1,4u1,2f2")