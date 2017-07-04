# -*- coding: utf-8 -*-
"""
Created on Thu Nov 05 16:44:30 2015

@brief:  Check script, BAM can be used with the genomon.
@author: okada

$Id: check_bam.py 180 2017-07-04 03:18:32Z aokada $
$Rev: 180 $

# before run
@code
export DRMAA_LIBRARY_PATH=/geadmin/N1GE/lib/lx-amd64/libdrmaa.so.1.0
@endcode

# run
@code
check_bam.py {TCGA metadata.json} {path to bam dir} {path to output dir} --config_file {option: config file}
@endcode
"""
rev = " $Rev: 180 $"

from multiprocessing import Process
import time
import sys
import os
import drmaa
import ConfigParser
import argparse

import subcode

cmd_format = """
#!/bin/bash
#
# download TCGA bam file
#
#$ -S /bin/bash         # set shell in UGE
#$ -cwd                 # execute at the submitted dir
#$ -e {log}
#$ -o {log}
pwd                     # print current working directory
hostname                # print hostname
date                    # print date
set -xv

echo {analysis_id} > {out}

echo {md5} >> {out}
md5=`md5sum {bam} | cut -f 1 -d " "`
echo $md5 >> {out}

if test "{md5}" = $md5; then

  total_l=`{samtools} view {bam} | wc -l`
  echo `expr $total_l` >> {out}

  single_l=`{samtools} view -F 1 {bam} | wc -l`
  echo `expr $single_l` >> {out}

else
  echo -1 >> {out}
  echo -1 >> {out}
fi
 
"""

def qsub_process(name, output_dir, bam, analysis_id, md5, config):
    
    script_path = output_dir + "/scripts/" + name + ".sh"
    log_path = output_dir + "/log/" + name + ".log"
    result_path = output_dir + "/result/" + name + ".txt"
    
    subcode.write_log(log_path, "w", name + ": Subprocess has been started, with script " + script_path, True, False)

    cmd = cmd_format.format(samtools = config.get('TOOLS', 'samtools'), 
                bam = bam, analysis_id = analysis_id, md5=md5,
                out = result_path, log = output_dir + "/log")

    f_sh = open(script_path, "w")
    f_sh.write(cmd)
    f_sh.close()
    os.chmod(script_path, 0750)

    s = drmaa.Session()

    return_val = -1
    retry_max = config.getint('JOB_CONTROL', 'retry_max')
    for i in range(retry_max):
        
        s.initialize()
        jt = s.createJobTemplate()
        jt.jobName = "check_bam"
        jt.outputPath = ':' + output_dir + '/log'
        jt.errorPath = ':' + output_dir + '/log'
        jt.nativeSpecification = config.get('JOB_CONTROL', 'qsub_option')
        jt.remoteCommand = script_path
        
        jobid = s.runJob(jt)
    
        subcode.write_log(log_path, "a", name + ": Job has been submitted with id: " + jobid, True, True)

        log_text = ""
        err = False
        
        try:
            wait_time = config.getint('JOB_CONTROL', 'wait_time')
            if wait_time == 0:
                wait_time = drmaa.Session.TIMEOUT_WAIT_FOREVER
                
            retval = s.wait(jobid, wait_time)
            log_text = 'with status: ' + str(retval.hasExited) + ' and exit status: ' + str(retval.exitStatus)
            if retval.exitStatus != 0 or retval.hasExited == False:
                err = True
                
        except Exception as e:
            s.control(jobid, drmaa.JobControlAction.TERMINATE)
            log_text = "with error " + e.message
            err = True
        
        subcode.write_log(log_path, "a", name + ": Job: " + str(jobid) + ' finished ' + log_text, True, True)

        s.deleteJobTemplate(jt)
        s.exit()

        if err == False:
            return_val = 0
            break
        
    subcode.write_log(log_path, "a", name + ": Subprocess has been finished: " + str(return_val), True, True)

    return return_val

def result_line (result, bam_path="", analysis_id="", md5_ref="", md5_alt="", read_total="", read_single="", read_rate=-1):
    template = "{result},{bam_path},{analysis_id},{md5_ref},{md5_alt},{read_total},{read_single},{read_rate:.3f}\n"
    
    return template.format(
                result = result, 
                bam_path = bam_path, 
                analysis_id = analysis_id, 
                md5_ref = md5_ref, 
                md5_alt = md5_alt, 
                read_total = read_total, 
                read_single = read_single, 
                read_rate = read_rate
            )
