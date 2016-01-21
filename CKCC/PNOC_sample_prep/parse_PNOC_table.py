#!/usr/bin/env python2.7

import sys, os, re, getopt
import argparse
import glob
import hashlib
import os
import shutil
import subprocess

usage = sys.argv[0]+""" <file>

From excel to PNOC converted table, find fastq files for a single sample, rename
so that the sample name is identical between treatments, download encrypted fastq files from
submitters ASW S3 location, decrypt, unzip, concatenate to one R1 and one R2 file per treatment, 
rezip, encrypt and upload to our S3 location.

outputs uuid,R1fastq,R2fastq

Requirements:
pip install aws
pip install s3am (--pre)

"""
def build_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--infile', required=True, help='input table')
    parser.add_argument('-t', '--intype', required=True, help='feas or trial')
    parser.add_argument('-p', '--pwfile', required=True, help='decrypt password file full path')
    return parser

def readTable(infile):
    pnoc = []
    cStudy = None
    f = open(infile,'r')
    for line in f:
        if line.startswith('study'):
            continue
        line = line.strip()
        fields = line.split('\t')
        if len(fields) == 4:	# new study
    	    cStudy = fields[0]
    	    sObj = fastqSet(fields, cStudy, stype[fields[1]])
            pnoc.append(sObj)
        elif len(fields) == 3:	# new type
            fields[:0] = ['undef']
    	    sObj = fastqSet(fields, cStudy, stype[fields[1]])
            pnoc.append(sObj)
        elif len(fields) == 1:	# new fastq, append
    	    sObj.addFq(fields[0])
        else:
            print >>sys.stderr, "do not understand input", line
    f.close()
    for i in pnoc:
        i.sampleId()
        i.combine()
    return pnoc




class fastqSet(object):
    """ 
    tables contain fields study, libraries, Fastq Path
    between study and libraries is a headerless field that indicates Tumor DNA, Constitutional (control) DNA, or Tumor RNA
    The fastq path samples are split in several lines.
    """
    def __init__(self, fields, study, stype):
        self.study  = study
        self.stype  = stype
        self.lib    = fields[2]
        # the first fastq starts with a quote mark
        self.fastq  = [fields[3].split('"')[1]]
        self.basedir = os.path.dirname(self.fastq[0])
    def addFq(self, field):
        "field may end with a quote mark"
        self.fastq.append(field.replace('"',''))
    def sampleId(self):
        "create a sample ID that can be used for all three types of data"
        self.uuid = ('_').join(os.path.basename(self.fastq[0]).split('_')[0:3])
    def combine(self):
        "separate forward and reverse fastqs"
        self.basedirs = set()
        self.r1 = []
        self.r2 = []
        for sf in self.fastq:
            self.basedirs.add(os.path.dirname(sf))
            f = sf.replace('_', '.')
            fields = f.split('.')
            if 'R2' in fields:
                self.r2.append(sf)
            if 'R1' in fields:
                self.r1.append(sf)
        # sanity checks
        if any(map(lambda v: v in self.r1, self.r2)): 
            print >>sys.stderr, "ERROR, same fastq in forward and reverse", self.r1, self.r2
        if len(self.r1) + len(self.r2) != len(self.fastq):
            print >>sys.stderr, "did not match all", self.fastq
            sys.exit()

def awsSync(awsbasedir, fqdirs, outdir):
    "Get all files for a single experiment"
    for fd in fqdirs:
        sync_command = ['aws',
                    's3',
                    'sync',
                    '{}'.format(os.path.join(awsbasedir, fd)+'/'),
                    '{}'.format(outdir)]
        print " ".join( str(i) for i in sync_command)
        try:
            subprocess.check_call(sync_command)
        except Exception, e:
            continue

def decrypt(infile, outdir, pwfile):
    "Run openssl to decrypt inputfile"
    outfile = os.path.join(outdir, os.path.basename(infile))
    ssl_command = ['openssl',
                  'enc',
                  '-d',
                  '-aes-256-cbc',
                  '-a',
                  '-in', '{}'.format(infile),
                  '-out', '{}'.format(outfile),
                  '-pass', 'file:{}'.format(pwfile)]
    print >>sys.stderr, " ".join( str(i) for i in ssl_command)
    subprocess.check_call(ssl_command)

def concat_files(indir, inputfiles, outputname):
    "concatenate gzipped inputfiles"
    for f in inputfiles:
        cat_command = [ 'cat', 
                         '{}'.format(os.path.join(indir, os.path.basename(f)))]
        print >> sys.stderr,  " ".join( str(i) for i in cat_command),  '>>', outputname
        with open(outputname, 'a') as f_out:
            subprocess.check_call(cat_command, stdout=f_out)

