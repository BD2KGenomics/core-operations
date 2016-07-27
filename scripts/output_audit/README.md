# Overview

A simple script to look for output in S3 and relate it back to the github input manifests.

## Dependencies

* perl
* AWS CLI 1.10.x or greater
* AWS credentials for our shared account

## Usage

    cat *input* | grep -v bam > ../scripts/output_audit/all.input.txt
    cd ../scripts/output_audit
    cat all.input.txt | perl match.pl
