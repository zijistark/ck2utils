#!/usr/bin/perl

######## WORK IN PROGRESS -- NOT FIT FOR USE -- WON'T WORK OR WILL BE USELESS ##########

use strict;
use warnings;
use Carp;
use List::Util qw(max reduce sum);

my $LOG_DIR = "/cygdrive/c/Users/$ENV{USER}/Documents/Paradox Interactive/Crusader Kings II/logs";
my $WIDTH = 120;

my $log_leaf = (@ARGV) ? shift @ARGV : 'error.log';
my $log_file = "$LOG_DIR/$log_leaf";
croak "file not found: $log_file" unless -e $log_file;

my @title_missing_loc;
my %title_missing_loc_ignore = ('---' => 1);
my @char_dup_id;
my @char_bad_birthdeath_dates;
my @char_invalid_in_title_history;
my @char_bad_spouse;
my @char_bad_father;
my @char_bad_mother;
my @char_male_mom;
my @char_female_dad;
my @char_samesex_spouse;
my @title_unlanded_char;
my @prov_setup_bad_title;
my @prov_setup_bad_max_settlements;
my @title_holder_unborn;
my @title_redefined;
my @region_bad_elem;
my @region_mult_elem;
my @prov_bad_barony;

my @unrecognized_lines = (); # that weren't filtered due to being uninteresting

open(my $f, '<:crlf', $log_file) or croak "open: $!: $log_file";
my $n_line = 0;

