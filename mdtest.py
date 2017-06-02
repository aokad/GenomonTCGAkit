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
    
    prog = "testmd"
    parser = argparse.ArgumentParser(prog = prog)
    parser.add_argument("--version", action = "version", version = prog + "-0.1.0")
    parser.add_argument('bam', help = "bam file", type = str)
    parser.add_argument('md5', help = "reference checksum", type = str)
    
    args = parser.parse_args()

    hexdigest = get_md5(args.bam);
    if hexdigest == args.md5:
        return 0
    
    return -1

if __name__ == "__main__":
    import sys
    sys.exit(main())
    