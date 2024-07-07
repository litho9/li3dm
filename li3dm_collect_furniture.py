import argparse, os, shutil, time
from datetime import datetime
from glob import glob

try:
    from wand import image
except ImportError:
    image = None

def prop(file:str, key:str): idx = file.index(key) + len(key) + 1; return file[idx:idx+8]

if __name__ == "__main__":
    start = time.time()
    parser = argparse.ArgumentParser(description="Collects and renames data from 3dmigoto frame dumps")
    parser.add_argument("-vb", type=str, help="Entity's draw VB hash (Ex.:329f5c91)")
    parser.add_argument("-n", "--name", type=str, default="Collect", help="Output folder name")
    parser.add_argument("-f", "--framedump", type=str, help="Name of framedump folder (if not specified, uses most recent)")
    parser.add_argument("--png", action=argparse.BooleanOptionalAction, help="Convert .dds files to .png (requires ImageMagik and wand)")
    args = parser.parse_args()

    in_dir = args.framedump or glob("FrameAnalysis*")[-1]
    out_dir = args.name + "_" + datetime.today().strftime('%Y-%m-%d-%H%M%S')
    print(f"From folder: {in_dir} to folder {out_dir}...")
    os.mkdir(out_dir)

    pos_file = glob(f"{in_dir}/*-vb0={args.vb}*.buf")[0]
    draw_id = os.path.split(pos_file)[-1][:6]
    tex_file = glob(f"{in_dir}/{draw_id}-vb1=*.buf")[0]  # all draws have a buf we can use. Get the first
    ib_file = glob(f"{in_dir}/{draw_id}-ib=*.buf")[0]

    tex_files = [f for f in glob(f"{in_dir}/{draw_id}-ps-t*") if "!" not in f]
    for i, tex in enumerate(tex_files[:3]):
        idx_name = ["diffuse", "lightMap", "extra", "extra2"][i]
        new_tex_file_name = f"{args.name}-t{str(i)}{idx_name}={prop(tex, 'ps-t' + str(i))}"
        shutil.copyfile(tex, f"{out_dir}/{new_tex_file_name}.{tex[-3:]}")
        if i == 0:
            img = image.Image(filename=tex)
            img.alpha_channel = False
            img.save(filename=f"{out_dir}/{new_tex_file_name}.png")

    shutil.copyfile(pos_file, f"{out_dir}/{args.name}-b0pos={args.vb}.buf")
    shutil.copyfile(tex_file, f"{out_dir}/{args.name}-b1tex={prop(tex_file, 'vb1')}.buf")
    shutil.copyfile(ib_file, f"{out_dir}/{args.name}-b2ib={prop(ib_file, 'ib')}.buf")
    print(f"Operation completed in {int((time.time()-start)*1000)}ms")

