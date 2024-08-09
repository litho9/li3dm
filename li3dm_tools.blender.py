import io
import re
from array import array
import struct
import numpy
import itertools
import collections
import os, time
from glob import glob
import json
import textwrap
import shutil
import logging
import sys
from glob import glob

# import vendor.bpy as bpy
# from vendor.bpy_extras.io_utils import unpack_list, ImportHelper, ExportHelper, axis_conversion, orientation_helper
# from vendor.bpy.props import BoolProperty, StringProperty, CollectionProperty
# from vendor.mathutils import Matrix, Vector
import bpy
from bpy_extras.io_utils import unpack_list, ImportHelper, ExportHelper, axis_conversion
from bpy.props import BoolProperty, StringProperty, CollectionProperty
from bpy_extras.image_utils import load_image
from mathutils import Matrix, Vector

bl_info = {
    "name": "Li3DM",
    "blender": (3, 6, 0),
    "author": "Lioh",
    "location": "File > Import-Export",
    "description": "Refactor of 3DMigoto's addon",
    "category": "Import-Export",
    "tracker_url": "https://github.com/SilentNightSound/GI-Model-Importer",
}

# logger = logging.getLogger(__name__)
# logger.setLevel(logging.DEBUG)
# logger.addHandler(logging.StreamHandler())

IOOBJOrientationHelper = type('DummyIOOBJOrientationHelper', (object,), {})

class Fatal(Exception): pass

def log(data):
    for window in bpy.context.window_manager.windows:
        screen = window.screen
        for area in screen.areas:
            if area.type == 'CONSOLE':
                override = {'window': window, 'screen': screen, 'area': area}
                bpy.ops.console.scrollback_append(override, text=str(data), type="OUTPUT")

# https://theduckcow.com/2019/update-addons-both-blender-28-and-27-support/
def make_annotations(cls):
    bl_props = {k: v for k, v in cls.__dict__.items() if isinstance(v, tuple)}
    if bl_props:
        if '__annotations__' not in cls.__dict__:
            setattr(cls, '__annotations__', {})
        annotations = cls.__dict__['__annotations__']
        for k, v in bl_props.items():
            annotations[k] = v
            delattr(cls, k)
    return cls


