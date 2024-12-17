import bpy

obj = bpy.context.selected_objects[0]
for v in obj.data.vertices:
    v.groups = sorted(v.groups, key=lambda x: x.weight)[:4]
# then normalize all
