import bpy, bmesh

obj = bpy.context.edit_object
for e in bmesh.from_edit_mesh(obj.data).edges:
    if not e.smooth:
        e.select = True

bmesh.update_edit_mesh(obj.data, False)
