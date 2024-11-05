import os, shutil, time
from datetime import datetime
from glob import glob

def prop(file:str, key:str): idx = file.index(key) + len(key) + 1; return file[idx:idx+8]

def collect_furniture(path:str, name:str, vb:str):
    os.chdir(path)
    in_dir = glob("FrameAnalysis*")[-1]

    out_dir = name + "_" + datetime.today().strftime('%Y-%m-%d-%H%M%S')
    print(f"From folder: {in_dir} to folder {out_dir}...")
    pos_file = glob(f"{in_dir}/*-vb0={vb}*.buf")[0]
    draw_id = os.path.split(pos_file)[-1][:6]
    ib_file = glob(f"{in_dir}/{draw_id}-ib=*.buf")[0]
    os.mkdir(out_dir)

    tex_files = [f for f in glob(f"{in_dir}/{draw_id}-ps-t*") if "!" not in f]
    for tex in tex_files[:3]:
        shutil.copyfile(tex, f"{out_dir}/{name}-{tex[42:53]}.{tex[-3:]}")

    shutil.copyfile(pos_file, f"{out_dir}/{name}-b0pos={vb}.buf")
    shutil.copyfile(ib_file, f"{out_dir}/{name}-b2ib={prop(ib_file, 'ib')}.buf")


if __name__ == "__main__":
    start = time.time()

    path0 = "C:/Users/urmom/Documents/create/mod/zzz/3dmigoto_dev"
    collect_furniture(path0, "HIABox", "d4c6ca97")

    print(f"Operation completed in {int((time.time()-start)*1000)}ms")

