#!/usr/bin/perl

my $indent = 0;

my %terrain = ();

while (<>) {
	next unless /^.+?EVENT .(\d+)\.(\d+)\.(\d+).:provsetup: PROV(\d+): (.+)$/;
	my ($y, $m, $d, $id, $t) = ($1, $2, $3, 0+$4, $5);
	$t =~ s/\r//g;
	$terrain{$id} = $t;
}

for my $id (sort { $a <=> $b } keys %terrain) {
	print "$id=$terrain{$id}\n";
}
