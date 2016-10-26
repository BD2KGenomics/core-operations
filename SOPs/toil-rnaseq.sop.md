# SOP for the RNASeq pipeline

   
## 1) Setup CGCloud

The step in this section should only have to be performed once. `toil-box`
images will have to be updated following major releases of Toil that contain
critical features or bug fixes, or at the direction of the Toil development
team.

Comprehensive help can be found at
[CGCloud](https://github.com/BD2KGenomics/cgcloud). The following steps are
provided for reference but it is recommended to read the source documentation
to gain full understanding on how to use CGCloud.

1. `virtualenv ~/cgcloud`
2. `source cgcloud/bin/activate`
3. `pip install cgcloud-toil==1.5.5`
4. `deactivate`
5. `ln -snf ~/cgcloud/bin/activate ~/bin/`
6. Configure the CGCLoud environment in `~/.profile` as explained in the CGCloud Core README, specifically
    - `export CGCLOUD_ZONE=us-west-2a`
    - `export CGCLOUD_PLUGINS="cgcloud.toil:$CGCLOUD_PLUGINS"`
    - `export CGCLOUD_KEYPAIRS="__me__ @@developers"`
7. Finally, create the image: `cgcloud create -IT toil-box`


## 2) Launch a cluster

Launch the leader instance first, and grow the cluster by adding workers after
starting the pipeline. 

The directory passed to the `--share` option—`keydir` in this example—should
contain the master key if encryption is being used:

```
cgcloud create-cluster --leader-instance-type m3.medium \
                       --share=key_dir/ \
                       --num-workers 0 \
                       --cluster-name example \
                       toil
```

## 3) Install and configure the pipeline

SSH into leader, install toil-scripts, setup config and manifest, grow cluster,
and start run.

1. `cgcloud ssh --cluster-name example toil-leader`

2. `virtualenv --system-site-packages toil-scripts`

3. `source toil-scripts/bin/activate`

4. `pip install toil-scripts==2.0.11`

5. Generate a config and manifest file, e.g. `toil-rnaseq generate`. These
   files will be generated in the current working directory, and contain
   instructions on how to fill them in.

6. `exit` so we can grow the cluster, in this case by 22 workers, ideally using
   spot market.

7. `cgcloud grow-cluster --cluster-name example --spot-auto-zone --spot-bid
   1.00 --instance-type c3.8xlarge --num-workers 22 toil`

8. `cgcloud ssh --cluster-name example toil-leader`

9. Place boto or AWS credentials on the leader (`~/.boto` or `~/.aws/credentials`)

## 4) Run the pipeline

Start a screen session

```
screen -S example-run
```

Activate the virtualenv

```
source toil-scripts/bin/activate
```

Run the pipeline:

```
toil-rnaseq run --retryCount=1 \
                --workDir=/var/lib/toil \
                --batchSystem=mesos \
                --mesosMaster=mesos-master:5050 \
                --sseKey=/home/mesosbox/shared/master.key \
                aws:us-west-2:jvivian-example-run-1 \
                2>&1 | tee 1.log
```

What do the above options mean:

- Passing `--retryCount=1` ensures that samples that failed for
  non-deterministic reasons have a chance to retry. A retry count of 1 means
  that any job will be attempted at most two times, one initial attempt, and
  one retry. If both attempts fail for one or more jobs in the pipeline, the
  entire pipeline will fail. You can retry the entire pipeline again, possible
  after modifying by adding `--restart` to the above command.

- The `--workDir=/var/lib/toil` option sets the work directory to the
  RAID-mounted ephemeral drives. This is a workaround for
  https://github.com/BD2KGenomics/toil/issues/1154. Once that is fixed, this
  option can be removed.

- `--batchSystem=mesos` and `--mesosMaster=mesos-master:5050` configures the
  Mesos batchsystem that must be used on clusters in EC2.

- The `--sseKey` option 1) enables encryption of intermediate files in Toil's
  job store and 2) configures the secret key to encrypt those files with. This
  is needed if the samples are access controlled for patient privacy. The key
  specified here is also used to 3) decrypt inputs to the pipeline and encrypt
  its outputs. For this to work, the inputs must have been uploaded with s3am's
  `--sse-key-is-master`.

- The final positional argument (`aws:us-west-2:jvivian-example-run-1`)
  specifies the job store location. On EC2, you almost always want to use
  `aws:` followed by the region your cluster is in. If you don't, the workflow
  is going to be slow and additional data transfer charges will be incurred.
  The part after that (`jvivian-example-run-1`) is a matter of choice, but be
  sure to prefix it with your name so we can track which job store belongs to
  which user.

## 5) Appendix

### Choosing a spot market price

In the CGCloud `grow-cluster` command, we added two optional arguments:
`--spot-auto-zone` and `--spot-bid <PRICE>`. Clusters can be run not on the
spot market, but it is much cheaper to do so and should be done whenever
possible.

At the EC2 console on AWS, click the **Spot Requests** link on the left-hand
side of the page. Then click on **Pricing History** and select the instance
type you're interested in, which is typically the **c3.8xlarge** or
**r3.8xlarge**.

A general rule of thumb is to look at a day or a couple days' worth of prices
and select a price that is lower than the [on-demand
price](https://aws.amazon.com/ec2/pricing/) but high enough above the spot
market price that your'e not at risk of getting your nodes shut down.

### Handling Errors

If a pipeline finishes and said there were failed jobs, then investigate the
logfile on the leader:

- `less 1.log`

- Type the forward slash `/` and then `TOIL` and hit enter. This will take you
  to the first error log.

- See if you can determine why the sample failed. If the error appears to have
  a non-deterministic cause, like an HTTP error, then restarting the pipeline
  is the optimal option.

- Rerun the `toil-rnaseq run ...` command from above, but add the `--restart`
  flag and change the log name to `2.log`.

If the issue looks like it is systemic but based on resources (not enough
memory or not enough disk), then please change the instance type to something
that is appropriate for the size of the sample you are trying to run, or
increase the size of the `disk` config option.
 
If the pipeline fails despite a `--restart` attempt, please copy the entire
error message into a ticket. Include the config and manifest and if possible
the path to the sample that failed.
