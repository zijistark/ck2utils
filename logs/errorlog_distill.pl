#!/usr/bin/perl

######## WORK IN PROGRESS -- NOT FIT FOR USE -- WON'T WORK OR WILL BE USELESS ##########

use strict;
use warnings;
use Carp;
use List::Util qw(max reduce sum);

my $LOG_DIR = "/cygdrive/c/Users/$ENV{USER}/Documents/Paradox Interactive/Crusader Kings II/logs";
my $WIDTH = 120;

# these turn on extra filters for ignoring certain file patterns for certain error/warning types, but they're not required:
my $EMF_V = 0;
my $EMF_S = 0;
my $SWMH = 1;
croak "only one of \$EMF_V, \$EMF_S, and \$SWMH may be enabled" if ($EMF_V && $EMF_S || $EMF_V && $SWMH || $EMF_S && $SWMH);

my $log_leaf = (@ARGV) ? shift @ARGV : 'error.log';
my $log_file = "$LOG_DIR/$log_leaf";
croak "file not found: $log_file" unless -e $log_file;

my @title_missing_loc;
my @title_unlanded_char;
my @title_holder_unborn;
my @title_redefined;
my @title_missing_tech_seed;
my @char_dup_id;
my @char_bad_birthdeath_dates;
my @char_invalid_in_title_history;
my @char_bad_spouse;
my @char_bad_father;
my @char_bad_mother;
my @char_bad_religion;
my @char_bad_culture;
my @char_male_mom;
my @char_female_dad;
my @char_samesex_spouse;
my @char_bad_dynasty;
my @char_bad_trait;
my @char_bad_employer;
my @char_dead;
my @char_bad_trait_removal;
my @char_polyandry; #NEW
my @dynasty_bad_coa;
my @region_bad_elem;
my @region_mult_elem;
my @prov_setup_bad_title;
my @prov_setup_bad_max_settlements;
my @prov_bad_barony;
my @prov_too_full;
my @prov_bad_capital;
my @prov_bad_rm_barony;
#my @prov_bad_command;
my @barony_building_missing_prereq;
my @barony_building_not_potential;
my @event_bad_picture;
my @event_no_picture;
my @event_bad_on_action;
my @assert_culture;
my @assert_culture_group;
my @assert_title;
my @assert_undefined_event;
my @bad_token;
my @bad_trigger;
my @bad_effect;

my @unrecognized_lines = (); # that weren't filtered due to being uninteresting

my %title_missing_loc_ignore = (
	'---' => 1
);
my @title_redefined_ignored_file = (
	qr/z_holy_sites/i,
	qr/zz_emf_heresy/i,
	qr/zz_emf_magyar/i,
);
my @assert_culture_ignored_file = (
#	qr/00_customizable_localisation_/,
	qr/achievement_events\.txt/,
	qr/achievements\.txt/,
);
my @assert_title_ignored_file = (
	qr/00_customizable_localisation_/,
	qr/achievement_events\.txt/,
	qr/achievements\.txt/,
);

if ($EMF_V) {
	push @assert_culture_ignored_file, qr/castleculture/i;
	push @assert_culture_ignored_file, qr/tribalculture/i;
	push @assert_culture_ignored_file, qr/combat_tactics/i;
	push @assert_culture_ignored_file, qr/retinue_subunits/i;
}
elsif ($EMF_S) {
	push @title_redefined_ignored_file, qr/color_overrides/i;
	push @title_redefined_ignored_file, qr/name_tier_overrides/i;
}

open(my $f, '<:crlf', $log_file) or croak "open: $!: $log_file";
my $n_line = 0;
my $in_tech_seed = 0;

