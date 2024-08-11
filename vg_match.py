import bpy
import numpy as np
from pykdtree.kdtree import KDTree

def matcher(source_object, target_object):
    matrix_world = np.array(source_object.matrix_world)
    sorted_target_object = sorted(target_object.data.vertices, key=lambda x: x.index)
    src = np.array([matrix_world @ np.array([v.co.x, v.co.y, v.co.z, 1.0]) for v in source_object.data.vertices])[:, :3]
    dst = np.array([matrix_world @ np.array([v.co.x, v.co.y, v.co.z, 1.0]) for v in sorted_target_object])[:, :3]
    kd = KDTree(src).query(dst)[1]
    #    for vg in source_object.vertex_groups:
    #        target_object.vertex_groups.new(name=vg.name)
    for v, src_vertex_index in zip(sorted_target_object, kd):
        src_vertex = source_object.data.vertices[src_vertex_index]
        for vg in src_vertex.groups:
            #log(f"{src_vertex_index} {vg.group} {vg.weight}")
            target_object.vertex_groups[vg.group].add((v.index,), vg.weight, 'REPLACE')

def group_mast0(source_object, target_object):
    # eu me bmesho muito, eu me bmesho muito, eu me bmesho muito, bmesho... MUITO!
    matrix_world = np.array(target_object.matrix_world)
    target_centers = map(lambda group: np.array([matrix_world @ np.array([v.co.x, v.co.y, v.co.z, 1.0]) for v in target_object.data.vertices for vg in v.groups if group.index == vg.group]).mean(axis=0), target_object.vertex_groups)
    source_centers = map(lambda group: np.array([matrix_world @ np.array([v.co.x, v.co.y, v.co.z, 1.0]) for v in source_object.data.vertices for vg in v.groups if group.index == vg.group]), source_object.vertex_groups)
    source_centers = list(map(lambda y: tuple(y.mean(axis=0)), filter(lambda x: len(x), source_centers)))

    source_center_map = {}
    for c, g in zip(source_centers, source_object.vertex_groups):
        source_center_map[c] = g

    tree = KDTree(source_centers, 4)

    for center, group in zip(target_centers, target_object.vertex_groups):
        nearest_source_center = tree.get_nearest(center)[1]
        nearest_group = source_center_map[nearest_source_center]
        print(f"the sun shines upon the group '{group.name}'. It indicates it's real name: '{nearest_group.name}'")
