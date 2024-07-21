import bpy, bmesh

def log(data):
    for window in bpy.context.window_manager.windows:
        screen = window.screen
        for area in screen.areas:
            if area.type == 'CONSOLE':
                override = {'window': window, 'screen': screen, 'area': area}
                bpy.ops.console.scrollback_append(override, text=str(data), type="OUTPUT")

objs = [o for o in bpy.context.scene.objects if o.type == 'MESH' and o.visible_get()]

def doodoo2():
    agh = { "Collei":[3,5], "Faruzan":[3,4], "Candace":[3,3], "Dehya":[3,2], "Layla":[3,1], "Nilou":[3,0] }
    ugh = { "Face":0, "Head":1, "Body":2 }
    for obj in [o for o in objs if not o.name.startswith("Couch")]:
        log(f"processing {obj.name}...")
        [char, part, *egh] = obj.name.split("_")
        if part == "BodyN": obj["pivot_u"] = .75; obj["pivot_v"] = .5; obj["scale"] = .25; continue
        obj["pivot_u"] = (agh[char][0] + ugh[part]) * .125
        obj["pivot_v"] = agh[char][1] * .125
        obj["scale"] = .125
    bpy.context.scene.objects["CouchFinnick"]["pivot_u"] = .75
    bpy.context.scene.objects["CouchFinnick"]["pivot_v"] = .75
    bpy.context.scene.objects["CouchFinnick"]["scale"] = .25
#doodoo2()

def join_meshes(objs):
    bm0 = bmesh.new()
    depsgraph = bpy.context.evaluated_depsgraph_get()
    for obj in objs:
        pivot_u = obj['pivot_u']
        pivot_v = obj['pivot_v']
        #        log(f"parsing {obj.name} (pivot_u={pivot_u},pivot_v={pivot_v},scale={obj['scale']}")
        bm = bmesh.new()
        bm.from_object(obj, depsgraph)
        bm.transform(obj.matrix_world)
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

    mesh0 = bpy.data.meshes.new('CouchFinnickSumeru')
    bm0.to_mesh(mesh0)
    obj0 = bpy.data.objects.new('CouchFinnickSumeru', mesh0)
    bpy.context.scene.collection.objects.link(obj0)
    bm0.free()
# join_meshes(objs)

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

