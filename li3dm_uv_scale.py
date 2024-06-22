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