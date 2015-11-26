#!/usr/bin/perl

my $ml = 0;

while (<>) {
	next unless /^.+?EVENT .(\d+)\.(\d+)\.(\d+).:(.+)$/;
	my ($y, $m, $d, $msg) = ($1, $2, $3, $4);
	
	if ($msg =~ '>>>') {
		$ml = 0;
		next;
	}
	elsif ($msg =~ '<<<') {
		$ml = 1;
		next;
	}
	
	$msg = "\a$msg" if ($msg =~ 'ASSERT' || $msg =~ 'SERIOUS' || $msg =~ 'ERROR');
	
	if ($ml) {
		print "> $msg\n";
	}
	else {
		printf("%d.%02d.%02d> %s\n", $y, $m, $d, $msg);
	}
}
