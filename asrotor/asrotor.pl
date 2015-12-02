#!/usr/bin/perl

use strict;
use warnings;

use Carp;
use Getopt::Long qw(:config gnu_getopt);
use File::stat;
use File::Spec;
use POSIX qw(setsid);
use Readonly;

my $home_doc_dir = File::Spec->catdir(qw( /cygdrive c Users ), $ENV{USER}, 'Documents');

my $ARCHIVE_DIR_DEFAULT = File::Spec->catdir($home_doc_dir, 'asrotor');
$ARCHIVE_DIR_DEFAULT = undef unless -d $ARCHIVE_DIR_DEFAULT;

my $USER_DIR_DEFAULT = File::Spec->catdir($home_doc_dir, 'Paradox Interactive', 'Crusader Kings II');
$USER_DIR_DEFAULT = undef unless -d $USER_DIR_DEFAULT;


my $opt_archive_dir = $ARCHIVE_DIR_DEFAULT;
my $opt_user_dir = $USER_DIR_DEFAULT;
my $opt_mod_user_dir = 'HIP';
my $opt_name;
my $opt_continue = 0;
my $opt_bench_file = 0;
my $opt_daemon = 0;
my $opt_resume_reason;
my $opt_compress = 1;
my $opt_archive = 1;

GetOptions(
	'a|archive-dir=s' => \$opt_archive_dir,
	'u|user-dir=s' => \$opt_user_dir,
	'm|mod-user-dir=s' => \$opt_mod_user_dir,
	'Z|ziji' => sub { $opt_user_dir = File::Spec->catdir(qw( /cygdrive d ck )) },
	'n|name=s' => \$opt_name,
	'c|continue' => \$opt_continue,
	'D|daemonize' => \$opt_daemon,
	'r|resume-reason=s' => \$opt_resume_reason,
	'ctd|resume-ctd' => sub { $opt_resume_reason = 'CTD' },
	'normal|resume-normal' => sub { $opt_resume_reason = 'Normal' },
	'no-compression' => sub { $opt_compress = 0 },
	'no-save-archiving' => sub { $opt_archive = 0 },
) or croak;

$opt_continue = 1 if $opt_resume_reason;
	
croak "specify a user directory with --user-dir" unless $opt_user_dir;
croak "specify a name for the savegame series with --name" unless $opt_name;
croak "specify an archive root directory with --archive-dir" unless $opt_archive_dir;

croak "user directory not found or not a directory: $opt_user_dir" unless -d $opt_user_dir;
croak "archive root directory not found or not a directory: $opt_archive_dir" unless -d $opt_archive_dir;

my $user_dir = $opt_user_dir;

if ($opt_mod_user_dir) {
	$user_dir = File::Spec->catdir($opt_user_dir, $opt_mod_user_dir);
	
	unless (-e $user_dir) {
		mkdir $user_dir or croak "folder creation failed: $!: $user_dir";
	}
}

# input
my $gamelog_dir = File::Spec->catdir($opt_user_dir, 'logs');
my $gamelog_file = File::Spec->catfile($gamelog_dir, 'game.log');
my $save_dir = File::Spec->catdir($user_dir, 'save games');
my $autosave_file = File::Spec->catfile($save_dir, 'autosave.ck2');

# output
my $archive_dir = File::Spec->catfile($opt_archive_dir, $opt_name);
my $counter_file = File::Spec->catfile($archive_dir, '.counter');
my $bench_file = File::Spec->catfile($archive_dir, 'benchmark_'.$opt_name.'.csv');
my $pid_file = File::Spec->catfile($opt_archive_dir, '.pid');
my $log_file = File::Spec->catfile($archive_dir, 'game.log');

unless (-d $save_dir) {
	mkdir $save_dir or croak "folder creation failed: $!: $save_dir";
}

unless (-d $gamelog_dir) {
	mkdir $gamelog_dir or croak "folder creation failed: $!: $gamelog_dir";
}