def encrypted_upload(myfile, tempkey):
    """
    Note that upload location is hardcoded
    """
    # Parse s3_dir to get bucket and s3 path
    s3_dir = 'cgl-driver-projects-encrypted/treehouse/pnoc-samples/'
    key_path = '/home/mesosbox/master.key'
    bucket_name = s3_dir.lstrip('/').split('/')[0]
    key_name = 'treehouse/pnoc-samples/' + os.path.basename(myfile)
    base_url = 'https://s3-us-west-2.amazonaws.com/'
    url = os.path.join(base_url, bucket_name, key_name)
    # Generate keyfile for upload
    with open(tempkey, 'wb') as f_out:
        f_out.write(generate_unique_key(key_path, url))
    # Upload to S3 via S3AM
    s3am_command = ['s3am',
                    'upload',
                    '--sse-key-file', tempkey,
                    'file://{}'.format(myfile),
                    bucket_name, key_name]
    print >> sys.stderr,  " ".join( str(i) for i in s3am_command)
    subprocess.check_call(s3am_command)
    return url

def generate_unique_key(master_key_path, url):
    """
    master_key_path: str    Path to the BD2K Master Key (for S3 Encryption)
    url: str                S3 URL (e.g. https://s3-us-west-2.amazonaws.com/bucket/file.txt)

    Returns: str            32-byte unique key generated for that URL
    """
    with open(master_key_path, 'r') as f:
        master_key = f.read()
    assert len(master_key) == 32, 'Invalid Key! Must be 32 characters. ' \
                                  'Key: {}, Length: {}'.format(master_key, len(master_key))
    new_key = hashlib.sha256(master_key + url).digest()
    assert len(new_key) == 32, 'New key is invalid and is not 32 characters: {}'.format(new_key)
    return new_key


# Main
# Run program
parser = build_parser()
args = parser.parse_args()

# setup type dict
stype = { 'Tumor DNA':'tumor_WXS', 'Tumor RNA':'tumor_RNASeq', 'Constitutional DNA':'control_WXS'}

pnoc = readTable(args.infile)

if args.intype == 'feas':
    awsbasedir = 's3://cbttc.seq.data/pnoc/feasibility_data'
    tempkey = 'feas.tempkey'
elif args.intype == 'trial':
    awsbasedir = 's3://cbttc.seq.data/pnoc/trial_data'
    tempkey = 'trial.tempkey'
else:
    print "intype should be feas or trial, not", args.intype
    sys.exit(1)
outdir = '/mnt/ephemeral'

curStudy = ''
didDecrypt = []
for i in pnoc:
    # the fastq files for one sample are in the same directory
    # NOTE: We can download without submitter's .boto file
    # if we're on a new set, remove the previous one
    if i.study != curStudy or (args.intype =='feas'):
        if len(didDecrypt) > 0:
            rm_command = ['rm', 
                  '-rf',
                  '{}'.format((' ').join(str(i) for i in didDecrypt))]
            print >> sys.stderr,  " ".join( str(i) for i in rm_command)
            #subprocess.check_call(rm_command)
        curStudy = i.study
        didDecrypt = []
        awsSync(awsbasedir, i.basedirs, outdir)
    # decrypt downloaded fastq files
    decryptdir = os.path.join(outdir, '{u}_{s}'.format(u=i.uuid, s=i.stype))
    os.mkdir(decryptdir)
    print >> sys.stderr,  "mkdir", decryptdir
    for f in i.fastq:
        fpath = os.path.join(outdir, os.path.basename(f))
        decrypt(fpath, decryptdir, args.pwfile)
        didDecrypt.append(fpath)

    # concatenate
    r1zip = '{d}/{u}_{s}.R1.fastq.gz'.format(d=os.path.join(decryptdir), u=i.uuid, s=i.stype) 
    r2zip = '{d}/{u}_{s}.R2.fastq.gz'.format(d=os.path.join(decryptdir), u=i.uuid, s=i.stype) 
    concat_files(decryptdir, i.r1, r1zip)
    concat_files(decryptdir, i.r2, r2zip)

    # and upload
    r1url = encrypted_upload(r1zip, tempkey)
    r2url = encrypted_upload(r2zip, tempkey)

    # Remove used fastq files and newly created files, but keep unused donwloaded fastq files
    # they will be used in the next round
    rm_command = ['rm', 
                  '-rf',
                  '{}'.format(decryptdir)]
    
    print >> sys.stderr,  " ".join( str(i) for i in rm_command)
    subprocess.check_call(rm_command)

    # print information on new filenames
    print '{}_{},{},{}'.format(i.uuid, i.stype, r1url, r2url)



