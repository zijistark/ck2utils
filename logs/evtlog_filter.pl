#!/usr/bin/perl

my $ml = 0;

while (<>) {
	next unless /^.+?EVENT .([^]]+).:(.+)$/;
	my ($date, $msg) = ($1, $2);
	
	if ($msg =~ '>>>') {
		$ml = 0;
		next;
	}
	elsif ($msg =~ '<<<') {
		$ml = 1;
		next;
	}
	
	print(($ml) ? $msg : "$date> $msg", "\n");
}
