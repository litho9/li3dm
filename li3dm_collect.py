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

    vb0_files = glob(f"{in_dir}/*-vb0={args.vb}*.buf")
    posed_files = [f for f in vb0_files if int(os.path.split(f)[-1][:6]) > 10]  # draw ids <10 are point lists
    draw_ids = [os.path.split(f)[-1][:6] for f in posed_files]
    tex_file = glob(f"{in_dir}/{draw_ids[0]}-vb1=*.buf")[0]  # all draws have a buf we can use. Get the first
    ib_file = glob(f"{in_dir}/{draw_ids[0]}-ib=*.buf")[0]

    pos_file_size = os.path.getsize(posed_files[0])  # the matching pointlist has the same size
    vs = "653c63ba4a73ca8b"  # always this value
    pointlist_vb0 = [f for f in glob(f"{in_dir}/*vb0*{vs}.buf") if os.path.getsize(f) == pos_file_size][0]
    blend_file = glob(f"{in_dir}/{os.path.split(pointlist_vb0)[-1][:6]}-vb1=*.buf")[0]

    ib_indexes = []
    for draw_id in draw_ids:
        f = open(glob(f"{in_dir}/{draw_id}-ib=*.txt")[0], "r")
        f.readline()  # throw away first line, we only need what's in the second one
        first_index = f.readline()[13:-1]  # Ex.: "first index: 0\n"
        if first_index in ib_indexes: continue  # skips duplicates
        print(f"Found new index {first_index} at draw {draw_id}")
        ib_indexes.append(first_index)
        tex_files = [f for f in glob(f"{in_dir}/{draw_id}-ps-t*") if "!" not in f]
        has_normal_map = len([f for f in tex_files if os.path.getsize(f) > 1e6]) > 2  # 1.048.724
        for i, tex in enumerate(tex_files):
            idx_name = ["normalMap", "diffuse", "lightMap", "extra", "extra2"][i if has_normal_map else i + 1]
            new_tex_file_name = f"{args.name}-{first_index.zfill(6)}-t{str(i)}{idx_name}={prop(tex, 'ps-t' + str(i))}"
            shutil.copyfile(tex, f"{out_dir}/{new_tex_file_name}.{tex[-3:]}")
            if args.png and idx_name == "diffuse" and tex.endswith(".dds"):
                img = image.Image(filename=tex)
                img.alpha_channel = False
                img.save(filename=f"{out_dir}/{new_tex_file_name}.png")

    shutil.copyfile(pointlist_vb0, f"{out_dir}/{args.name}-b0pos={prop(pointlist_vb0, 'vb0')}-draw={args.vb}.buf")
    shutil.copyfile(tex_file, f"{out_dir}/{args.name}-b1tex={prop(tex_file, 'vb1')}.buf")
    indexes = '_'.join(map(str, sorted(map(int, ib_indexes))))  # here's a classic example of python being dumb
    shutil.copyfile(ib_file, f"{out_dir}/{args.name}-b2ib={prop(ib_file, 'ib')}-indexes={indexes}.buf")
    shutil.copyfile(blend_file, f"{out_dir}/{args.name}-b3blend={prop(blend_file, 'vb1')}.buf")
    print(f"Operation completed in {int((time.time()-start)*1000)}ms")