while (<$f>) {
	++$n_line;
	next if /^\s*$/;
	next if /^\*+$/;
	next if /^\[internationalizedtext\.cpp:/;
	next if /Terrain for \d+ does not correspond to history.$/;
	next if /"Duchy defined in region not found. See log."$/;
	next if /"Region have multiple entries of the same province!"$/;
	next if /Error create vertices [\d\-]+ [\d\-]+ [\d\-]+ [\d\-]+$/;
	next if /^\[gfx_dx9\.cpp:1493\]: managed$/;

	if ($in_tech_seed) {
		if (m{^\[technology.cpp:\d+\]: ([bcdek]_[\w\-]+)$}i) {
			push @title_missing_tech_seed, [$1,];
			next;
		}
		else {
			$in_tech_seed = 0;
		}
	}
	elsif (/Missing Tech seed values/i) {
		$in_tech_seed = 1;
	}
	elsif (m{Missing localization for ([\w-]+)$}i) {
		next if exists $title_missing_loc_ignore{$1};
		push @title_missing_loc, [$1,];
	}
	elsif (m{Character ID:(\d+) holds title '([\w-]+)', but no baronies!$}i) {
		push @title_unlanded_char, [$2, $1];
	}
	elsif (/Unborn title holder$/i) {
		my $line = get_line($f);
		$line =~ m{^\tTitle: ([\w-]+)\(}i;
		my $title = $1;
		$line = get_line($f);
		$line =~ m{^\tDate: ([\d\.]+)$}i;
		my $date = $1;
		$line = get_line($f);
		$line =~ m{^\tCharacter ID: (\d+), Birth date: ([\d\.]+)$}i;
		my ($char, $birthdate) = ($1, $2);
		push @title_holder_unborn, [$char, $title, $date, $birthdate];
	}
	elsif (/Title Already Exists!$/i) {
		my $line = get_line($f);
		$line =~ m{^\tTitle: ([\w-]+)$}i;
		my $title = $1;
		$line = get_line($f);
		$line =~ m{^\tLocation: common/landed_titles/([\w \.+-]+?)\s*\((\d+)\)$}i;
		my $fn = $1;
		next if grep { $fn =~ $_ } @title_redefined_ignored_file;
		push @title_redefined, [$title, $fn, $2];
	}
	elsif (m{Invalid character (\d+) in history/titles/([\w\-]+)\.txt$}i) {
		push @char_invalid_in_title_history, [$1, $2];
	}
	elsif (m{Duplicate Historical Character! ID:(\d+)$}i) {
		push @char_dup_id, [$1,];
	}
	elsif (m{Bad Birth and Death dates for character: (.+?) \((\d+)\)$}i) {
		push @char_bad_birthdeath_dates, [$2, $1];
	}
	elsif (m{Tried to marry wife that does not exist. ID:(\d+) tried to marry ID: (\d+)$}i) {
		push @char_bad_spouse, [$1, $2];
	}
	elsif (m{Bad Father for character: (.+?) \((\d+)\)$}i) {
		push @char_bad_father, [$2];
	}
	elsif (m{Bad Mother for character: (.+?) \((\d+)\)$}i) {
		push @char_bad_mother, [$2];
	}
	elsif (m{Failed to read religionchange for character (\d+) to TAG: ([\w\-]+)$}i) {
		push @char_bad_religion, [$1, $2];
	}
	elsif (m{Failed to read culturechange for character (\d+) to TAG: ([\w\-]+)$}i) {
		push @char_bad_culture, [$1, $2];
	}
	elsif (m{Character ID:(\d+) has a female father!$}i) {
		push @char_female_dad, [$1];
	}
	elsif (m{Character ID:(\d+) has a male mother!$}i) {
		push @char_male_mom, [$1];
	}
	elsif (m{Same sex marriage. ID:(\d+) is married to ID: (\d+)$}i) {
		push @char_samesex_spouse, [$1, $2];
	}
	elsif (m{Reference to undefined trait.\s+file:\s+(.+) line: (\d+)$}i) {
		push @char_bad_trait, [$1, $2];
	}
	elsif (m{Reference to undefined dynasty.\s+file:\s+(.+) line: (\d+)$}i) {
		push @char_bad_dynasty, [$1, $2];
	}
	elsif (m{Setting employer of (.+) \( (\d+) \) to (.+) \( (\d+) \) who can't have a court$}i) {
		#push @char_bad_employer, [$1, $2, $3, $4];
		next;
	}
	elsif (m{[bcdek]_[\w\-]+\((\d+)\) holds title ([bcdek]_[\w\-]+) while scripted as DEAD in (\d+\.\d+\.\d+)$}i) {
		push @char_dead, [$1, $2, $3];
	}
	elsif (m{Trying to remove trait '([^']+)' despite character '(\d+)' not having it$}i) {
		push @char_bad_trait_removal, [$1, $2];
	}
	elsif (m{Polyandry not allowed. Female ID:(\d+) is married to more than one living male}i) {
		push @char_polyandry, [$1,];
	}
	elsif (m{Scripted Dynasty: ([^\s]+) has an invalid texture in their coat of arms, randomizing!$}i) {
		push @dynasty_bad_coa, [$1,];
	}
	elsif (m{Barony '([\w-]+)' in the wrong province: (.+)$}i) {
		push @prov_bad_barony, [$2, $1];
	}
	elsif (m{Error in common/province_setup/([\w \.+-]*?): Title for (\d+) does not correspond to history.$}i) {
		push @prov_setup_bad_title, [$2, $1];
	}
	elsif (m{Error in common/province_setup/([\w \.+-]*?): Max settlements for (\d+) does not correspond to history.$}i) {
		push @prov_setup_bad_max_settlements, [$2, $1];
	}
	elsif (m{Too many settlements added to province (.+)$}i) {
		push @prov_too_full, [$1,];
	}
	elsif (m{Bad capital title '([\w-]+)' in province (\d+)$}) {
		push @prov_bad_capital, [$2, $1];
	}
	elsif (m{Bad remove_settlement: '([^']+)' in province (\d+)$}) {
		push @prov_bad_rm_barony, [$2, $1];
	}
	elsif (m{Building '(.+)' constructed in '(.+)' while pre-requisite '(.+)' is missing$}i) {
		push @barony_building_missing_prereq, [$2, $1, $3];
	}
	elsif (m{Removed non-potential building from province! building: "(.+)", province: "(.+)"$}i) {
		push @barony_building_not_potential, [$2, $1];
	}
	elsif (m{(?:duchy|county|province) '?([\w\-]+)'? defined in region '([\w\-]+)' not found$}i) {
		push @region_bad_elem, [$2, $1];
	}
	elsif (m{Region '([\w\-]+)' have multiple entries for the (?:duchy|county|province) '([\w\-]+)'$}i) {
		push @region_mult_elem, [$1, $2];
	}
	elsif (m{Non-existent image for event picture '([^']+)'. (.+)$}i) {
		push @event_bad_picture, [$1, $2];
	}
	elsif (m{Event #(\d+) has no picture scripted in (.+)$}i) {
		push @event_no_picture, [$2, $1];
	}
	elsif (m{OnAction list is referencing invalid event! event: "([^"]+)", on_action: "([^"]+)"}i) {
		push @event_bad_on_action, [$1, $2];
	}
	elsif (m{"pCulture->IsValid\(\)", type: "\w+", location: " file: (.+) line: (\d+)"$}i) {
		my $fn = $1;
		next if grep { $fn =~ $_ } @assert_culture_ignored_file;
		push @assert_culture, [$fn, $2];
	}
	elsif (m{"pCultureGroup->IsValid\(\)", type: "\w+", location: " file: (.+) line: (\d+)"$}i) {
		my $fn = $1;
		next if grep { $fn =~ $_ } @assert_culture_ignored_file;
		push @assert_culture_group, [$fn, $2];
	}
	elsif (m{"pTitle->IsValid\(\)", type: "\w+", location: " file: (.+) line: (\d+)"$}i) {
		my $fn = $1;
		next if grep { $fn =~ $_ } @assert_title_ignored_file;
		push @assert_title, [$fn, $2];
	}
	elsif (m{Undefined event!, assert: "_pEvent", type: "\w+", location: " file: (.+) line: (\d+)"$}i) {
		push @assert_undefined_event, [$1, $2];
	}
	elsif (m{Error: "Unexpected token: (.+), near line: (\d+)" in file: "([^"]+)"$}i) {
		push @bad_token, [$3, $2, $1];
	}
	elsif (m{Unknown trigger-type: "([^"]+)" at\s+file: (.+) line: (\d+)$}i) {
		push @bad_trigger, [$1, $2, $3];
	}
	elsif (m{Unknown effect-type: "([^"]+)" at\s+file: (.+) line: (\d+)$}i) {
		push @bad_effect, [$1, $2, $3];
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
	($_[0] =~ /^\d+$/) ? "PROV($_[0])" : $_[0];
}

