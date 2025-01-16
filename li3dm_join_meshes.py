import bpy, bmesh, numpy as np

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
        [char, part, *_egh] = obj.name.split("_")
        if part == "BodyN": obj["pivot_u"] = .75; obj["pivot_v"] = .5; obj["scale"] = .25; continue
        obj["pivot_u"] = (agh[char][0] + ugh[part]) * .125
        obj["pivot_v"] = agh[char][1] * .125
        obj["scale"] = .125
    bpy.context.scene.objects["CouchFinnick"]["pivot_u"] = .75
    bpy.context.scene.objects["CouchFinnick"]["pivot_v"] = .75
    bpy.context.scene.objects["CouchFinnick"]["scale"] = .25
#doodoo2()

def join_meshes(name:str, names, objs, scale=1/4, vb_fmt="4f2,4i1,4i1,2f2"):
    deps = bpy.context.evaluated_depsgraph_get()
    def inb(vv, q): return -vv[0], vv[2], -vv[1], q
    ib, vb0, index_map, idx = [], [], {}, 0
    for obj in objs:
        for mod in [m for m in obj.modifiers if m.type == 'SOLIDIFY' or m.type == 'NODES']:
            mod.show_viewport = False
        [char, part_str, *_] = obj.name.split("_")
        pivot = np.fromiter((int(part_str), names.index(char)), np.float32)
        print(f"parsing {obj.name} (pivot={pivot},scale={scale})")
        bm = bmesh.new()
        bm.from_object(obj, deps)
        bm.transform(obj.matrix_world)
        bmesh.ops.triangulate(bm, faces=bm.faces[:])
        for loop in [l for face in bm.faces for l in reversed(face.loops)]:
            uv, nor = loop[bm.loops.layers.uv[0]].uv, loop.calc_normal()
            h = (loop.vert.index, *uv, *nor)
            if h not in index_map:
                index_map[h] = idx; idx += 1
                vb0.append((inb(loop.vert.co, 1.), inb(nor * 127., 0),
                        inb(loop.calc_tangent() * 127., 127), (pivot + uv) * scale))
            ib.append(index_map[h])
        bm.free()

    np.fromiter(ib, np.uint16).tofile(f"{name}-ib.buf")
    np.fromiter(vb0, np.dtype(vb_fmt)).tofile(f"{name}-vb0.buf")
# join_meshes("Furnitest", ["", "苍角", "Yanagi", "Unagi"], objs, vb_fmt="4f2,4i1,4i1,2f2,2f2")

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

