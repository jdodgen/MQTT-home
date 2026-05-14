package filterPrint;
use Data::Dumper;
use strict;
use Exporter;

our @ISA = qw(Exporter);
our @EXPORT = qw(prt prt_init prt_filter DBG);

use constant DBG => 0;

# DBG when set to 0 causes all the prt statement to be optomized out (speeds things up)
# some times DBG can be overridden in the package.
#setting the first parm in the new to zero causes the prints to be off but code is not optomized
#this may go away later.
#
## usage:
## use filterPrint;
## use constant DBG => 0; 1 to turn on 0 to turn off
## my $fp = filterPrint->new(); or to use the filter $fp = filterPrint->new("a string", "another", "and more");
##
## DBG&&$fp->prt("somthing %s", $foo);  Note no newlines needed


my @global_prt_trace; # =  ("1F43"); #("5626","1F43");

sub new
{
    my ($class,  $options) = @_;
    my $self = {};
    $self->{package} =  caller();
    $self->{trace} = 1;
    $self->{modules} = $options->{modules} if ($options->{modules});
    my @work;
    $self->{prt_trace} = ();
    if (@global_prt_trace)
    {
        foreach my $g (@global_prt_trace)
        {
            push(@work, uc $g);
        }
    }
    if ($options->{items})
    {
        push(@work, (@{$options->{items}}));
    }
    $self->{prt_trace} = \@work;
    bless $self, $class;
    #print Dumper $self;
    return $self;
}
sub trace_if
{
    my ($self, $on) = @_;
    $self->{trace} = $on?1:0;
}

sub on
{
    my ($self) = @_;
    return ($self->{trace} && $self->{do_prt}) ? 1:0;
}
my @filler = qw(1missing 2missing 3missing 4missing 5missing);
sub prt
{
    #return;
    my ($self, $fmt, @parms) = @_;
    no warnings;
    chomp($fmt); # remove any newlines
    my $who = ((caller(1))[3]||$self->{package});
    if ($self->{trace} == 1)
    {
        if ($self->{modules})
        {
            foreach my $n (@{$self->{modules}})
            {
                if (index($who, $n) != -1)
                {
                    printf("[%s]".$fmt."\n", ($who, @parms, @filler));
                    last;
                }
            }
        }
        else
        {
            printf("[%s]".$fmt."\n", ($who, @parms, @filler));
        }
    }
}

sub filter
{
    my ($self, @values) = @_;
    if (@values)
    {
        $self->{trace} = 0;

        foreach my $value (@values)
        {
            if ($value)
            {
                $value = uc $value;
                foreach my $pt (@{$self->{prt_trace}})
                {
                    my $work = uc ''.$pt;
                    #print " testing [$value] [$work]\n";
                    if (''.$value =~ /$work$/)
                    {
                        $self->{trace} = 1;
                        last;
                    }
                    elsif (''.sprintf("%0X",$value) =~ /$work$/)
                    {
                        $self->{trace} = 1;
                        last;
                    }
                }
            }
            last if ($self->{trace} == 1);
        }
    }
    else
    {
        $self->{trace} = 1;
    }
}

#my $fp = filterPrint->new({modules => ['foo','bar','done']});

#done();
#was();

#sub done
#{
    #$fp->prt("done\n");
#}

#sub foo
#{
    #$fp->prt("foo\n");
#}


#sub was
#{
   #$fp->prt("was\n");
   #foo();
#}

#$fp->prt("worked");
1;
