import bpy
import numpy as np

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

# https://github.com/Vectorized/Python-KD-Tree
class KDTree(object):
    def __init__(self, points, dim, dist_sq_func=None):
        if dist_sq_func is None:
            dist_sq_func = lambda a, b: sum((x - b[i]) ** 2 for i, x in enumerate(a))

        def make(points, i=0):
            if len(points) > 1:
                points.sort(key=lambda x: x[i])
                i = (i + 1) % dim
                m = len(points) >> 1
                return [make(points[:m], i), make(points[m + 1:], i),
                        points[m]]
            if len(points) == 1:
                return [None, None, points[0]]

        def add_point(node, point, i=0):
            if node is not None:
                dx = node[2][i] - point[i]
                for j, c in ((0, dx >= 0), (1, dx < 0)):
                    if c and node[j] is None:
                        node[j] = [None, None, point]
                    elif c:
                        add_point(node[j], point, (i + 1) % dim)

        import heapq
        def get_knn(node, point, k, return_dist_sq, heap, i=0, tiebreaker=1):
            if node is not None:
                dist_sq = dist_sq_func(point, node[2])
                dx = node[2][i] - point[i]
                if len(heap) < k:
                    heapq.heappush(heap, (-dist_sq, tiebreaker, node[2]))
                elif dist_sq < -heap[0][0]:
                    heapq.heappushpop(heap, (-dist_sq, tiebreaker, node[2]))
                i = (i + 1) % dim
                # Goes into the left branch, then the right branch if needed
                for b in (dx < 0, dx >= 0)[:1 + (dx * dx < -heap[0][0])]:
                    get_knn(node[b], point, k, return_dist_sq,
                            heap, i, (tiebreaker << 1) | b)
            if tiebreaker == 1:
                return [(-h[0], h[2]) if return_dist_sq else h[2]
                        for h in sorted(heap)][::-1]

        def walk(node):
            if node is not None:
                for j in 0, 1:
                    for x in walk(node[j]):
                        yield x
                yield node[2]

        self._add_point = add_point
        self._get_knn = get_knn
        self._root = make(points)
        self._walk = walk

    def __iter__(self):
        return self._walk(self._root)

    def add_point(self, point):
        if self._root is None:
            self._root = [None, None, point]
        else:
            self._add_point(self._root, point)

    def get_knn(self, point, k, return_dist_sq=True):
        return self._get_knn(self._root, point, k, return_dist_sq, [])

    def get_nearest(self, point, return_dist_sq=True):
        l = self._get_knn(self._root, point, 1, return_dist_sq, [])
        return l[0] if len(l) else None
