import os, shutil, time
from glob import glob

def prop(file:str, key:str): idx = file.index(key) + len(key) + 1; return file[idx:idx+8]

def collect(name:str, vb:str, out_dir="collected"):
    in_dir = glob("FrameAnalysis*")[-1]
    print(f"From folder: {in_dir} to folder {out_dir}...")
    pos_file = glob(f"{in_dir}/*-vb0={vb}*.buf")[0]
    draw_id = os.path.split(pos_file)[-1][:6]
    ib_file = glob(f"{in_dir}/{draw_id}-ib=*.buf")[0]

    tex_files = [f for f in glob(f"{in_dir}/{draw_id}-ps-t*") if "!" not in f]
    for tex in tex_files[:3]:
        shutil.copyfile(tex, f"{out_dir}/{name}-{tex[42:53]}.{tex[-3:]}")

    shutil.copyfile(pos_file, f"{out_dir}/{name}-b0pos={vb}.buf")
    shutil.copyfile(ib_file, f"{out_dir}/{name}-b2ib={prop(ib_file, 'ib')}.buf")


if __name__ == "__main__":
    start = time.time()

    os.chdir("C:/Users/cyrog/Documents/create/mod/zzz/3dmigoto_dev")
    # collect(path0, "HIABox", "d4c6ca97")
    collect("VideoArchiveSofa", "df7ddf5e")

    print(f"Operation completed in {int((time.time()-start)*1000)}ms")

import bpy, numpy

def import_collected_furniture(path:str, name:str="Furniture"):
    vb_file, ib_file = glob(f"{path}/{name}-b0pos*.buf")[0], glob(f"{path}/{name}-b2ib*.buf")[0]
    with open(vb_file, "rb") as pos, open(ib_file, "rb") as ib:
        positions, normals, colors, uvs = [], [], [], [[], [], []]
        for i in range(os.path.getsize(vb_file) // 24):
            [px, py, pz, _] = numpy.frombuffer(pos.read(8), numpy.float16)
            positions.append((-px, -pz, py))
            [nx, ny, nz, _] = numpy.frombuffer(pos.read(4), numpy.int8) / 127.0
            normals.append((-nx, -nz, ny))
            for uv in uvs:
                uv.append(numpy.frombuffer(pos.read(4), numpy.float16))

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