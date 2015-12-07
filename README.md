# Genomics core record-keeping

##### Scope

This document describes a procedure to keep track of the data running through the genomics core.  It is expected that these processes will evolve as the core matures.  This document will mature with them.

##### Batch Requests
When batches are to be run through the core, the wrangler who runs the batch does the following three things, in order:
1. Creates a github issue in the BD2KGenomics/core-operations repo:
  1. Given the issue a name that indicates the project, the sample library prep (RNASeq, WGS, WXS, …) and a unique label of some form.
  2. In the github issue description, add any special instructions for analyzing the batch (e.g. samples that cannot be run in the cloud)
  3. Enter text in the issue indicating where the input data is located, how many samples are present, and what type(s) of analyses are to be performed.
  4. Note the github issue number.
2. Check out the BD2KGenomics/core-operations repo.
3. Under this repo, create a subdirectory for the project if one has not already been created.
  * The subdirectory should have a short Readme.md file that says what the project is at a very high level and indicates internal contacts.
4. Create one more more batch file in the project subdirectory.
  1. Name it with a name in the form `<descriptiveLabel>.<libraryPrep>.<githubIssueNumber>.[sub-batch-id].txt`
    1. The descriptive label is for the user’s benefit
    2. The library prep is generally one of RNASeq, WGS and WXS
    3. The github issue number is the number assigned to the github issue above.
    4. If the batch will be broken up into multiple batches for execution, these batches can each be identified with unique sub batch IDs.
  2. The contents of the file should contain one line per sample, with the sample ID.  The toil config file can be used here.
5. Add a line to manifest.txt in the parent directory to identify the batch, with:
  1. date
  2. (sub)batch filename from above
  3. Status (initially Entered)
  
##### Batch execution
As the batch is executed, the Github issue is updated to indicate the status of the batch.  These updates include but are not limited to:
  Sample upload (with new location)
  Pipelines started
  Pipelines completed
  Output data made available

##### Batch output
When a pipeline has completed on the batch and a set of outputs are delivered, this is indicated in two places:
  1. The Github issue is updated to indicate when, how and to whom the outputs were delivered.
  2. The genomics core manifest file is updated to indicate the pipeline that was run, the date that the outputs were delivered, and the delivery mechanism.

##### Problems and outliers
Whenever a sample requires special handling, or cannot be processed with the rest of the batch (e.g. possible file corruption, error conditions that require further investigation), then: 
  1. Move the problem samples into a separate sub-batch file.
  2. Note the creation of the sub-batch file in the manifest.txt file and under the Github issue.  If one or more samples has to be cancelled (e.g. because of problems with the input data), then: 
    1. Unless an entire existing batch or sub-batch needs to be cancelled, then:
      1. Move the sample(s) in question into a separate sub-batch file 
      2. Note the creation of the sub-batch in the manifest file and under the Github issue
    2. Mark in both the manifest file and the Github issue that the sub-batch has been cancelled.  
    3. Create a succinct report describing why the samples were cancelled.  Check the file into github in the same directory as the sub-batch file, with the name `<descriptiveLabel>.<libraryPrep>.<githubIssueNumber>.[sub-batch-id].error.txt`.  Note that this follows the name of the sub-batch file, but changes the `.txt` suffix to `.error.txt`.

##### Batch completion
When a batch has completed, its completion is noted (with the date) in the genomics core manifest file and its Github issue is closed.  A batch is considered closed when every sample in the batch (and every sample in every sub-batch) has either been executed or cancelled. 

##### Batch cancellation
If an entire batch has to be cancelled without any delivery of output whatsoever (e.g. all samples in the batch are corrupted), then the cancellation is recorded following the steps for cancelling a sample.






  
 


