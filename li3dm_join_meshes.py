import bpy, bmesh

def log(data):
    for window in bpy.context.window_manager.windows:
        screen = window.screen
        for area in screen.areas:
            if area.type == 'CONSOLE':
                override = {'window': window, 'screen': screen, 'area': area}
                bpy.ops.console.scrollback_append(override, text=str(data), type="OUTPUT")

def join_meshes(objs):
    bm0 = bmesh.new()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    for obj in objs:
        for m in obj.modifiers:
            if m.type == "SOLIDIFY":
                m.show_viewport = False
        obj = bpy.context.scene.objects[obj.name]
        pivot_u = obj['pivot_u'] if 'pivot_u' in obj else 0
        pivot_v = obj['pivot_v'] if 'pivot_v' in obj else 0
        log(f"parsing {obj.name} (pivot_u={pivot_u},pivot_v={pivot_v},scale={obj['scale']}")
        bm = bmesh.new()
        bm.from_object(obj, depsgraph)
        bm.verts.ensure_lookup_table()
        # bm.faces.flatMap { it.loops }.map { it[bm.loops.layers.uv[0]] }
        for layer in [loop[bm.loops.layers.uv[0]] for face in bm.faces for loop in face.loops]:
            layer.uv = pivot_u + obj['scale'] * layer.uv[0], pivot_v + obj['scale'] * layer.uv[1]

        # bmesh doesn't have a "from_bmesh" method, so this ugly piece of code had to me written
        mesh = bpy.data.meshes.new('Temp')
        bm.to_mesh(mesh)
        bm0.from_mesh(mesh)
        bpy.data.meshes.remove(mesh)
        bm.free()

        for m in obj.modifiers:
            if m.type == "SOLIDIFY":
                m.show_viewport = True

    mesh0 = bpy.data.meshes.new('Test')
    bm0.to_mesh(mesh0)
    obj0 = bpy.data.objects.new('Test', mesh0)
    bpy.context.scene.collection.objects.link(obj0)
    bm0.free()

def doodoo():
    agh = { "Ayaka":[7,0], "Yoimiya":[6,0], "Shinobu":[5,0], "Kirara":[4,0], "Yae":[3,0], "Kokomi":[2,0], "Chiori":[1,0], "Raiden":[0,0], "Sara":[7,3] }
    ugh = { "Face":0, "Head":1, "Body":2 }
    for obj in [o for o in bpy.context.scene.objects if o.type == 'MESH' and o.visible_get() and not o.name.startswith("0")]:
        log(f"processing {obj.name}...")
        [char, part, *_] = obj.name.split("_")
        if part == "BodyN": obj["pivot_u"] = 0;obj["pivot_v"] = 0;obj["scale"] = .25; continue
        obj["pivot_u"] = (agh[char][0] + ugh[part]) * .125
        obj["pivot_v"] = agh[char][1] * .125
        obj["scale"] = .125

    bpy.context.scene.objects["0_Sneku"]["pivot_u"] = .75
    bpy.context.scene.objects["0_Sneku"]["pivot_v"] = .75
    bpy.context.scene.objects["0_Sneku"]["scale"] = .25