def main():
    
    prog = os.path.splitext(os.path.basename(sys.argv[0]))[0]
    
    # get args
    parser = argparse.ArgumentParser(prog = prog)
    
    parser.add_argument("--version", action = "version", version = prog + rev)
    
    parser.add_argument('metadata', help = "metdata-file(.json) downloaded from TCGA", type = str)
    parser.add_argument('bam_dir', help = "bam downloaded directory", type = str)
    parser.add_argument('output_dir', help = "output root directory", type = str)
    # parser.add_argument('project', help = "project name (ACC, BLCA, etc)", type = str)

    parser.add_argument("--config_file", help = "config file", type = str, default = "")
    args = parser.parse_args()
    
    output_dir = os.path.abspath(args.output_dir)
    metadata = os.path.abspath(args.metadata)
    bam_dir = os.path.abspath(args.bam_dir)
    
    if len(args.config_file) > 0:
        config_file = os.path.abspath(args.config_file)
    else:
        config_file = os.path.splitext(os.path.abspath(sys.argv[0]))[0] + ".cfg"
        
    # read config file
    config = ConfigParser.RawConfigParser()
    config.read(config_file)
    
    # make dir
    if (os.path.exists(output_dir) == False):
        os.makedirs(output_dir)
    if (os.path.exists(output_dir + "/log") == False):
        os.makedirs(output_dir + "/log")
    if (os.path.exists(output_dir + "/result") == False):
        os.makedirs(output_dir + "/result")
    if (os.path.exists(output_dir + "/scripts") == False):
        os.makedirs(output_dir + "/scripts")
    
    this_name = "%s_%s" % (prog, subcode.date_str())
    log_path = output_dir + "/log/%s.log" % this_name
    subcode.write_log(log_path, "w", "Start main process.", True, True)

    process_list = []
    
    # read metadata
    loaded = subcode.load_metadata(metadata, bam_dir, config)
    data = loaded["data"]
    
    result_path = output_dir + "/result/result_%s.csv" % this_name
    f = open(result_path, "w")
    f.write("result,bam_path,analysis_id,md5_reference,md5_target,total_lines,single_lines,single_rate\n")
    for row in loaded["invalid"]:
        f.write(result_line( result = row[1], analysis_id = row[0] ))
    f.close()
    
    # loop for job start
    max_once_jobs = config.getint('JOB_CONTROL', 'max_once_jobs')
    max_all_jobs = max_once_jobs * 2
    interval = float(config.getint('JOB_CONTROL', 'interval'))/1000.0
    
    j = 0
    while j < len(data):
        alives = 0
        for process in process_list:
            if process.exitcode == None:
               alives += 1
    
        jobs = max_all_jobs - alives
        if jobs > max_once_jobs:
            jobs = max_once_jobs
        
        for i in range(jobs):
            if j >= len(data):
                break
                
            name = "%s_%05d_%s" % (prog, j+1, subcode.date_str())

            bam = bam_dir + "/" + data[j]["file_id"] + "/" + data[j]["file_name"]
            
            process = Process(target=qsub_process, name=name, args=(name, output_dir, bam, data[j]["file_id"], data[j]["md5sum"], config))
            process.daemon == True
            process.start()
            
            subcode.write_log(log_path, "a", name + ": Start sub process.", True, False)

            process_list.append(process)
            j += 1
        
            time.sleep(interval)

    # summarize logs and results  
    th_read_total = 0
    if config.has_option("CHECKBAM", "read_total"):
        th_read_total = config.getint("CHECKBAM", "read_total")
    
    th_single_rate = 1.0
    if config.has_option("CHECKBAM", "single_rate"):
        th_read_total = config.getfloat("CHECKBAM", "single_rate")
        
    for process in process_list:
        process.join()

        f_plog = open(output_dir + '/log/' + process.name + ".log")
        plog = f_plog.read()
        f_plog.close()
        os.remove(output_dir + '/log/' + process.name + ".log")

        subcode.write_log(log_path, "a", plog, False, False)
        
        f_result = open(output_dir + '/result/' + process.name + ".txt")
        pres = f_result.read()
        f_result.close()
        lines = pres.split("\n")
        f = open(result_path, "a")
        
        result = bam_path = analysis_id = md5_ref = md5_alt = read_total = read_single = ""
        read_rate = -1
            
        if len(lines) >= 5:
            os.remove(output_dir + '/result/' + process.name + ".txt")
            
            analysis_id = lines[0]
            md5_ref = lines[1]
            md5_alt = lines[2].split(" ")[0]
            bam_path = lines[2].split(" ")[1]
            read_total = lines[3]
            read_single = lines[4] 
            read_rate = float(lines[4]) / float(lines[3])            
            
            if md5_ref != md5_alt:
                result = "unmatch checksum"
            elif int(read_total) < th_read_total:
                result = "too few reads"
            elif read_rate > th_single_rate:
                result = "single read"
            else:
                result = "OK"
        else:
            result = "check_error"
            
            if len(lines) == 4:
                read_total = lines[3], 
            if len(lines) >= 3:
                md5_alt = lines[2].split(" ")[0]
                bam_path = lines[2].split(" ")[1] 
            if len(lines) >= 2:
                md5_ref = lines[1]
            if len(lines) >= 1:
                analysis_id = lines[0]
                
        f.write(result_line(
            result = result, 
            bam_path = bam_path, 
            analysis_id = analysis_id, 
            md5_ref = md5_ref, 
            md5_alt = md5_alt, 
            read_total = read_total, 
            read_single = read_single, 
            read_rate = read_rate
        ))
        
        f.close()    

    subcode.write_log(log_path, "a", "End main process.", True, True)

def load_resultfile(result_file, choose_ok = True):
    
    if not os.path.exists(result_file):
        print("not exists path: %s" % (result_file))
        return None
    
    result = []
    f = open(result_file)
    for line in f.readline():
        line = line.rstrip("\n")
        items = line.split(",")
        if len(items) >= 2:
            if choose_ok == True and items[0] != "OK":
                continue
            if items[1] == "":
                continue
            
            result.append({ "path": items[1], "result": items[0]})
    
    f.close()
    return result
    
if __name__ == "__main__":
    main()
