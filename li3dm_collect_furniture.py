import argparse, os, shutil, time
from datetime import datetime
from glob import glob
from pathlib import Path
try:
    from wand import image
except ImportError:
    image = None

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
    for i, tex in enumerate(tex_files[:3]):
        print(f"analysing {tex}")
        new_tex_file_name = f"{name}-{tex[42:53]}"
        shutil.copyfile(tex, f"{out_dir}/{new_tex_file_name}.{tex[-3:]}")
        if i == 3 and image:
            img = image.Image(filename=tex)
            img.alpha_channel = False
            img.save(filename=f"{out_dir}/{new_tex_file_name}.png")

    shutil.copyfile(pos_file, f"{out_dir}/{name}-b0pos={vb}.buf")
    shutil.copyfile(ib_file, f"{out_dir}/{name}-b2ib={prop(ib_file, 'ib')}.buf")


if __name__ == "__main__":
    start = time.time()

    # parser = argparse.ArgumentParser(description="Collects and renames data from 3dmigoto frame dumps")
    # parser.add_argument("-vb", type=str, help="Entity's draw VB hash (Ex.:329f5c91)")
    # parser.add_argument("-n", "--name", type=str, default="Collect", help="Output folder name")
    # parser.add_argument("-f", "--framedump", type=str, help="Name of framedump folder (if not specified, uses most recent)")
    # parser.add_argument("--png", action=argparse.BooleanOptionalAction, help="Convert .dds files to .png (requires ImageMagik and wand)")
    # args = parser.parse_args()
    # collect_furniture(in_dir, args.name, args.vb)

    path0 = "C:/Users/urmom/Documents/create/mod/zzz/3dmigoto_dev"
    collect_furniture(path0, "HIABox", "d4c6ca97")

    print(f"Operation completed in {int((time.time()-start)*1000)}ms")

