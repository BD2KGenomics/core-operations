# rnaseq workflow

This is a description of how to run the rnaseq-cgl toil workflow v2.0.10 on a toil cluster with toil v 3.3.3  on the Amazon cloud.

For details on the workflow itself, see [the manual](https://github.com/BD2KGenomics/cgl-docker-lib/tree/master/rnaseq-cgl-pipeline)

## Inputs

The workflow needs two input files: a `config` and a `manifest`. The standard config for a production run can be found [here](mustfillin).

The only change that _must_ be made in the `config` file is the s3 output location (see NAMING CONVENTIONS below).
The `manifest` file lists inputs and must be created for each run and stored in this github repository.

Input data is in `fastq` format and can be single ended or (usually) paired. A single sample may contain multiple (paired) fastq files, and if this is the case, input must be tarred. The manifest then looks like this:
```
tar     paired  <SAMPLE ID>     s3://cgl-driver-projects-encrypted/<GROUP>/<SAMPLE>_input/<NAME>.tar
```
where the input is tab separated.

Likewise, if the sample data is single ended and tarred:
```
tar     single  <SAMPLE ID>     s3://cgl-driver-projects-encrypted/<GROUP>/<SAMPLE>_input/<NAME>.tar
```
If there is just one single ended fastq for a sample, it does not have to be tarred:
```
fq     single  <SAMPLE ID>     s3://cgl-driver-projects-encrypted/<GROUP>/<SAMPLE>_input/<NAME>.fq
```
(can also be gzipped fastq, in which case the filename will be `<NAME>.fq.gz` or `<NAME>.fastq.gz`)

Paired samples must be comma separated and there can't be more than two:
```
fq     single  <SAMPLE ID>     s3://cgl-driver-projects-encrypted/<GROUP>/<SAMPLE>_input/<NAME_1>.fq.gz,s3://cgl-driver-projects-encrypted/<GROUP>/<SAMPLE>_input/<NAME_2>.fq.gz
```

## Getting input data from requester

The requester will typically upload their tarred files to one of our `s3 inbox` locations, using a new key that they then share with us.

We move these files to one of our cgl-driver-projects-encrypted locations and re-encrypt them using `s3am`.
In the example below, the inbox is `cgl-inbox-su2c-ucsf-rnaseq` and the final input location is under `ucsf-pnoc`:
```
s3am upload --src-sse-key-file ./20160713.key --sse-key-file ./master.key --sse-key-is-master --download-slots 40 --upload-slots 40 --part-size 50M s3://cgl-inbox-su2c-ucsf-rnaseq/<NAME>.tar s3://cgl-driver-projects-encrypted/ucsf-pnoc/ucsf_issue53_input/<NAME>.tar
```

## Record keeping

Production runs are currently tracked via github:
```
git clone https://github.com/BD2KGenomics/core-operations.git
```

Each production run gets its own github ticket ([example]( https://github.com/BD2KGenomics/core-operations/issues/53)) before the run starts.

The ticket is used to keep track of file upload, transfer, and run details. It gets closed once the run finishes successfully.

The ticket name contains the requester ID (`ucsf-pnoc`, for instance) and the name of the workflow (`rna-seq`) and matches the corresponding manifest file in the repository.
For instance, ticket 53 is named `WCDT/medbook_UCSF_RNA-seq.20160714.53`

Each collaborator has their own subdirectory in the repository (CKCC, WCDT, etc) and a copy of the manifest file is kept inside it. Every run gets its own ticket, and the ticket number becomes part of the file name:
```
ckcc_PNOC_WXS.20160301.21.input.txt
stanford-rnaseq-20160417.35.input.txt
```
This corresponds to https://github.com/BD2KGenomics/core-operations/blob/master/WCDT/medbook_UCSF_RNA-seq.20160714.53.input.txt

In the top directory is a file named `dashboard.txt`. Add the manifest, the date, and any progress notifications:
```
20160629 CKCC/all.rnaseq.bam.redo.20160629.50.input.txt Entered
20160630 CKCC/all.rnaseq.bam.redo.20160629.50.input.txt Started
20160701 CKCC/all.rnaseq.bam.redo.20160629.50.input.txt 55 of 74 finished
20160705 CKCC/all.rnaseq.bam.redo.20160629.50.input.txt Corrected input, restarted
20160706 CKCC/all.rnaseq.bam.redo.20160629.50.input.txt 68 of 74 finished, corrected input, restarted
20160707 CKCC/all.rnaseq.bam.redo.20160629.50.input.txt Completed
```
*Note that every entry starts with the date*

Then `git add`, `git commit`, and `git push`. Keep more detailed notes in the corresponding ticket to keep collaborators updated

## Naming Conventions

Like the git tickets, the input and output locations on `s3` also follow rules. Inputs are all in `cgl-driver-projects-encrypted`, under the requester ID, in a subdirectory withe ticket number, for instance
```
s3://cgl-driver-projects-encrypted/ucsf-pnoc/ucsf_issue53_input
```
Outputs are put in
```
s3://cgl-driver-projects/ucsf-pnoc/ucsf_issue53_output
```
*Note that you must create this output directory before the run, and list it in the config file.*

## Set up CGCLOUD

`cgcloud` is needed to set up a cluster on the Amazon cloud with `toil` and other necesities installed
For details see [the documentation](
https://github.com/BD2KGenomics/cgcloud/blob/master/core/README.rst)

I usually run this from a VM, so here are instructions for a full install with the dependencies:

(**you only need to do this once**)
```
sudo apt-get install libffi-dev
sudo apt-get install libyaml-dev
virtualenv cgcloud
source cgcloud/bin/activate
pip install --upgrade pip
pip install pycrypto
pip install cgcloud-core
pip install cgcloud-toil
```

Then add these to .bashrc:
```
export CGCLOUD_ZONE=us-west-2a
export CGCLOUD_PLUGINS="cgcloud.toil:$CGCLOUD_PLUGINS"
export CGCLOUD_NAMESPACE=/yourname/  # this must be something without underscores or periods
```
create a `ssh key pair` using `ssh-keygen`. This will be used in creating the cluster.

Before you create your first cluster,  you must create a master image:
```
cgcloud create -IT toil-box
And register your key:
cgcloud register-key ~/.ssh/id_rsa.pub
```

(**end of one off instructions**)

I find that I have to run the below every time I log on to the VM:
```
kill $(ps -ef | grep agent | awk  '{print $2}')
eval "$(ssh-agent )"
ssh-add ~/.ssh/id_rsa
```

This lets you interact with the cluster without having to type a password.

## Creating a cluster

First, create a `~/shared` directory from your launch box that contains the `config` and `manifest files`, as well as the `master.key`.

To create a cluster it is recommended to find out the *spot market price*:

Log on to the `EC2 dashboard` and select `Spot Requests` in the left side bar.
Click on the `launch wizard`, and then select `Cancel` at the bottom of the next page.
Then, at the top of the resulting page, select `Pricing History` and check `c3.8xlarge` and `r3.8xlarge` (separately). Make sure at least one of them has
stayed below `$0.6` for a while. The zoning (2a, b, c) does not matter, because `cgcloud` will automatically select the best one.

The number of workers needed is roughly 1 per 7 samples, or 30 nodes maximum. In the example below, I create 15 workers.
```
source cgcloud/bin/activate   # or wherever you put your virtualenv
cgcloud create-cluster --leader-instance-type m3.medium -D --instance-type c3.8xlarge --share shared/ --spot-auto-zone --spot-bid 1 -s 15 --cluster-name <issueNR> toil
```

Keep watching while this runs - after the leader is created you will have to type `yes` once. After that you can walk away until
the setup is done (takes anywhere from 2 to 15 minutes)

Once the cluster has been created, tag the instances. In production runs, the tags are always `Key=ENV,Value=PROD Key=PURPOSE,Value=<requester ID`, e.g. CKCC).
```
aws --region us-west-2 ec2 describe-instances | grep -A3 InstanceId | grep -B3 <yourname> | grep InstanceId | cut -f4 -d'"' > instance.ids
for i in $(cat instance.ids); do aws --region us-west-2 ec2 create-tags --resource $i --tags Key=ENV,Value=PROD Key=PURPOSE,Value=CKCC; done
```
(You can install aws using `pip install awscli` if you're not on an Amazon VM)

Log on to the leader:
```
cgcloud ssh toil-leader
```
and get the toil scripts release in a `virtualenv`
```
virtualenv --system-site-packages toilscripts
source toilscripts/bin/activate
pip install toil-scripts
```
Do `pip list` to check that the toil-scripts release is `2.0.10` and toil is version `3.3.3`
I usually do `pip list > shared/piplist` to keep track

Then start a screen and from there start the run
```
source toilscripts/bin/activate
toil-rnaseq run aws:us-west-2:<yourname>-rnaseq-<issuenr> --batchSystem=mesos --mesosMaster mesos-master:5050 --config /home/mesosbox/shared/config.txt --manifest /home/mesosbox/shared/manifest.txt 2>&1 | tee shared/log
```
The `aws:us-west-2:<yourname>-rnaseq-<issuenr>` creates a bucket on `s3` for this run. If the run fails for any reason, this bucket can sometimes be used to restart it, but you are responsible for removing it afterwards. If necessary:
```
toil clean aws:us-west-2:<yourname>-rnaseq-<issuenr>
```
If the job runs without trouble, the bucket gets deleted automatically.

Watch for a while before you log off. If you see a lot of failed jobs, check if your workers are still up, for instance through the EC2 dashboard.
If you get overbid, Amazon kills your workers and you may have to add new ones from your launcing machine:
```
cgcloud grow-cluster --instance-type c3.8xlarge --spot-auto-zone --spot-bid 0.6  --num-workers 5 toil
```
Once you're convinced that things are running, you can exit the toil leader.
From your launching machine, you can check if your workers are still up by
```
cgcloud list toil-worker
```
To see if the run has finished, I log on to the leader and check the screen, and I go to `s3` and count the output files. The workflow copies out the final results as the very last step. Once the run is done, copy the log to your VM or wherever you keep your records.
Then terminate the cluster so it doesn't keep costing money:
```
cgcloud terminate-cluster toil
```
## Failed jobs

Unfortunately the current log is not set up to be very clear about what went wrong. For instance, `WARNING` and `ERROR` messages give the job ID but not the sample ID. Usually jobs in a batch fail for similar reasons, such as unpaired reads in the fastq files. This is why it's useful to let a run finish completely and check for missing outputs. If there are any, check the log for clues. At this point you might have to ask the developers for explanations.

If there are any reasons for a restart or troubles with the samples (read the log for details), put this in the ticket. That way you keep the requester and the production core updated on your progress.
## FINISHING UP

Attach the following files to the github ticket
- piplist
- config file
- log file

Also note the toil and toil-scripts versions in the ticket (`2.0.10` and `3.3.3` as of this writing)













