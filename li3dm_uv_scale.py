import bpy

for data in bpy.data.objects["z"].data.uv_layers["TEXCOORD.xy"].data:
    data.uv = .5 + .25 * data.uv[0], .75 + .25 * data.uv[1]


# import bpy
# from mathutils import Vector
#
# # Scale a 2D vector v, considering a scale s and a pivot point p 0,671875
# def Scale2D(v, s, p):
#     return p[0] + s[0] * v[0], p[1] + s[1] * v[1]
#
# bpy.ops.object.mode_set(mode='OBJECT')  # UV data is not accessible in edit mode
# pivot = Vector((0.5, 0.75))
# scale = Vector((0.25, 0.25))
#
# objName = "z"
# obj = bpy.data.objects[objName]
# uvMap = obj.data.uv_layers["TEXCOORD.xy"]
# for uvIndex in range(len(uvMap.data)):
#     uvMap.data[uvIndex].uv = Scale2D(uvMap.data[uvIndex].uv, scale, pivot)

bm0 = bmesh.new()
depsgraph = bpy.context.evaluated_depsgraph_get()
for name in ["AyakaDress-vb0=0107925f.txt","AyakaBody-vb0=0107925f.txt","AyakaHead-vb0=0107925f.txt"]:
    obj = bpy.context.scene.objects[name]
    bm = bmesh.new()
    bm.from_object(obj, depsgraph)
    bm.verts.ensure_lookup_table()
    #    uv = bm.loops.layers.uv.active
    uv_layer = bm.loops.layers.uv.new()
    for face in bm.faces:
        for loop in face.loops:
            [u, v] = obj.data.uv_layers[0].data[loop.index].uv
            loop[uv_layer].uv = (getattr(obj, 'pivot_u', 0) + obj['scale'] * u,
                                 getattr(obj, 'pivot_v', 0) + obj['scale'] * v)
                                 #    for data in uv_layer:
                                 #        data.uv = (obj['pivot_u'] + (obj['scale'] or 0) * data.uv[0],
                                 #                   obj['pivot_v'] + (obj['scale'] or 0) * data.uv[1])
                                 bm0.from_mesh(bm)


mesh = bpy.data.meshes.new('Test')
bm0.to_mesh(mesh)
mesh.update()
bm0.free()