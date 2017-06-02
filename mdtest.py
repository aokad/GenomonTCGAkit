#!/usr/bin/env python

def get_md5(filename, size = 8192):
    import hashlib

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
    parser.add_argument('bamfile', help = "bam files to  glob", type = str)
    parser.add_argument('md5', help = "bam files to  glob", type = str)
    
    args = parser.parse_args()

    hexdigest = get_md5(bam);
    return (hexdigest == args.md5)

if __name__ == "__main__":
    main()
