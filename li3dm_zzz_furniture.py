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

import bpy, numpy

f16 = lambda buf: numpy.frombuffer(buf.read(4), numpy.float16)
f32 = lambda buf: numpy.frombuffer(buf.read(8), numpy.float32)
f64 = lambda buf: numpy.frombuffer(buf.read(16), numpy.float64)

def import_collected_furniture(path:str, name:str="Furniture", tex_fns=(f32,f32,f16)):
    vb_file, ib_file = glob(f"{path}/{name}-b0pos*.buf")[0], glob(f"{path}/{name}-b2ib*.buf")[0]
    with open(vb_file, "rb") as pos, open(ib_file, "rb") as ib:
        positions, normals, colors = [], [], []
        uvs = [[] for _ in range(len(tex_fns))]
        for i in range(os.path.getsize(vb_file) // 28):
            [px, py, pz, _] = numpy.frombuffer(pos.read(8), numpy.float16)
            positions.append((-px, -pz, py))
            [nx, ny, nz, _] = numpy.frombuffer(pos.read(4), numpy.int8) / 127.0
            normals.append((-nx, -nz, ny))
            # for uv in uvs:
            #     uv.append(numpy.frombuffer(pos.read(4), numpy.float16))
            for j, tex_fn in enumerate(tex_fns):
                uvs[j].append(tex_fn(pos))

        contents = numpy.frombuffer(ib.read(), numpy.uint16)
        faces = [list(reversed(contents[i*3:i*3+3])) for i in range(len(contents)//3)]

        mesh = bpy.data.meshes.new(name)
        obj = bpy.data.objects.new(mesh.name, mesh)
        mesh.from_pydata(positions, [], faces)
        bpy.context.scene.collection.objects.link(obj)

        mesh.polygons.foreach_set("use_smooth", [True] * len(mesh.polygons))
        mesh.calc_normals_split()
        mesh.use_auto_smooth = True
        mesh.normals_split_custom_set_from_vertices(normals)

        for i, uv in enumerate(uvs):
            uv_layer = mesh.uv_layers.new(name=f"TEXCOORD{i}.xy")
            for l in mesh.loops:
                uv_layer.data[l.index].uv = uv[l.vertex_index]

        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.mode_set(mode='EDIT')
        bpy.ops.mesh.select_all(action='SELECT')
        bpy.ops.mesh.remove_doubles(threshold=.000001, use_sharp_edge_from_normals=True)
        bpy.ops.object.mode_set(mode='OBJECT')

        for diffuse in glob(f"{path}/*t1*.jpg"):
            mat = bpy.data.materials.new(name=f"LynMaterial")
            obj.data.materials.append(mat)
            mat.use_nodes = True
            bsdf = mat.node_tree.nodes["Principled BSDF"]
            tex_image = mat.node_tree.nodes.new('ShaderNodeTexImage')
            tex_image.image = bpy.data.images.load(diffuse)
            mat.node_tree.links.new(bsdf.inputs['Base Color'], tex_image.outputs['Color'])

def export_furniture(name:str):
    with (open(f"{name}.buf", "wb") as buf,
          open(f"{name}.ib", "wb") as ib):
        obj = bpy.context.selected_objects[0].data
        obj.calc_tangents()
        index_map = {}
        idx = 0
        for loop in obj.loops:
            co = obj.vertices[loop.vertex_index].co
            [u, v] = obj.uv_layers[1].data[loop.index].uv
            nor = numpy.fromiter(loop.normal, numpy.float32)
            tan = numpy.fromiter(loop.tangent, numpy.float32)

            h = (loop.vertex_index, u, v, nor[0], nor[1], nor[2])
            if h in index_map:
                ib.write(numpy.uint32(index_map[h]))
                continue
            index_map[h] = idx
            ib.write(numpy.uint32(idx))  # ib.write(numpy.uint32(index_map[h]))
            idx += 1

            pos = [-co.x, co.z, -co.y]
            buf.write(numpy.fromiter(pos, numpy.float16))
            buf.write(b'\x00\x3c')
            buf.write((nor * 128.0).astype(numpy.int8))
            buf.write(b'\x00')
            buf.write((tan * 128.0).astype(numpy.int8))
            buf.write(b'\x81' if loop.bitangent_sign > 0 else b'\x7f')
            [u0, v0] = obj.uv_layers[0].data[loop.index].uv
            buf.write(numpy.fromiter([u0, v0], numpy.float16))
            buf.write(numpy.fromiter([u, v], numpy.float16))