# -*- coding: utf-8 -*-
"""
Created on Wed Nov 11 16:47:03 2015

@brief:  (1) Split TCGA metadata.json. Per diseases.<br>
         
@author: okada

$Id: split_metadata.py 120 2016-01-08 04:44:28Z aokada $
$Rev: 120 $

# run
@code
split_metadata.py {input} {output_dir}
@endcode
"""
rev = " $Rev: 120 $"

def main():

    import os
    import sys
    import argparse
    import json
    
    name = os.path.splitext(os.path.basename(sys.argv[0]))[0]
    
    # get args
    parser = argparse.ArgumentParser(prog = name)
    
    parser.add_argument("--version", action = "version", version = name + rev)
    parser.add_argument('input', help = "metadata files download from TCGA, split with ','", type = str)
    parser.add_argument('output_dir', help = "output root directory", type = str)
    
    args = parser.parse_args()
    
    output_dir = os.path.abspath(args.output_dir)
    if os.path.exists(output_dir) == False:
        os.makedirs(output_dir)

    inputs = args.input.split(",")
    outputs = []
    
    for json_file in inputs:
        for obj in json.load(open(json_file)):
            write_file = "%s/%s.json" % (output_dir, obj["cases"][0]["project"]["project_id"])
            fw = None
            if write_file in outputs:
                fw = open(write_file, "a")
                fw.write(",\n")
            else:
                outputs.append(write_file)
                fw = open(write_file, "w")
                fw.write("[\n")
            
            json.dump(obj, fw, ensure_ascii=False, indent=4, sort_keys=True, separators=(',', ': '))
            fw.close()
            
    for write_file in outputs:
        fw = open(write_file, "a")
        fw.write("\n]\n")
        fw.close()

if __name__ == "__main__":
    main()
