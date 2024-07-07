import bpy, numpy, os
from glob import glob

def import_collected_furniture(path:str):
    vb_file, ib_file = glob(f"{path}/*-b0pos*.buf")[0], glob(f"{path}/*-b2ib*.buf")[0]
    with open(vb_file, "rb") as pos, open(ib_file, "rb") as ib:
        vertex_data = {"positions": [], "normals": [], "colors": [], "uv": []}
        for i in range(os.path.getsize(vb_file) // 10):
            [px, py, pz, _] = numpy.frombuffer(pos.read(8), numpy.float16)
            [nx, ny, nz, _] = numpy.frombuffer(pos.read(4), numpy.int8) / 127.0
            [u, v] = numpy.frombuffer(pos.read(4), numpy.float16)
            pos.read(4)  # throw tangent info away
            vertex_data["positions"].append((-px, -pz, py))
            vertex_data["normals"].append((-nx, -nz, ny))
            vertex_data["uv"].append([u, 1 - v])

        contents = numpy.frombuffer(ib.read(), numpy.uint16)
        faces = [list(reversed(contents[i*3:i*3+3])) for i in range(len(contents)//3)]

        mesh = bpy.data.meshes.new("Furniture")
        obj = bpy.data.objects.new(mesh.name, mesh)
        mesh.from_pydata(vertex_data["positions"], [], faces)
        bpy.context.scene.collection.objects.link(obj)

        mesh.polygons.foreach_set("use_smooth", [True] * len(mesh.polygons))
        mesh.calc_normals_split()
        mesh.use_auto_smooth = True
        mesh.normals_split_custom_set_from_vertices(vertex_data["normals"])

        uv_layer = mesh.uv_layers.new(name=f"TEXCOORD.xy")
        for l in mesh.loops:
            uv_layer.data[l.index].uv = vertex_data["uv"][l.vertex_index]

        for diffuse in glob(f"{path}/*diffuse*.png"):
            mat = bpy.data.materials.new(name=f"LynMaterial")
            obj.data.materials.append(mat)
            mat.use_nodes = True
            bsdf = mat.node_tree.nodes["Principled BSDF"]
            tex_image = mat.node_tree.nodes.new('ShaderNodeTexImage')
            tex_image.image = bpy.data.images.load(diffuse)
            mat.node_tree.links.new(bsdf.inputs['Base Color'], tex_image.outputs['Color'])