sub aligned_date {
	my ($y, $m, $d) = split(/\./, $_[0]);
	sprintf("%4s.%2s.%2s", $y, $m, $d);
}

sub event_file {
	my $fn = shift;
	$fn =~ s|^.+/(\w+)\.txt$|$1|i;
	return $fn;
}

print_data_tables({
	title => "landed title held by character with no actual land",
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
	title => "title missing technology seed",
	data => \@title_missing_tech_seed,
	suppress_header => 1,
	cols => [
		{
			title => "Title",
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
	title => "character has invalid religion",
	data => \@char_bad_religion,
	severity => 1,
	cols => [
		{
			title => "Character ID",
		},
		{
			title => "Religion",
			left_align => 1,
		},
	],
},
{
	title => "character has invalid culture",
	data => \@char_bad_culture,
	severity => 1,
	cols => [
		{
			title => "Character ID",
		},
		{
			title => "Culture",
			left_align => 1,
		},
	],
},
{
	title => "reference to undefined trait",
	data => \@char_bad_trait,
	cols => [
		{
			title => "Filename",
		},
		{
			title => "Line",
			left_align => 1,
		},
	],
},
{
	title => "reference to undefined dynasty",
	data => \@char_bad_dynasty,
	severity => 1,
	cols => [
		{
			title => "Filename",
		},
		{
			title => "Line",
			left_align => 1,
		},
	],
},
{
	title => "trait removed but never added",
	data => \@char_bad_trait_removal,
	cols => [
		{
			title => "Trait Name",
		},
		{
			title => "Character ID",
			left_align => 1,
		},
	],
},
{
	title => "character has invalid / non-ruler employer",
	data => \@char_bad_employer,
	cols => [
		{
			title => "Name",
		},
		{
			title => "ID",
			left_align => 1,
		},
		{
			title => "Employer",
		},
		{
			title => "Employer ID",
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
	title => "character dead when scripted to hold title",
	data => \@char_dead,
	severity => 1,
	numeric_sort => 1,
	cols => [
		{
			title => "Character ID",
		},
		{
			title => "Title",
		},
		{
			title => "Date",
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
	title => "female married to more than one living male",
	data => \@char_polyandry,
	numeric_sort => 1,
	suppress_header => 1,
	cols => [
		{
			title => "Female ID",
			left_align => 1,
		},
	],
},
{
	title => "dynasty has invalid texture in coat of arms",
	data => \@dynasty_bad_coa,
	cols => [
		{
			title => "Dynasty Name",
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
	title => "province has too many settlements",
	data => \@prov_too_full,
	severity => 1,
	cols => [
		{
			title => "Province Name",
		},
	],
},
{
	title => "province has bad capital barony",
	data => \@prov_bad_capital,
	severity => 0,
	numeric_sort => 1,
	cols => [
		{
			title => "Province ID",
		},
		{
			title => "Barony Title",
			left_align => 1,
		},
	],
},
{
	title => "attempted to remove invalid barony",
	data => \@prov_bad_rm_barony,
	severity => 0,
	numeric_sort => 1,
	cols => [
		{
			title => "Province ID",
		},
		{
			title => "Bad Barony Title",
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
	title => "building removed due to failing its potential trigger",
	data => \@barony_building_not_potential,
	cols => [
		{
			title => "Barony Title",
		},
		{
			title => "Building",
			left_align => 1,
		},
	],
},
{
	title => "event picture invalid",
	data => \@event_bad_picture,
	severity => 1,
	cols => [
		{
			title => "Invalid Picture ID",
		},
		{
			title => "Event",
			left_align => 1,
		},
	],
},
{
	title => "no picture scripted for event",
	data => \@event_no_picture,
	severity => 1,
	cols => [
		{
			title => "Event File",
			observer => \&event_file,
		},
		{
			title => "Raw Event ID",
			left_align => 1,
		},
	],
},
{
	title => "invalid event referenced by on_action",
	data => \@event_bad_on_action,
	severity => 1,
	cols => [
		{
			title => "Event ID",
		},
		{
			title => "OnAction",
			left_align => 1,
		},
	],
},
{
	title => "reference to undefined culture",
	data => \@assert_culture,
	severity => -1,
	cols => [
		{
			title => "Filename",
		},
		{
			title => "Line",
			left_align => 1,
		},
	],
},
{
	title => "reference to undefined culture group",
	data => \@assert_culture_group,
	severity => -1,
	cols => [
		{
			title => "Filename",
		},
		{
			title => "Line",
			left_align => 1,
		},
	],
},
{
	title => "reference to undefined title",
	data => \@assert_title,
	severity => -1,
	cols => [
		{
			title => "Filename",
		},
		{
			title => "Line",
			left_align => 1,
		},
	],
},
{
	title => "reference to undefined event",
	data => \@assert_undefined_event,
	severity => 1,
	cols => [
		{
			title => "Filename",
		},
		{
			title => "Line",
			left_align => 1,
		},
	],
},
{
	title => "invalid token",
	data => \@bad_token,
	severity => 2,
	cols => [
		{
			title => "Filename",
		},
		{
			title => "Line",
			left_align => 1,
		},
		{
			title => "Bad Token",
		},
	],
},
{
	title => "invalid trigger",
	data => \@bad_trigger,
	severity => 2,
	cols => [
		{
			title => "Bad Trigger",
		},
		{
			title => "Filename",
		},
		{
			title => "Line",
			left_align => 1,
		},
	],
},
{
	title => "invalid effect",
	data => \@bad_effect,
	severity => 2,
	cols => [
		{
			title => "Bad Effect",
		},
		{
			title => "Filename",
		},
		{
			title => "Line",
			left_align => 1,
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
