import os, time
from glob import glob
from shutil import copyfile

def prop(file:str, key:str): idx = file.index(key) + len(key) + 1; return file[idx:idx+8]

def collect_zzz(path:str, name:str, vb:str, in_dir:str, out_dir = "collected"):
    os.chdir(path)
    in_dir = in_dir or glob("FrameAnalysis*")[-1]
    print(f"From folder: {in_dir} to folder {out_dir}...")

    vb0_files = glob(f"{in_dir}/*-vb0={vb}*.buf")
    posed_files = [f for f in vb0_files if int(os.path.split(f)[-1][:6]) > 10]  # draw ids <10 are point lists
    draw_id = [os.path.split(f)[-1][:6] for f in posed_files][0]
    tex_file = glob(f"{in_dir}/{draw_id}-vb1=*.buf")[0]
    ib_file = glob(f"{in_dir}/{draw_id}-ib=*.buf")[0]

    pos_file_size = os.path.getsize(posed_files[0])  # the matching pointlist has the same size
    vs = "e8425f64cfb887cd"  # always this value
    pointlist_vb0 = [f for f in glob(f"{in_dir}/*vb0*{vs}.buf") if os.path.getsize(f) == pos_file_size][0]
    blend_file = glob(f"{in_dir}/{os.path.split(pointlist_vb0)[-1][:6]}-vb2=*.buf")[0]

    for tex in [f for f in glob(f"{in_dir}/{draw_id}-ps-t*") if "!" not in f]:
        copyfile(tex, f"{out_dir}/{name}-{tex[42:53]}.{tex[-3:]}")
    copyfile(pointlist_vb0, f"{out_dir}/{name}-b0pos={prop(pointlist_vb0, 'vb0')}-draw={vb}.buf")
    copyfile(tex_file, f"{out_dir}/{name}-b1tex={prop(tex_file, 'vb1')}.buf")
    copyfile(ib_file, f"{out_dir}/{name}-b2ib={prop(ib_file, 'ib')}.buf")
    copyfile(blend_file, f"{out_dir}/{name}-b3blend={prop(blend_file, 'vb2')}.buf")

if __name__ == "__main__":
    start = time.time()
    path0 = "C:/Users/urmom/Documents/create/mod/zzz/3dmigoto_dev"

    # collect_zzz(path0, "SoukakuHair", "5432bbb8", "FrameAnalysis-2024-07-21-162646") # vertex_count=5924
    # collect_zzz(path0, "SoukakuBody", "ff00994d", "FrameAnalysis-2024-07-21-162646")
    collect_zzz(path0, "SoukakuFace", "d06e95fd", "FrameAnalysis-2024-07-21-162646") # vertex_count=2165

    print(f"Operation completed in {int((time.time()-start)*1000)}ms")

