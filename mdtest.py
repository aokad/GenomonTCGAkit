#!/usr/bin/env python

import hashlib

def get_md5(filename, size = 8192):
    md5 = hashlib.md5()
    with open(filename, 'rb') as f:
        for chunk in iter(lambda: f.read(size * md5.block_size), b''):
            md5.update(chunk)
    return md5.hexdigest()

def main():
    import argparse
    import glob

    prog = "testmd"
    parser = argparse.ArgumentParser(prog = prog)
    parser.add_argument("--version", action = "version", version = prog + "-0.1.0")
    parser.add_argument('bam_pattern', help = "bam files to  glob", type = str)
    parser.add_argument('output', help = "output file", type = str)
    args = parser.parse_args()

    bams = glob.glob(args.bam_pattern)
    f = open(args.output, "wb")
    f.write("bam_pattern=%s, output=%s, files=%d\n" % (args.bam_pattern, args.output, len(bams)))
    f.close()

    for bam in bams:
        hexdigest = get_md5(bam)
        f = open(bam + ".md5", 'rb')
        reference = f.read()
        f.close()

        with open(args.output, 'ab') as f:
            f.write("file=%s, ref=%s, copy=%s\n" % (bam, reference, hexdigest))
            if reference != hexdigest:
                f.write("[ERROR] MD5 check error! %s\n" % (bam))

if __name__ == "__main__":
    main()
