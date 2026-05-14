package time_keeper;
use strict;
use filterPrint;
use tools;
#use constant DBG => 0;
my $fp = filterPrint->new();
sub set_time
{
    my ($dt, $epoc_time) = @_;
    DBG&&$fp->prt("time_keeper:set_time: = %s", $epoc_time||'?');
    my $result = system ('sudo /bin/date -s  @'.$epoc_time." >/dev/null");
}

sub fix_time
{
    my ($dt, $epoc_time) = @_;
    my $curr_time =  time;
    my $diff = $curr_time - $epoc_time;
    DBG&&$fp->prt("time_keeper:fix_time: correcting time from %s to %s diff =%s", $curr_time, $epoc_time||'?', $diff);
    $dt->do("update config set time_offset = time_offset + %s", $diff);
    set_time($dt, $epoc_time);
}

1;
