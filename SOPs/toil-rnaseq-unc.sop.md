Steps to run the RNA-seq UNC pipeline vs the RNA-seq CGL pipeline

Setup the cluster the same way, but instead of needing a venv and pip installing toil-scripts, 
`git clone toil-scripts -b releases/2.0.x`
you'll also need to use `cgcloud ssh-cluster` to `pip uninstall toil` and reinstall `pip install toil==3.1.6` to all the nodes
 
There is a convenience script for running on mesos, which you'll edit to change bucket other settings etc.  
The config you create (there is an example in the directory), must be on every machine, so you'll use the `--share` 
option and pass in a location where that file is, which will be on `/home/mesosbox/shared`
You will also need to have the master key file in the shared directory

1) Setup CGCloud
See the SOP https://github.com/BD2KGenomics/core-operations/blob/master/SOPs/toil-rnaseq.sop.md
2) Launch a cluster
See the SOP https://github.com/BD2KGenomics/core-operations/blob/master/SOPs/toil-rnaseq.sop.md

#instead of section 3 and 4 in the toil-rnaseq.sop.md use the following:
3) Install and configure the pipeline
#ssh as administrator into the Toil leader (-a) so you can do sudo apt-get to install git
cgcloud ssh —a —-cluster-name example toil-leader
#install git on the leader
sudo apt-get install git
#exit out of the leader
exit

#grow the cluster
cgcloud grow-cluster --cluster-name example --spot-auto-zone --spot-bid 1.00 --instance-type c3.8xlarge --num-workers 22 toil

#remove current Toil from the leader and the workers
#use CGCloud to remove the current Toil version from the workers
cgcloud ssh-cluster --cluster-name example --admin toil -o StrictHostKeyChecking=no sudo pip uninstall -y toil

#install Toil version 3.1.6 on all the workers
cgcloud ssh-cluster --cluster-name example  --admin toil -o StrictHostKeyChecking=no sudo pip install toil==3.1.6

#install unzip and samtools because these are not installed by default
cgcloud ssh-cluster --cluster-name example --admin toil -o StrictHostKeyChecking=no sudo apt-get install -y unzip samtools

#log back into the Toil leader
cgcloud ssh --cluster-name example toil-leader

#clone the correct toil scripts repo
git clone https://github.com/BD2KGenomics/toil-scripts -b releases/2.0.x

#edit the launch script to make sure paths and options are setup correctly
#especially the location of the config file and the S3 output directory
vim /home/mesosbox/toil-scripts/src/toil_scripts/rnaseq_unc/launch_unc_mesos.sh
  #for example
  'aws:us-west-2:unc-run-1 \' -> 'aws:us-west-2:example-unc-run-1 \'
  '--s3_dir cgl-driver-projects/test/ \' -> '--s3_dir cgl-driver-projects-encrypted/wcdt/issue1111/output/ \'
#cd to the scripts directory
cd /home/mesosbox/toil-scripts/src/toil_scripts/rnaseq_unc
#set the script as executable
chmod 775 launch_unc_mesos.sh 

#turn off ‘Requester Pays’ on the Amazon S3 console so that downloads can occur
#(turn this back on after the run finishes downloading files)
go to the S3 console https://console.aws.amazon.com/s3/home?region=us-west-2
click on All Buckets
click on cgl-pipline-inputs
click on Properties
click on Requester Pays
uncheck the ‘Enable’ box 
click ’Save’

4) Run the pipeline
#start a screen session so we can log back in and see progress
screen -S myRNASeq-UNC-session

#run the launch script
./launch_unc_mesos.sh

#if a problem occurs and you need to restart
#add '--restart' to the end of the launch_unc_mesos.sh script and rerun the script
#or
#if you need to clean up all of the previous run
#do the following to clean up first (change to the appropriate region and run name)
toil clean 'aws:us-west-2:example-unc-run-1'
#and rerun the launch_unc_mesos.sh script

#after the run finishes or after downloads have occurred
#turn on ‘Requester Pays’ on the Amazon S3 console so that downloads can occur
go to the S3 console https://console.aws.amazon.com/s3/home?region=us-west-2
click on All Buckets
click on cgl-pipline-inputs
click on Properties
click on Requester Pays
check the ‘Enable’ box 
click ’Save’

