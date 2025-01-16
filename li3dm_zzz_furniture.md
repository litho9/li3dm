ZZZ Object Import/Export

Export

For objects, different from characters, there's only one vertex-buffer (only vb0 and no vb1 and vb2).

The vertex-buffer holds loop (a.k.a. face corner) coordinates, split normals, tangents, and uv data.

"Wait, if it is a loop buffer, why is it called 'vertex-buffer'?"
Dunno, people like giving bad names for things.

The whole thing is like 15 lines, but there's a lot of stuff in each of them.

```py
import bpy, os, numpy
```

`bpy` is how python communicates with blender.
`os` is how python communicates with the Operational System.
`numpy` is the soul of this method of importing data. It's a very fast way of dealing with binary stuff and parallel execution.

```py
def export_furniture(name:str, mesh, vb_fmt="4f2,4i1,4i1,2f2"):
```

Our function call. The `vb_fmt` is the format for each loop stored in the vb0. By default, it is:
`4f2` (four 2-byte floats, three for coordinates x, y, z, and one that's always 1.0 (no idea what it represents))
`4i1` (four 1-byte signed integers, three for split normals x, y, z, and one that's always 0)
`4i1` (four 1-byte signed integers, three for tangents x, y, z, and one for the bitangent sign, that's always 1.0 or -1.0)
`2f2` (two 2-byte floats, representing the x and y of a texture map)

the `vb_fmt` is defined as a parameter with a default value because **it can be different**. I've seen objects with an extra texture map, and in that case the param needs another `2f2` at the end.

```py 
def inb(vv, q): return -vv[0], vv[2], -vv[1], q
```
The rotate/invert function. It rotates your object so it appear the same in-game as it appear in blender. Most importantly, it flips the x-axis, one of the main reasons I wrote this script myself. The `q` parameter is passed to the end of the returned tuple, as a handy way to deal with the fixed values for coordinates, split normals and the bitangent sign.

```py
ib, vb0, index_map, idx = [], [], {}, 0
```

initializes the two buffers and the variables used for the "loop cache". This is a good time to explain how the index buffer and the vertex buffer work together.

Programmers could just store the data for each loop in a sequence and that'd be enough to reconstruct the object in-game, but that would result in **a lot of repeated data**. You see, it is very common for face-corners to have the same position, the same split-normals, and the same texture coordinates. It is the case for every time a face meets another in a smooth surface.

TODO images

To tackle that, the vertex buffer only stores non-repeated data, and the index buffer maps the sequence of loops to the correspondent data stored in the vertex buffer.
Example: the first three loops form the first triangle of the 3d object. Their data are stored in the vb, and in the ib we store "first block of data, second block of data, third block of data". For the second triangle, we also have three loops, but two of the corners are the same as two from the first triangle. In this case, we can store only the data for the different loop in the vb, and in the ib we store "first block of data, second block of data, fourth block of data".

TODO awesome image

The `index_map` then stores the index for each data combination, mapping to the position it's position on the vb. The `idx` stores the next index (it's always equal to the current length of the vb).

```py
for l in [mesh.loops[i+2-i%3*2] for i in range(len(mesh.loops))]:
```

This line iterates the loops. Instead of just being `for l in mesh.loops` we have to do a little trick here. You see, if we just iterated the loops in order, we would end up with our whole model with **flipped normals**.
