import bpy
import numpy as np
from pykdtree.kdtree import KDTree

def matcher(source_object, target_object):
    matrix_world = np.array(source_object.matrix_world)
    sorted_target_vertices = sorted(target_object.data.vertices, key=lambda x: x.index)
    src = np.array([matrix_world @ np.array([v.co.x, v.co.y, v.co.z, 1.0]) for v in source_object.data.vertices])[:, :3]
    dst = np.array([matrix_world @ np.array([v.co.x, v.co.y, v.co.z, 1.0]) for v in sorted_target_vertices])[:, :3]
    kd = KDTree(src).query(dst)[1]
    for vg in source_object.vertex_groups:
        target_object.vertex_groups.new(name=vg.name)
    for v, src_vertex_index in zip(sorted_target_vertices, kd):
        src_vertex = source_object.data.vertices[src_vertex_index]
        for vg in src_vertex.groups:
            #log(f"{src_vertex_index} {vg.group} {vg.weight}")
            target_object.vertex_groups[vg.group].add((v.index,), vg.weight, 'REPLACE')

def rename_group_to_nearest_bone(armature, tgt):
    src_centers = np.fromiter([(b.head + b.tail) / 2 for b in armature.pose.bones], "3f")
    tgt_centers = [np.array([v.co for v in tgt.data.vertices if g.index in [vg.group for vg in v.groups]]).mean(axis=0) for g in tgt.vertex_groups]
    kd = KDTree(src_centers).query(tgt_centers)[1]
    for i, idx in enumerate(kd):
        # print(f"the sun shines upon the group '{tgt.vertex_groups[i].name}'. It indicates it's real name: '{armature.pose.bones[idx].name}'")
        tgt.vertex_groups[i].name = armature.pose.bones[idx].name

len([np.array([v.co for v in tgt.data.vertices if g.index in [vg.group for vg in v.groups]]).mean(axis=0) for g in tgt.vertex_groups])