#!/usr/bin/perl

my $indent = 0;

while (<>) {
	next unless /^.+?EVENT .(\d+)\.(\d+)\.(\d+).:(.+)$/;
	my ($y, $m, $d, $msg) = ($1, $2, $3, $4);
	
	if ($msg =~ '>>>') {
		--$indent;
		next;
	}
	if ($msg =~ '<<<') {
		++$indent;
		next;
	}
	
	$msg = "\a$msg" if ($msg =~ 'ASSERT' || $msg =~ 'SERIOUS' || $msg =~ 'ERROR');
	
	if ($indent) {
		print(('>' x $indent), " $msg\n");
	}
	else {
		printf("%d.%02d.%02d> %s\n", $y, $m, $d, $msg);
	}
}
