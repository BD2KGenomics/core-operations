# Core Operations Production SOP
## UC Santa Cruz Genomics Institute, Computational Genomics Lab
 
## Environment Setup
 
 These steps should only have to be run once. Toil-box images will have to be updated periodically to stay current.
  
### Setup CGCloud
Comprehensive help is found at: https://github.com/BD2KGenomics/cgcloud .
 The following steps are provided for convenience but it is recommended to read the source documentation.

1. `virtualenv ~/cgcloud`
2. `source cgcloud/bin/activate`
3. `pip install cgcloud-toil==1.5.5`
4. `deactivate`
5. `ln -snf ~/cgcloud/bin/activate ~/bin/`
6. Set `~/.profile` options from CGCloud README
7. `cgcloud create -IT toil-box`

## Running a Pipeline on a Cluster

### Launching cluster
Launch the cluster leader first, and grow the cluster after starting the pipeline.
The directory passed to `--share` should contain the master key if encryption is being used.

- `cgcloud create-cluster --leader-instance-type m3.medium --share=key_dir/ --num-workers 0 --cluster-name example toil`

### Setup and Run Pipeline
SSH into leader, install toil-scripts, setup config and manifest, grow cluster, and start run.

1. `cgcloud ssh -c example toil-leader`
2. `virtualenv --system-site-packages toilscripts`
3. `source toilscripts/bin/activate`
4. `pip install toil-scripts==2.0.11`
5. Run the binary for the pipeline, example: `toil-rnaseq` for the RNA-seq CGL pipeline.
6. Generate a config and manifest file, e.g. `toil-rnaseq generate`. These files will be generated in the current working directory, and contain instructions on how to fill them in.
7. `exit` so we can grow the cluster, in this case by 22 workers, ideally using spot market.
8. `cgcloud grow-cluster --cluster-name example --spot-auto-zone --spot-bid 1.00 --instance-type c3.8xlarge --num-workers 22 toil`
9. `cgcloud ssh -c example toil-leader`
10. Place boto or AWS credentials on the leader (`~/.boto` or `~/.aws/credentials`)
10. `screen -S example-run`
11. `source toilscripts/bin/activate`
12. `toil-rnaseq run --retryCount=1 --workDir=/var/lib/toil --batchSystem=mesos --mesosMaster=mesos-master:5050 --sseKey=/home/mesosbox/shared/master.key aws:us-west-2:jvivian-example-run-1 2>&1 | tee 1.log`

## Explanation of Run Options

- `--retryCount=1` - Ensures samples that failed for non-deterministic reasons have a chance to retry
- `--workDir=/var/lib/toil` - Sets the work directory to the RAID-mounted ephemeral drives
- `--batchSystem=mesos` - Distributed runs on EC2 use the Mesos batch system
- `--mesosMaster=mesos-master:5050` - Tells Mesos what port to use
- `--sseKey` - Encrypts the data in-flight when using the S3 job store for patient security
- The final positional argument is the location of the jobStore

## Handling Errors

Sometimes a pipeline fails. This can be for various reasons, but it is unlikely that there is an issue with the pipeline
or Toil itself. Failures generally stem from an issue with the sample -- improperly paired reads, samples too large for
the amount of memory or disk on a machine, etc.
This assumption isn't based on hubris, but the fact that the pipeline had a throughput of 99.6% across 20,000 samples.

If a pipeline finishes and said there were failed jobs, then investigate the logfile on the leader:

- `less 1.log`
- Type the forward slash `/` and then `TOIL` and hit enter. This will take you to the first error log. 
- See if you can understand why the sample failed. If the error appears to stem from a non-deterministic process, like an HTTP error, then restarting the pipeline is the optimal option.
- Rerun the `toil-rnaseq run ...` command, but add the `--restart` flag and change the log name to `2.log`. 

If the issue looks like it is systemic but based on resources (not enough memory or not enough disk), then please change the instance type to
something that is appropriate for the size of the sample you are trying to run, or increase the size of the `disk` config option.
 
If the pipeline fails despite a `--restart` attempt, please copy the entire error message into a ticket. Include the config and manifest and if possible the path to the sample that failed.
