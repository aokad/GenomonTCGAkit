# -*- coding: utf-8 -*-
"""
Created on Thu Nov 05 16:44:30 2015

@brief:  Check script, BAM can be used with the genomon.
@author: okada

# before run
export DRMAA_LIBRARY_PATH=/geadmin/N1GE/lib/lx-amd64/libdrmaa.so.1.0

# run
check_singlebam.py {path to working dir} {TCGA summary file} {path to bam dir} --config_file {option: config file}
"""

from multiprocessing import Process
import pandas
import time
import datetime
import sys
import os
import drmaa
import ConfigParser
import argparse

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

total_l=`{samtools} view {bam} | wc -l`
single_l=`{samtools} view -F 1 {bam} | wc -l`

echo {analysis_id} > {out}
echo `expr $total_l` >> {out}
echo `expr $single_l` >> {out}
"""

def write_log(path, mode, text, date, printer):

    t = ""
    if date == True:
        now = datetime.datetime.now()
        t = "{0:0>4d}/{1:0>2d}/{2:0>2d} {3:0>2d}:{4:0>2d}:{5:0>2d}: ".format(
                                now.year, now.month, now.day, now.hour, now.minute, now.second)

    f = open(path, mode)
    f.write(t + text + "\n")
    f.close()

    if printer == True:
        print (t + text)


def qsub_process(name, output_dir, bam, analysis_id, config):
    
    script_path = output_dir + "/scripts/" + name + ".sh"
    log_path = output_dir + "/log/" + name + ".log"
    result_path = output_dir + "/result/" + name + ".txt"
    
    write_log(log_path, "w", name + ": Subprocess has been started, with script " + script_path, True, False)
    
    if os.path.exists(bam) == False:
        write_log(log_path, "a", name + "[%s] bam file is not exists.: %s" % (analysis_id, bam), True, True)
        f = open(result_path, "w")
        f.write("%s\n-1\n-1" % analysis_id)
        f.close()
        write_log(log_path, "a", name + ": Subprocess has been finished: 0", True, True)
        return 0

    cmd = cmd_format.format(samtools = config.get('TOOLS', 'samtools'), 
                bam = bam, analysis_id = analysis_id, \
                out = result_path, log = output_dir + "/log")

    f_sh = open(script_path, "w")
    f_sh.write(cmd)
    f_sh.close()
    os.chmod(script_path, 0750)


    s = drmaa.Session()

    return_val = 1
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
    
        write_log(log_path, "a", name + ": Job has been submitted with id: " + jobid, True, True)

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
        
        write_log(log_path, "a", name + ": Job: " + str(jobid) + ' finished ' + log_text, True, True)

        s.deleteJobTemplate(jt)
        s.exit()

        if err == False:
            return_val = 0
            break
        
    write_log(log_path, "a", name + ": Subprocess has been finished: " + str(return_val), True, True)

    return return_val
    

def main():
    name = os.path.splitext(os.path.basename(sys.argv[0]))[0]
    
    # get args
    parser = argparse.ArgumentParser(prog = name)
    
    parser.add_argument("--version", action = "version", version = name + "-1.0.0")
    parser.add_argument('output_dir', help = "output root directory", type = str)
    parser.add_argument('summary', help = "summary file download from TCGA", type = str)
    parser.add_argument('bam_dir', help = "bam downloaded directory", type = str)
    parser.add_argument("--config_file", help = "config file", type = str, default = "")
    args = parser.parse_args()

    output_dir = os.path.abspath(args.output_dir)
    summary = os.path.abspath(args.summary)
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
    
    now = datetime.datetime.now()
    this_name = "check_bam_{0:0>4d}{1:0>2d}{2:0>2d}_{3:0>2d}{4:0>2d}{5:0>2d}".format(
                now.year, now.month, now.day, now.hour, now.minute, now.second)
    log_path = output_dir + "/log/" \
                + "%s.log" % this_name
    write_log(log_path, "w", "Start main process.", True, True)

    process_list = []
    
    # read summary
    ext = os.path.splitext(summary)[1]
    if ext.lower() == ".tsv":
        data = pandas.read_csv(summary, sep = "\t")
    elif ext.lower() == ".csv":
        data = pandas.read_csv(summary, sep = ",")
    else:
        print (ext + " file is not support")
        return
    
    if len(data) < 1:
        print ("no summary data.")
        return

    # loop for job start
    else:        
        max_once_jobs = config.getint('JOB_CONTROL', 'max_once_jobs')
        max_all_jobs = max_once_jobs * 2
        interval = config.getint('JOB_CONTROL', 'interval')
        
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
                    
                now = datetime.datetime.now()
                name = "{name}_{index:0>5d}_{year:0>4d}{month:0>2d}{day:0>2d}_{hour:0>2d}{minute:0>2d}{second:0>2d}".format(
                        name = "check_bam", index = j+1,
                        year = now.year, month = now.month, day = now.day, 
                        hour = now.hour, minute = now.minute, second = now.second)

                bam = bam_dir + "/" + data.iloc[j]["analysis_id"] + "/" + data.iloc[j]["filename"]
                
                process = Process(target=qsub_process, name=name, args=(name, output_dir, bam, data.iloc[j]["analysis_id"], config))
                process.daemon == True
                process.start()
                
                write_log(log_path, "a", name + ": Start sub process.", True, False)

                process_list.append(process)
                j += 1
            
            time.sleep(interval)

    # summarize logs and results
    f = open(output_dir + "/result/check_bam_result.csv", "w")
    f.write("analysis_id,total_lines,single_lines\n")
    f.close()
    
    for process in process_list:
        process.join()

        f_plog = open(output_dir + '/log/' + process.name + ".log")
        plog = f_plog.read()
        f_plog.close()
        os.remove(output_dir + '/log/' + process.name + ".log")

        write_log(log_path, "a", plog, False, False)
        
        f_result = open(output_dir + '/result/' + process.name + ".txt")
        pres = f_result.read()
        f_result.close()
        lines = pres.split("\n")
        if len(lines) >= 3:
            os.remove(output_dir + '/result/' + process.name + ".txt")
            
            f = open(output_dir + "/result/result_%s.csv" % this_name, "a")
            f.write(lines[0] + "," + lines[1] + "," + lines[2] + "\n")
            f.close()

    write_log(log_path, "a", "End main process.", True, True)

if __name__ == "__main__":
    main()
