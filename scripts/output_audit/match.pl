use strict;
use Data::Dumper;

# cat all.input.txt | perl match.pl

my $d = {};
my $d2 = {};

while(<>) {
  chomp;
  $_ =~ /\/([^\/]+)$/;
  $d2->{$1} = 1;
}

my $lst = `aws s3 ls s3://cgl-driver-projects --recursive | awk '{print "s3://cgl-driver-projects/" \$4}'`;
my @arr = split /\n/, $lst;
foreach my $key (keys %{$d2}) {
  foreach my $list_val (@arr) {
    if ($list_val =~ /$key/) { push @{$d->{$key}}, $list_val; }
  }
}

foreach my $key (keys %{$d2}) {
  if (defined $d->{$key}) { print "$key\t".join("\t", @{$d->{$key}})."\n"; }
  else { print "$key\tMISSING\n"; }
}