while (<$f>) {
	++$n_line;
	next if /^\s*$/;
	next if /^\*+$/;
	next if /^\[internationalizedtext\.cpp:/;
	next if /Terrain for \d+ does not correspond to history.$/;
	next if /"Duchy defined in region not found. See log."$/;
	next if /"Region have multiple entries of the same province!"$/;

	if (/Missing localization for ([\w-]+)$/) {
		next if exists $title_missing_loc_ignore{$1};
		push @title_missing_loc, [$1,];
	}
	elsif (m|Invalid character (\d+) in history/titles/([\w-]+)\.txt$|) {
		push @char_invalid_in_title_history, [$1, $2];
	}
	elsif (/Duplicate Historical Character! ID:(\d+)$/) {
		push @char_dup_id, [$1];
	}
	elsif (/SERIOUS: Bad Birth and Death dates for character: (.+?) \((\d+)\)$/) {
		push @char_bad_birthdeath_dates, [$2, $1];
	}
	elsif (/Tried to marry wife that does not exist. ID:(\d+) tried to marry ID: (\d+)$/) {
		push @char_bad_spouse, [$1, $2];
	}
	elsif (/Bad Father for character: (.+?) \((\d+)\)$/) {
		push @char_bad_father, [$2];
	}
	elsif (/Bad Mother for character: (.+?) \((\d+)\)$/) {
		push @char_bad_mother, [$2];
	}
	elsif (/Character ID:(\d+) has a female father!$/) {
		push @char_female_dad, [$1];
	}
	elsif (/Character ID:(\d+) has a male mother!$/) {
		push @char_male_mom, [$1];
	}
	elsif (/Same sex marriage. ID:(\d+) is married to ID: (\d+)$/) {
		push @char_samesex_spouse, [$1, $2];
	}
	elsif (/Character ID:(\d+) holds title '([\w-]+)', but no baronies!$/) {
		push @title_unlanded_char, [$2, $1];
	}
	elsif (/Barony '([\w-]+)' in the wrong province: (.+)$/) {
		push @prov_bad_barony, [$2, $1];
	}
	elsif (m|Error in common/province_setup/([\w \.+-]*?): Title for (\d+) does not correspond to history.$|) {
		push @prov_setup_bad_title, [$2, $1];
	}
	elsif (m|Error in common/province_setup/([\w \.+-]*?): Max settlements for (\d+) does not correspond to history.$|) {
		push @prov_setup_bad_max_settlements, [$2, $1];
	}
	elsif (m{Bad capital title '([\w-]+)' in province (\d+)$}) {
		# uh, placeholder until I know what that means
		push @unrecognized_lines, $_;
	}
	elsif (m{(?:duchy|county|province) '?([\w\-]+)'? defined in region '([\w\-]+)' not found$}i) {
		push @region_bad_elem, [$2, $1];
	}
	elsif (m{Region '([\w\-]+)' have multiple entries for the (?:duchy|county|province) '([\w\-]+)'$}i) {
		push @region_mult_elem, [$1, $2];
	}
	elsif (/Unborn title holder$/) {
		my $line = get_line($f);
		$line =~ m|^\tTitle: ([\w-]+)\(|;
		my $title = $1;
		$line = get_line($f);
		$line =~ m|^\tDate: ([\d\.]+)$|;
		my $date = $1;
		$line = get_line($f);
		$line =~ m|^\tCharacter ID: (\d+), Birth date: ([\d\.]+)$|;
		my ($char, $birthdate) = ($1, $2);
		push @title_holder_unborn, [$char, $title, $date, $birthdate];
	}
	elsif (/Title Already Exists!$/) {
		my $line = get_line($f);
		$line =~ m|^\tTitle: ([\w-]+)$|;
		my $title = $1;
		$line = get_line($f);
		$line =~ m|^\tLocation: common/landed_titles/([\w \.+-]*?)\((\d+)\)$|;
		push @title_redefined, [$title, $1, $2];
	}
	else {
		push @unrecognized_lines, $_;
	}
}

$f->close;

my $old_fh = select STDERR;
print @unrecognized_lines;
select $old_fh;

sub markup_province {
	($_[0] =~ /^\d+$/) ? "province_id[$_[0]]" : $_[0];
}

sub aligned_date {
	my ($y, $m, $d) = split(/\./, $_[0]);
	sprintf("%4s.%2s.%2s", $y, $m, $d);
}

print_data_tables({
	title => "duplicate character ID",
	data => \@char_dup_id,
	suppress_header => 1,
	severity => 2,
	cols => [
		{
			title => "Character ID",
			left_align => 1,
		},
	],
},
{
	title => "character has invalid birth/death dates",
	data => \@char_bad_birthdeath_dates,
	severity => 2,
	cols => [
		{
			title => "Character ID",
		},
		{
			title => "Name",
			left_align => 1,
		},
	],
},
{
	title => "province has out-of-place barony",
	data => \@prov_bad_barony,
	severity => 2,
	cols => [
		{
			title => "Province Name",
		},
		{
			title => "Barony Title",
			left_align => 1,
		},
	],
},
{
	title => "invalid character in title history",
	data => \@char_invalid_in_title_history,
	severity => 2,
	numeric_sort => 1,
	cols => [
		{
			title => "Character ID",
		},
		{
			title => "Title",
			left_align => 1,
		},
	],
},
{
	title => "province setup: incorrect title",
	data => \@prov_setup_bad_title,
	severity => 2,
	numeric_sort => 1,
	cols => [
		{
			title => "Province ID",
			left_align => 1,
		},
	],
},
{
	title => "province setup: incorrect max_settlements",
	data => \@prov_setup_bad_max_settlements,
	severity => 1,
	numeric_sort => 1,
	cols => [
		{
			title => "Province ID",
			left_align => 1,
		},
	],
},
{
	title => "titles missing localisation",
	data => \@title_missing_loc,
	severity => 1,
	suppress_header => 1,
	cols => [
		{
			title => "Title",
			left_align => 1,
		},
	],
},
{
	title => "regions with undefined titles",
	data => \@region_bad_elem,
	severity => 1,
	cols => [
		{
			title => "Region",
		},
		{
			title => "Title",
			left_align => 1,
		},
	],
},
{
	title => "regions with repeated elements",
	data => \@region_mult_elem,
	cols => [
		{
			title => "Region",
		},
		{
			title => "Element",
			left_align => 1,
			observer => \&markup_province,
		},
	],
},
{
	title => "invalid spouse for character",
	data => \@char_bad_spouse,
	numeric_sort => 1,
	cols => [
		{
			title => "Character ID",
		},
		{
			title => "Spouse ID",
			left_align => 1,
		},
	],
},
{
	title => "character has same-sex marriage",
	data => \@char_samesex_spouse,
	numeric_sort => 1,
	cols => [
		{
			title => "Character ID",
		},
		{
			title => "Spouse ID",
			left_align => 1,
		},
	],
},
{
	title => "invalid father for character",
	data => \@char_bad_father,
	numeric_sort => 1,
	suppress_header => 1,
	cols => [
		{
			title => "Character ID",
			left_align => 1,
		},
	],
},
{
	title => "invalid mother for character",
	data => \@char_bad_mother,
	numeric_sort => 1,
	suppress_header => 1,
	cols => [
		{
			title => "Character ID",
			left_align => 1,
		},
	],
},
{
	title => "character has female father",
	data => \@char_female_dad,
	numeric_sort => 1,
	suppress_header => 1,
	cols => [
		{
			title => "Character ID",
			left_align => 1,
		},
	],
},
{
	title => "character has male mother",
	data => \@char_male_mom,
	numeric_sort => 1,
	suppress_header => 1,
	cols => [
		{
			title => "Character ID",
			left_align => 1,
		},
	],
},
{
	title => "landed title held by character with no demesne",
	data => \@title_unlanded_char,
	cols => [
		{
			title => "Title",
		},
		{
			title => "Character ID",
			left_align => 1,
		},
	],
},
{
	title => "title holder not yet born",
	data => \@title_holder_unborn,
	numeric_sort => 1,
	cols => [
		{
			title => "Character ID",
		},
		{
			title => "Title",
			left_align => 1,
		},
		{
			title => "Date Held",
			left_align => 1,
			observer => \&aligned_date,
		},
		{
			title => "Date Born",
			left_align => 1,
			observer => \&aligned_date,
		},
	],
},
{
	title => "title redefinitions",
	data => \@title_redefined,
	severity => -1,
	cols => [
		{
			title => "Title",
		},
		{
			title => "Filename",
		},
		{
			title => "Line",
			left_align => 1,
		},
	]
});

exit 0;

########

sub print_data_tables {
	my @tables = @_;
	my %num_errs_by_severity = map { $_ => 0 } (-1..2);
	my $num_errs = 0;

	map {
		$_->{severity} = 0 unless defined $_->{severity};
		my $sev = ($_->{severity} == 2) ? " (!!)" :
				  ($_->{severity} == 1) ? " (!)" :
				  ($_->{severity}  < 0) ? " (?)" : "";
		$_->{title} = "$_->{title}$sev" if $sev;
		$num_errs_by_severity{ $_->{severity} } += scalar @{ $_->{data} };
		$num_errs += scalar @{ $_->{data} } if $_->{severity} >= 0;
	} @tables;

	print "(!!) Errors requiring immediate attention: $num_errs_by_severity{2}\n";
	print " (!) Errors (high priority): $num_errs_by_severity{1}\n";
	print "     Errors (normal): $num_errs_by_severity{0}\n";
	print " (?) Warnings: $num_errs_by_severity{-1}\n";
	print "\nTotal errors: $num_errs\n";

	for my $tbl (sort { $b->{severity} <=> $a->{severity} } grep { @{$_->{data}} } @tables) {
		print_data_table(%$tbl);
	}
}

sub print_data_table {
	my %tbl = @_;
	return unless @{ $tbl{data} };

	my @cols = @{ $tbl{cols} };
	map { $_->{maxlen} = length $_->{title} } @cols;
	map { $_->{pad} = 0 } @cols;

	for my $row (@{ $tbl{data} }) {
		for my $i (0..$#cols) {
			my $c = $cols[$i];
			$row->[$i] = (defined $c->{observer}) ? &{$c->{observer}}( $row->[$i] ) : $row->[$i];
			$c->{maxlen} = max $c->{maxlen}, length $row->[$i];
		}
	}

	my $caption = " \U$tbl{title} ";
	my $caption_len = length $caption;
	my $data_width = -1 + sum map { $_->{maxlen} + 2 + 1 } @cols;

	if ($caption_len > $data_width) {
		my $caption_excess = $caption_len - $data_width;
		my $caption_excess_per_col = int($caption_excess / scalar @cols);
		my $caption_excess_remainder = $caption_excess % scalar @cols;

		for my $c (@cols) {
			$c->{pad} += $caption_excess_per_col;

			if ($caption_excess_remainder > 0) {
				--$caption_excess_remainder;
				++$c->{pad};
			}
		}

		$data_width = $caption_len;
	}

	my $caption_pad = $data_width - $caption_len;
	my $caption_pad_left = $caption_pad / 2;
	my $caption_pad_right = $caption_pad_left + $caption_pad % 2;

	print "\n/", '-' x $data_width, "\\\n";
	print "|", ' ' x $caption_pad_left, $caption, ' ' x $caption_pad_right, "|\n";

	my $sep_line = reduce { "$a".('-' x ($b->{maxlen} + $b->{pad} + 2)).'+' } '+', @cols;

	my $hdr_line = '|';

	for my $c (@cols) {
		my $pt = " \u$c->{title} ";
		my $align_char = '';
		$align_char = '-' if defined $c->{left_align};
		$hdr_line .= sprintf("%$align_char*s|", $c->{maxlen} + $c->{pad} + 2, $pt);
	}

	print "$sep_line\n";

	unless (exists $tbl{suppress_header} && $tbl{suppress_header}) {
		print "$hdr_line\n";
		print "$sep_line\n";
	}

	my $row_fmt = '|';

	for my $c (@cols) {
		my $align = $c->{maxlen} + $c->{pad};
		$align = '-'.$align if defined $c->{left_align};
		$row_fmt .= ' %'.$align.'s |';
	}

	$row_fmt .= "\n";

	my @rows = (exists $tbl{numeric_sort} && $tbl{numeric_sort})
		? sort { 0+$a->[0] <=> 0+$b->[0] } @{ $tbl{data} }
		: sort { $a->[0] cmp $b->[0] } @{ $tbl{data} };

	my $last_key = '';

	for my $row (@rows) {
		no warnings;

		my $k = shift @$row;
		printf($row_fmt, ((scalar @cols > 1 && $last_key && $last_key eq $k) ? '' : $k), @$row);
		$last_key = $k;
	}

	print "\\", '-' x $data_width, "/\n";
}


sub get_line {
	my $fh = shift;
	defined(my $line = <$fh>) or croak "unexpected EOF or I/O error on input line $n_line: $!";
	++$n_line;
	return $line;
}
