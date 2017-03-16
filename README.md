# DEPRECATED

We are now using a much more automated process for analyzing data in the Computational Genomics Platform.

This repo is currently only used for issues used to track data processing problems.

# Standard operating procedures

See [SOPs](SOPs).

# Genomics core record-keeping

### Scope

This document describes a procedure to keep track of the data running through the genomics core.  It is expected that these processes will evolve as the core matures.  This document will mature with them.

### Set Requests
When sets of data are to be run through the core, the wrangler who runs the set does the following three things, in order:
1. Check out the BD2K/core-operations repo
2. Create a project subdirectory for the project that requested the file, if one does not already exist.
  1. Add a brief Readme indicating what the project is, and who the technical contacts are.   
3. Create an input file for the sample set:
  1. Name it with a name in the form `<descriptiveLabel>.<libraryPrep>.<date>.[label].input.txt`
    1. The descriptive label is for the user’s benefit
    2. The library prep is generally one of RNASeq, WGS and WXS
    3. The date is the date on which the set enters the system.
    4. Optionally, a descriptive label can be added to the end.
  2. The contents of the file should contain one line per sample, with the sample ID and URL.  The toil config file can be used here.
2. Create a github issue in the BD2KGenomics/core-operations repo:
  1. Give the issue the same name as the file from (above), adding the project name (the subdirectory name) and omitting the ".input.txt" suffix.
  2. In the github issue description, add any special instructions for analyzing the sample set (e.g. samples that cannot be run in the cloud)
  3. Enter text in the issue indicating where the input data is located, how many samples are present, and what type(s) of analyses are to be performed.
  4. Optionally, indicate github users to follow the issue by adding lines with the folliwng syntax:
    `/cc @userId1 @userId2 ...`
5. Add a line to dashboard.txt in the parent directory to identify the set, with:
  1. date
  2. filename from above
  3. Status (initially Entered)
  4. Pipelines to be run
  
### Set execution
As the set is executed, the Github issue is updated to indicate what has been run or is being run.  

When a pipeline is run on a set, the issue is updated to indicate the following:
* Name of pipeline
* Pipeline, with git commit ID
* URLs for inputs
Here is an example:
```
  Run MuTect and MuSE callers on both samples.
  MuTect:

  Toil pipeline: toil-scripts/gatk-pipeline/exome_variant_pipeline.py, git commit 64aa5d715f9a818d64131187daf18ce02bf21fcc

  Inputs:
    reference https://s3-us-west-2.amazonaws.com/cgl-alignment-inputs/genome.fa
    phase https://s3-us-west-2.amazonaws.com/cgl-variant-inputs/1000G_phase1.indels.hg19.sites.vcf
    mills https://s3-us-west-2.amazonaws.com/cgl-variant-inputs/Mills_and_1000G_gold_standard.indels.hg19.sites.vcf
    dbsnp https://s3-us-west-2.amazonaws.com/cgl-variant-inputs/dbsnp_138.hg19.vcf
    cosmic https://s3-us-west-2.amazonaws.com/cgl-variant-inputs/cosmic.hg19.vcf

```
As the set is run, any specific issues that are encountered are recorded in the github issue.

### Set output
When a pipeline has completed on the sample set and a set of outputs are delivered, this is indicated in three places:
  1. The Github issue is updated to indicate that output was made available, and to whom / how it was delivered
  2. The genomics core dashboard file is updated to indicate the pipeline that was run, the date that the outputs were delivered, and the delivery mechanism.
  3. A file is created in the same subdirectory as the input file, listing URLs of the outputs.  Its name mirrors the input file, except that rather than having the suffix `input.txt`, it has the suffix `<analysis>.txt` where `<analysis>` is the human-readable name of the analysis pipeline.  

### Problems and outliers
Whenever a sample requires special handling, or cannot be processed with the rest of the set (e.g. possible file corruption, error conditions that require further investigation), then: 
  1. Move the entries for problem samples from the set file into a separate subset file.
  2. Note the creation of the subset file in the dashboard.txt file and under the Github issue.  If one or more samples has to be cancelled (e.g. because of problems with the input data), then: 
    1. Unless an entire existing set or subset needs to be cancelled, then:
      1. Move the sample(s) in question into a separate subset file 
      2. Note the creation of the subset in the dashboard file and under the Github issue
    2. Mark in both the dashboard file and the Github issue that the subset has been cancelled.  
    3. Create a succinct report describing why the samples were cancelled.  Check the file into github in the same directory as the subset file, with the name `<descriptiveLabel>.<libraryPrep>.<dateEntered>.[label].error.txt`.  Note that this follows the name of the subset file, but changes the `.txt` suffix to `.error.txt`.

### Sample set completion
When a set has completed, its completion is noted (with the date) in the genomics core dashboard file and its Github issue is closed.  A set is considered closed when every sample in the set (and every sample in every subset) has either been executed or cancelled. 

### Set cancellation
If an entire set has to be cancelled without any delivery of output whatsoever (e.g. all samples in the batch are corrupted), then the cancellation is recorded following the steps for cancelling a sample.






  
 


