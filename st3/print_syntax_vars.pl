#!/usr/bin/perl

use strict;
use warnings;
use Carp;
use File::Basename qw(fileparse);

my @files = sort { $a cmp $b } @ARGV;

for my $fn (@files)
{
    preprocess_file($fn);
    my ($base, $dirs, $suffix) = fileparse($fn, '.txt');

    open(my $f, '<', $fn) or croak $!;
    my $first = 1;

    print "  v$base: |-\n";
    print "    (?xi:\n";
    while (<$f>) {
        s/\s*\#.*$//;
        my $indent = '    | ';
        if ($first)
        {
            $indent = '      ';
            $first = 0;
        }
        print $indent.$_;
    }
    print "    )\n";
}

sub preprocess_file
{
    my $fn = shift;
    my $fn_t = $fn.".tmp";

    my %kw = ();
    open(my $f, '<', $fn) or croak $!;
    open(my $ft, '>', $fn_t) or croak $!;

    while (<$f>)
    {
        s/\r\n//;
        s/^\s*//;
        s/\s*$//;
        next if /^\s*$/;
        $kw{"$_"} = 1;
    }

    for my $k (sort { $a cmp $b } keys %kw)
    {
        $ft->print("$k\n");
    }

    $f->close;
    $ft->close;
    unlink $fn or croak $!;
    rename $fn_t, $fn or croak $!;
}