def import_mesh_from_frame_analysis(name, ib, vb, diffuse):
    next(ib)  # byte offset
    first_index = int(next(ib)[13:-1])  # len["first index: "]
    for i in range(4):  next(ib)  # index count, topology, format, ""
    faces = [list(map(int, line.split())) for line in ib]

    mesh = bpy.data.meshes.new(f"{first_index}-{name}")
    obj = bpy.data.objects.new(mesh.name, mesh)
    obj['3DMigoto:IBFormat'] = "DXGI_FORMAT_R32_UINT"
    obj['3DMigoto:FirstIndex'] = first_index

    vb_elem_pattern = re.compile(r'''vb\d+\[\d*]\+\d+ (?P<semantic>[^:]+): (?P<data>.*)$''')
    pos, weights, indices, colors, normals, tex = [], [], [], [], [], [[], []]
    layout = {}
    for line in vb:
        if line.startswith('stride:'):
            obj['3DMigoto:VBStride'] = int(line[8:-1])
        elif line.startswith('first vertex:'):
            obj['3DMigoto:FirstVertex'] = int(line[14:-1])
        elif line.startswith("element["):
            ln = next(vb)[16:-1]  # [len("  SemanticName: "):]
            layout[ln] = {}
            layout[ln]['index'] = int(next(vb)[17:-1])  # [len("  SemanticIndex: "):]
            layout[ln]['format'] = next(vb)[10:-1]  # [len("  Format: "):]
            layout[ln]['slot'] = int(next(vb)[13:-1])  # [len("  InputSlot: "):]
            layout[ln]['offset'] = int(next(vb)[21:-1])  # [len("  AlignedByteOffset: "):]
            next(vb)  # InputSlotClass: per-vertex
            next(vb)  # InstanceDataStepRate: 0
        elif line.startswith("vb0["):
            match = vb_elem_pattern.match(line)
            semantic = match.group('semantic')
            if semantic == 'POSITION':
                [x, y, z] = match.group('data').split(", ")
                pos.append((-float(x), -float(z), float(y)))
            elif semantic == 'NORMAL':
                [x, y, z] = match.group('data').split(", ")
                normals.append((float(x), float(z), -float(y)))
            elif semantic == 'BLENDWEIGHT':
                weights.append(list(map(float, match.group('data').split(", "))))
            elif semantic == 'BLENDINDICES':
                indices.append(list(map(int, match.group('data').split(", "))))
            elif semantic.startswith('TEXCOORD'):
                idx = 0 if semantic == 'TEXCOORD' else int(semantic[8:])
                [x, y] = match.group('data').split(", ")
                tex[idx].append((float(x), 1-float(y)))

    obj['3DMigoto:VBLayout'] = json.dumps(layout)  # Attach the vertex buffer layout to the object for later exporting.
    mesh.from_pydata(pos, [], faces)
    if len(weights):
        group_count = max(itertools.chain(*(tuple(idx for idx in indices))))
        for i in range(group_count + 1):
            obj.vertex_groups.new(name=str(i))
        for vid in range(len(weights)):
            for i, w in zip(indices[vid], weights[vid]):
                if w != 0.0:
                    obj.vertex_groups[i].add((vid,), w, 'REPLACE')
    if 'COLOR' in layout and layout['COLOR']['offset'] > 0:
        vertex_color = mesh.vertex_colors.new(name='COLOR')
        for i, c in enumerate(colors):
            vertex_color.data[i].color = c
    for i in range(len([x for x in tex if len(x)])):
        uv_layer = mesh.uv_layers.new(name=f"TEXCOORD{i}")
        for l in mesh.loops:
            uv_layer.data[l.index].uv = tex[i][l.vertex_index]
    mesh.use_auto_smooth = True
    mesh.normals_split_custom_set_from_vertices(normals)

    # add image texture (if .png exists)
    if diffuse:
        mat = bpy.data.materials.new(name=f"{name}Material")
        obj.data.materials.append(mat)
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes["Principled BSDF"]
        tex_image = mat.node_tree.nodes.new('ShaderNodeTexImage')
        tex_image.image = bpy.data.images.load(diffuse)
        mat.node_tree.links.new(bsdf.inputs['Base Color'], tex_image.outputs['Color'])

    return obj

f16 = lambda buf: numpy.frombuffer(buf.read(2), numpy.float16)
f32 = lambda buf: numpy.frombuffer(buf.read(4), numpy.float32)
f64 = lambda buf: numpy.frombuffer(buf.read(8), numpy.float64)