if (-e $pid_file) {
	open(my $pf, '<', $pid_file);
	my $pid = <$pf>;
	$pf->close;

	if (kill 0 => $pid) {
		print STDERR "A daemon (background) asrotor instance is already running!\n";
		print STDERR "Its process ID is $pid. Terminate it with the command:\nkill $pid\n";
		exit 1;
	}
	else {
		print STDERR "WARNING: Found PID file from previous daemon, but it's no longer running.\n";
		print STDERR "This means that it may not have cleanly shutdown.\n\n";
		unlink($pid_file);
	}
}

my $time_start = time();
my $time_last = $time_start;
my $counter_start = 0;
my $counter = 0;

sub finish {
	unlink $pid_file if $opt_daemon;
	
	print "Processed ".($counter-$counter_start)." autosaves, series totaling $counter, over ".sprintf("%.2f", (time()-$time_start)/60)." minutes.\n";
	print "Path: $archive_dir\n";
	exit 0;
}

$SIG{INT} = \&finish;
$SIG{TERM} = \&finish;


my $bf;

if (-e $archive_dir) {
	croak "archive directory preexists; continue existing series with -c or --continue" unless $opt_continue;
	croak "must specify a resume reason with --resume-reason <TEXT>, --ctd, or --normal" unless $opt_resume_reason;
	croak "cannot continue without series counter file" unless -f $counter_file;

	read_counter_file();
	$counter_start = $counter;
	open($bf, '>>', $bench_file) or croak "file open failed: $!: $bench_file";
}
else {
	mkdir $archive_dir or croak "folder creation failed: $!: $archive_dir";
	update_counter_file();
	open($bf, '>', $bench_file) or croak "file open failed: $!: $bench_file";
	$bf->print("Sample ID;Date;Duration (seconds);File Size (MB);Resume Reason;Comment\n");
}

my $as_mtime = (-f $autosave_file) ? stat($autosave_file)->mtime : 0;
my $gl_size = 0;
my $waiting = 0;