def import_collected_zzz(path:str, name:str, tex_fns=(f16,f32,f16)):
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

        [r, g, b, a] = numpy.frombuffer(tex.read(4), numpy.uint8)
        colors.append((r, g, b, a))
        for j, tex_fn in enumerate(tex_fns):
            uvs[j].append([tex_fn(tex), 1 - tex_fn(tex)])

        weights.append(numpy.frombuffer(blend.read(16), numpy.float32))
        indices.append(numpy.frombuffer(blend.read(16), numpy.int32))

    ib_section = numpy.frombuffer(bytearray(ib.read()), numpy.uint16)
    faces = [list(reversed(ib_section[i*3:i*3+3])) for i in range(len(ib_section)//3)]

    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    mesh.from_pydata(positions, [], faces)
    bpy.context.scene.collection.objects.link(obj)
    mesh.use_auto_smooth = True
    mesh.normals_split_custom_set_from_vertices(normals)

    color_layer = mesh.vertex_colors.new(name='Color')
    for l in mesh.loops:
        color_layer.data[l.index].color = colors[l.vertex_index]
    for i, uv in enumerate(uvs):
        uv_layer = mesh.uv_layers.new(name=f"TEXCOORD{i}")
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
    bpy.ops.mesh.remove_doubles(threshold=.000001)
    bpy.ops.object.mode_set(mode='OBJECT')

    for diffuse in glob(f"{path}/{name}*.png"):
        mat = bpy.data.materials.new(name=f"LynMaterial")
        obj.data.materials.append(mat)
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes["Principled BSDF"]
        tex_image = mat.node_tree.nodes.new('ShaderNodeTexImage')
        tex_image.image = bpy.data.images.load(diffuse)
        mat.node_tree.links.new(bsdf.inputs['Base Color'], tex_image.outputs['Color'])


def import_collected(path:str, name:str):
    files = glob(f"{path}/{name}-b*.buf")
    pos, tex, ib, blend = [open(f, "rb") for f in files]
    vertex_count = os.path.getsize(os.path.join(path, files[0])) // 40
    tex_stride = os.path.getsize(os.path.join(path, files[1])) // vertex_count  # either 12 or 20
    vertex_data = {"positions": [], "normals": [], "colors": [], "indices": [], "weights": [],
                   "uvs": [[] for _ in range((tex_stride - 4) // 8)]}
    for i in range(vertex_count):
        [px, py, pz, nx, ny, nz] = [f32(pos) for _ in range(6)]
        vertex_data["positions"].append((-px, -pz, py))
        vertex_data["normals"].append((-nx, -nz, ny))
        pos.read(16)  # throw tangent info away, it will be recalculated on export

        [r, g, b, a] = numpy.frombuffer(tex.read(4), numpy.uint8)
        vertex_data["colors"].append((r, g, b, a))
        for uv in vertex_data["uvs"]:
            uv.append([f32(tex), 1 - f32(tex)])

        vertex_data["weights"].append(numpy.frombuffer(blend.read(16), numpy.float32))
        vertex_data["indices"].append(numpy.frombuffer(blend.read(16), numpy.int32))

    ib_indexes = list(map(int, files[2].split("=")[2].split(".")[0].split("_"))) + [sys.maxsize]
    contents = numpy.frombuffer(bytearray(ib.read()), numpy.uint16)
    for idx in range(len(ib_indexes) - 1):
        ib_section = contents[ib_indexes[idx]:ib_indexes[idx+1]]
        faces = [list(reversed(ib_section[i*3:i*3+3])) for i in range(len(ib_section)//3)]

        mesh = bpy.data.meshes.new(name)
        obj = bpy.data.objects.new(name, mesh)
        mesh.from_pydata(vertex_data["positions"], [], faces)
        bpy.context.scene.collection.objects.link(obj)

        mesh.polygons.foreach_set("use_smooth", [True] * len(mesh.polygons))
        mesh.calc_normals_split()
        mesh.use_auto_smooth = True
        mesh.normals_split_custom_set_from_vertices(vertex_data["normals"])

        color_layer = mesh.vertex_colors.new(name='Color')
        for l in mesh.loops:
            color_layer.data[l.index].color = vertex_data["colors"][l.vertex_index]
        for i, uv in enumerate(vertex_data["uvs"]):
            uv_layer = mesh.uv_layers.new(name=f"TEXCOORD{i}")
            for l in mesh.loops:
                uv_layer.data[l.index].uv = uv[l.vertex_index]

        if len(vertex_data["indices"]):
            for i in range(max(itertools.chain(*vertex_data["indices"])) + 1):
                obj.vertex_groups.new(name=str(i))
            # for v, i, w in [(v, i, w) for v, [i0, w0] in enumerate(zip(indices, weights)) for i, w in zip(i0, w0) if i != 0]:
            for vid in range(len(vertex_data["weights"])):
                for w, i in zip(vertex_data["weights"][vid], vertex_data["indices"][vid]):
                    if w != 0:
                        obj.vertex_groups[i].add((vid,), w, 'REPLACE')

        for diffuse in [f for f in os.listdir(path) if str(ib_indexes[idx]) in f and f.endswith("png")]:
            mat = bpy.data.materials.new(name=f"LynMaterial")
            obj.data.materials.append(mat)
            mat.use_nodes = True
            bsdf = mat.node_tree.nodes["Principled BSDF"]
            tex_image = mat.node_tree.nodes.new('ShaderNodeTexImage')
            tex_image.image = bpy.data.images.load(os.path.join(path, diffuse))
            mat.node_tree.links.new(bsdf.inputs['Base Color'], tex_image.outputs['Color'])


class ImportFrameAnalysis(bpy.types.Operator, ImportHelper, IOOBJOrientationHelper):
    bl_idname = "import_meshes.frame_analysis"
    bl_label = "Import Frame Analysis Dump"
    bl_options = {'PRESET', 'UNDO'}

    filename_ext = '.txt'
    filter_glob: StringProperty(default='*.txt', options={'HIDDEN'},)
    files: CollectionProperty(name="File Path", type=bpy.types.OperatorFileListElement,)

    def execute(self, context):
        try:
            start = time.time()
            dir_name = os.path.dirname(self.filepath)
            folder_name = os.path.basename(dir_name)
            collection = bpy.data.collections.new(folder_name)
            bpy.context.scene.collection.children.link(collection)
            for ib_file in [f for f in self.files if "-ib=" in f.name]:
                self.report({'INFO'}, f"importing {ib_file.name}... ")
                name = ib_file.name.split("-")[0]
                vb_file = [f for f in self.files if "-vb0=" in f.name and f.name.startswith(name)][0]
                ib = open(os.path.join(dir_name, ib_file.name), 'r')
                vb = open(os.path.join(dir_name, vb_file.name), 'r')
                diffuse = os.path.join(dir_name, f"{name}Diffuse.png")
                obj = import_mesh_from_frame_analysis(name.replace(folder_name, ""), ib, vb, diffuse)
                bpy.data.collections[folder_name].objects.link(obj)
                obj.select_set(True)
                context.view_layer.objects.active = obj

                # delete loose vertices, not indexed in the .ib
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.select_all(action='SELECT')
                bpy.ops.mesh.delete_loose(use_verts=True)
                bpy.ops.object.mode_set(mode='OBJECT')
            self.report({'INFO'}, f"operation completed in {int((time.time() - start)*1000)}ms")
        except Fatal as e:
            self.report({'ERROR'}, str(e))
        return {'FINISHED'}


def export(path, name):
    with open(os.path.join(path, f"{name}Position.li.buf"), "wb") as bufPos, \
            open(os.path.join(path, f"{name}Blend.li.buf"), "wb") as bufBlend, \
            open(os.path.join(path, f"{name}Texcoord.li.buf"), "wb") as bufTex:
        offset = 0
        for obj in sorted(bpy.context.selected_objects, key=lambda x: x.name):  # list selected objects by index
            log(f"processing object {obj.name}. there are {len(obj.data.loops)} loops...")
            obj.data.calc_tangents()
            color = obj.data.vertex_colors["COLOR"].data
            ib = open(os.path.join(path, f"{name}-{obj.name.split('.')[0]}.li.ib"), "wb")
            max_loop = -1
            for loop in obj.data.loops:
                ib.write(numpy.uint32(loop.vertex_index + offset))

                if max_loop >= loop.vertex_index: continue
                if max_loop + 1 != loop.vertex_index:
                    log(f"jumping from index {max_loop} to {loop.vertex_index}")
                max_loop = loop.vertex_index

                co = obj.data.vertices[loop.vertex_index].co
                arr = [-co.x, co.z, -co.y]
                arr += [loop.normal[0], -loop.normal[2], loop.normal[1]]
                arr += [-loop.tangent[2], -loop.tangent[0], loop.tangent[1], loop.bitangent_sign]
                bufPos.write(numpy.fromiter(arr, numpy.float32))  # 32 bits each

                c = numpy.fromiter(color[loop.vertex_index].color, numpy.float32) * 255.0
                bufTex.write(numpy.around(c).astype(numpy.uint8))
                for uv in [tex.data[loop.index].uv for tex in obj.data.uv_layers]:
                    bufTex.write(numpy.fromiter([uv[0], 1 - uv[1]], numpy.float32))

            for v in obj.data.vertices:
                g = v.groups
                weight = [g[i].weight if i < len(g) else .0 for i in range(4)]
                index = [g[i].group if i < len(g) else 0 for i in range(4)]
                bufBlend.write(numpy.fromiter(weight, numpy.float32))
                bufBlend.write(numpy.fromiter(index, numpy.int32))

            offset += max_loop + 1

# obj = bpy.context.selected_objects[0]
# log([g.name for g in obj.vertex_groups])

def export_furniture(name:str, invert=True):
    with (open(f"{name}.buf", "wb") as buf,
          open(f"{name}.ib", "wb") as ib):
        obj = bpy.context.selected_objects[0].data
        obj.calc_tangents()
        index_map = {}
        idx = 0
        for loop in obj.loops:
            co = obj.vertices[loop.vertex_index].co
            [u, v] = obj.uv_layers[0].data[loop.index].uv
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
            buf.write(numpy.fromiter([u, 1 - v], numpy.float16))
            buf.write(b'\x00\x00\x00\x00')
            buf.write((tan * 128.0).astype(numpy.int8))
            buf.write(b'\x81' if loop.bitangent_sign > 0 else b'\x7f')

def export_furniture_with_toggles(path:str, name:str, invert=True):
    offset, idx = 0, 0
    ini_consts, ini_keys, ini_draws = "", "", ""
    with (open(f"{path}/{name}.buf", "wb") as buf,
          open(f"{path}/{name}.ib", "wb") as ib):
        for obj in sorted(bpy.context.selected_objects, key=lambda x: x.name):
            log(f"processing object {obj.name}. there are {len(obj.data.vertices)} vertices and {len(obj.data.loops)} loops...")
            index_map = {}
            obj.data.calc_tangents()
            for loop in obj.data.loops:
                [u, v] = obj.data.uv_layers[0].data[loop.index].uv

                h = (loop.vertex_index, u, v)  # hash the vertex index and the UV coordinates
                if h in index_map:
                    ib.write(numpy.uint32(index_map[h]))
                    continue  # skip duplicates
                index_map[h] = idx
                ib.write(numpy.uint32(idx))  # same as ib.write(numpy.uint32(index_map[h]))
                idx += 1

                co = obj.data.vertices[loop.vertex_index].co
                pos = [co.x, co.y, -co.z if invert else co.z]  # 'invert' needs Mesh->Normals->Flip
                buf.write(numpy.fromiter(pos, numpy.float16))
                buf.write(b'\x00\x3c')

                nor = numpy.fromiter(loop.normal, numpy.float16)
                buf.write((nor * 128.0).astype(numpy.int8))
                buf.write(b'\x00')

                buf.write(numpy.fromiter([u, 1 - v], numpy.float16))
                buf.write(b'\x00\x00\x00\x00')

                tan = numpy.fromiter(loop.tangent, numpy.float16)
                buf.write((tan * 128.0).astype(numpy.int8))
                buf.write(b'\x81' if loop.bitangent_sign > 0 else b'\x7f')  # -1 or 1

            obj_name = obj.name.split('_')[1]  # remove the part used for sorting (Ex.: "01_Mona")
            if obj['key']:  # property "key" marks mesh as part of a toggle
                ini_consts += f"global persist ${obj_name} = 1\n"
                ini_keys += f"[KeySwap{obj_name}]\nkey = {obj['key']}\ntype = cycle\n${obj_name} = 0,1\n"
                ini_draws += f"if ${obj_name} == 1\n  drawindexed = {len(obj.data.loops)}, {offset}, 0\nendif\n"
            offset += len(obj.data.loops)

    with open(f"{path}/{name}.ini", "w") as ini:
        ini.write(f"; {name}\n\n")
        if ini_consts:
            ini.write(f"[Constants]\n{ini_consts}\n{ini_keys}\n\n")
        ini.write(f"[TextureOverrideVB]\nhash = 2554c4c5\nvb0 = ResourceVB\n\n")
        ini.write(f"[ResourceVB]\ntype = Buffer\nstride = 24\nfilename = {name}.buf\n\n")
        ini.write(f"[TextureOverrideIB0]\nhash = 5fc31415\nhandling = skip\n\n")
        ini.write(f"[TextureOverrideIB]\nhash = 5fc31415\nmatch_first_index = 0\nib = ResourceIB\n{ini_draws or 'drawindexed = auto'}\n\n")
        ini.write(f"[ResourceIB]\ntype = Buffer\nformat = DXGI_FORMAT_R32_UINT\nfilename = {name}.ib\n")


def menu_func_import_fa(self, context):
    self.layout.operator(ImportFrameAnalysis.bl_idname, text="li3dm dump (vb.txt + ib.txt)")

register_classes = (ImportFrameAnalysis,)

def register():
    for cls in register_classes:
        make_annotations(cls)
        bpy.utils.register_class(cls)

    bpy.types.TOPBAR_MT_file_import.append(menu_func_import_fa)

def unregister():
    for cls in reversed(register_classes):
        bpy.utils.unregister_class(cls)

    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import_fa)

if __name__ == "__main__":
    register()