while (1) {

	if ($waiting % 10 == 0) {
		print STDERR "Waiting for first autosave (start the game)...\n";
		++$waiting; # only print this reminder every 10sec
		
		if ($opt_daemon && $waiting == 0) {
			my $pid = daemonize();

			if ($pid) {
				# parent... print PID of child for later reference, then exit.
				print STDERR "Running in the background...\nTo terminate: kill $pid\n";
				exit 0;
			}
			else {
				# child... now detach from terminal and create a new session
				detach();
				# then continue onward...
			}
		}
	}

	my $st = stat($autosave_file);
	
	if (defined $st && $st->mtime > $as_mtime) {
		# autosave file is present and its mtime is newer than previously recorded
		
		$waiting = -1;
		
		# sleep an extra 10 seconds to allow for the game to do a slow write-out
		# of a very large save.  we may otherwise catch the file in the middle of
		# being written.
		
		sleep(10);
		
		my $gl_st = stat($gamelog_file);
		my $gl_new_size;

		unless (defined $gl_st) {
			print STDERR "ERROR: could not stat game.log when rotating save: $!\n";
			$gl_new_size = 0;
		}
		else {
			$gl_new_size = $gl_st->size;
		}

		my $gl_bytes_grown = $gl_new_size - $gl_size;
		
		if ($gl_bytes_grown > 0) {
			my $gl_new_data;
			
			open(my $glf, '<', $gamelog_file) or croak "file open failed: $!: $gamelog_file";
			$glf->seek($gl_size, 0);
			($glf->read($gl_new_data, $gl_bytes_grown) == $gl_bytes_grown)
				or croak "read of $gl_bytes_grown bytes failed: $!: $gamelog_file";
			$glf->close;
			
			open($glf, '>>', $log_file) or croak "file open failed: $!: $log_file";
			$glf->print($gl_new_data);
			$glf->close;
		}
		elsif ($gl_bytes_grown < 0) {
			print STDERR "WARNING: game.log was truncated, implying restart of CK2: excluding autosave's timing...\n";
			
			my $gl_new_data;
			
			if ($gl_new_size) {
				open(my $glf, '<', $gamelog_file) or croak "file open failed: $!: $gamelog_file";
				($glf->read($gl_new_data, $gl_new_size) == $gl_new_size)
					or croak "read of $gl_new_size bytes failed: $!: $gamelog_file";
				$glf->close;
			}
				
			open($glf, '>>', $log_file) or croak "file open failed: $!: $log_file";
			$glf->print("=" x 72, "\n", "==== GAME.LOG TRUNCATED!\n", "=" x 72, "\n");
			$glf->print($gl_new_data) if $gl_new_data;
			$glf->close;
		}
		
		$gl_size = $gl_new_size;
		
		# redo the stat, in case the mtime is later now due to an in-progress write
		# (and, if benchmarking, we want the exact time between the end-of-write
		# of autosaves)
		$st = stat($autosave_file);
		my $date = parse_savegame_date($autosave_file);
		
		my $elapsed = '';
		my $reason_for_no_timing = '';
		my $sdate = '';
		my $size_mb = sprintf('%0.1f', $st->size / 1_000_000);
		
		unless ($date) {
			print STDERR "ERROR: could not extract date from autosave!\n";
		}
		else {
			$sdate = sprintf("%04d-%02d-%02d", @$date);
		}
	
		if ($counter == $counter_start) { # the first save in a run can't be clocked
			$reason_for_no_timing = $opt_resume_reason if $counter;
		}
		elsif ($gl_bytes_grown < 0) {
			$reason_for_no_timing = 'Unknown';
		}
		else {
			$elapsed = $st->mtime - $as_mtime;
		}
		
		$as_mtime = $st->mtime; # rotate the previous mtime
		
		$bf->print($counter, ';', $sdate, ';', $elapsed, ';', $size_mb, ';', $reason_for_no_timing, ';', "\n");
		$bf->flush;
		
		++$counter;
		update_counter_file();
		
		# now move the save to the head of our archive series, if archiving

		if ($opt_archive) {
			if ($opt_compress) {
				my $dest_file = "$sdate.ck2.gz";
				# TODO: actually fork() and redirect STDIN/STDOUT and exec gzip, as this won't allow series
				# to have names with apostrophes, for one thing.
				(system("gzip < '$autosave_file' > '$archive_dir/$dest_file'") == 0)
					or croak "ERROR: failed to gzip save: $!";
			}
			else {
				my $dest_file = "$sdate.ck2";
				File::Copy::move($autosave_file, "$archive_dir/$dest_file") or croak $!;
			}
		}

		
		print STDERR "processed save (date: $sdate)";
		print STDERR " in ${elapsed}sec" if $elapsed;
		print STDERR "\n";
		$time_last = time();
	}
	
	sleep(1);
}

# currently not reachable, as a SIGINT is required to stop monitoring the save directory
finish();



sub update_counter_file {
    open(my $cf, '>', $counter_file) or croak $!;
    $cf->print("$counter\n");
}

sub read_counter_file {
    open(my $cf, '<', $counter_file) or croak $!;
    $counter = <$cf>;
    $counter =~ s/\r?\n$//;
}

sub daemonize {
	my $null = File::Spec->devnull;
	
	chdir($archive_dir)       or croak "can't chdir: $!: $archive_dir";
	open(STDIN,  "<", $null)  or croak "can't read $null: $!";
	open(STDOUT, ">", $null)  or croak "can't write to $null: $!";
	defined(my $pid = fork()) or croak "can't fork: $!";
	return $pid;
}

sub detach {
	(setsid() != -1)          or croak "can't start a new session: $!";
	open(STDERR, ">&STDOUT")  or croak "can't dup stderr -> stdout: $!";
	
	open(my $pf, '>', $pid_file);
	$pf->print($$);
	$pf->close;
}

sub parse_savegame_date {
	my $filename = shift;
	my $date = undef;
	
	open(my $sf, '<', $filename) or croak "failed to open savegame file: $!: $filename";
	
	while (<$sf>) {
		next unless /^\tdate="(\d{3,4})\.(\d{1,2})\.(\d{1,2})"/;
		$date = [0+$1, 0+$2, 0+$3];
		last;
	}
	
	$sf->close;
	return $date;
}

