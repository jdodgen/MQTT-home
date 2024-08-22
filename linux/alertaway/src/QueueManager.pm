package QueueManager;
use POSIX;
use POSIX::RT::MQ;
use IPC::SysV qw(IPC_NOWAIT);
use Storable;
use Carp qw(croak carp confess cluck longmess shortmess);
use Data::Dumper;
# use processManager;
use cfg;
use db;
use strict;

use filterPrint;
use constant DBG => 1;

my $fp = filterPrint->new();

my $WorkerBeeQueue_id = 'WorkerBeeQueue';
my $SendQueue_id = 'SendQueue';
my $ReceiveQueue_id = 'ReceiveQueue';
my $TraceQueue_id = 'TraceQueue';
my $EmailQueue_id = 'EmailQueue';
my $Watchdog_id = 'Watchdog';
my $ProcessMsgQueue_id = 'ProcessMsgQueue';
my $PacketQueue_id = "PacketQueue";
my $EvaluateQueue_id = "EvaluateQueue";

sub new
{   # options are timeout, name, create (caution on create, only do it befor the other processes start processes) message_size ( message size only used on a create)
    # 1 = reader, 2 = readwrite (rare),  python_reader = 1 if sending to python pickled else perl Storable (faster)
    my($this, $options) = @_;
    my $class = ref($this) || $this;
    my $timeout;
    my $dt = db::open(cfg::DBNAME);
    my $pname = GetNameByPID($dt,$$);
    if ($options->{timeout})
    {
        $timeout = $options->{timeout};
        # print "timeout $timeout\n";
    }
    my $self = {};
    bless $self, $class;

    if ($options->{python_reader})
    {
        $self->{pickle} = 1;
        DBG&&$fp->prt("pickling on");
    }
    $self->{wait} = 0;
    if ($options->{nowait})
    {
        $self->{wait} = IPC_NOWAIT;
    }
    $self->{dt} = $dt;
    $self->{WorkerBeeQueue} = undef;
    $self->{WorkerBeeQueue}= QueueManager::WorkerBeeQueue() if ($WorkerBeeQueue_id ne $options->{name});
    $self->{name} = '/'.$options->{name};
    DBG&&$fp->prt("debugging ON");
    my $status;
    my ($mq_msgsize, $mq_maxmsg);
    ($status, $self->{largest_msg}, $self->{nbr_in_queue}, $mq_msgsize, $mq_maxmsg) = $dt->get_rec("SELECT largest_msg, nbr_in_queue, mq_msgsize, mq_maxmsg FROM queue_size WHERE queue = %s", $self->{name});
    if ($status == 0) #fresh no history yet
    {
        $self->{largest_msg} = 0;
        $self->{nbr_in_queue} = 0;
    }
    else # now check to see how things look and adjust if needed
    {
        # TBD
    }

    DBG&&$fp->prt("%s %s pid = %s", $options->{name}, $options->{reader}||'DEFAULT', $pname);

    if ($options->{create})
    {
        $self->{oflag} = 'O_RDWR|O_CREAT';
        my $attr = {mq_maxmsg  => $options->{queue_size}, mq_msgsize => $options->{message_size}||256};
        $self->{mq} = POSIX::RT::MQ->open($self->{name}, O_RDWR|O_CREAT, 0666, $attr)
           or croak "QueueManager:new cannot open [$pname] [$self->{name}]: [$!] maxmsg[$options->{queue_size}] maxsize[$options->{message_size}]\n";
        my $mq_attr = $self->{mq}->attr();
        $mq_attr->{mq_flags} |= O_NONBLOCK if ($options->{nowait});
        $self->{dt}->do("INSERT OR REPLACE INTO  queue_size (largest_msg, mq_msgsize, nbr_in_queue, mq_maxmsg, queue) VALUES ( %s,%s,%s,%s,%s)",
            $self->{largest_msg},  $mq_attr->{mq_msgsize}, $self->{nbr_in_queue}, $mq_attr->{mq_maxmsg}, $self->{name});
        # chmod 0666, '/dev/mqueue/'.$self->{name};
        printf "QueueManager::new mq_flags[%s],mq_maxmsg[%s],mq_msgsize[%s],mq_curmsgs[%s]\n", $mq_attr->{mq_flags},  $mq_attr->{mq_maxmsg},  $mq_attr->{mq_msgsize},  $mq_attr->{mq_curmsgs};
    }
    else
    {
        my $oflag = O_WRONLY; # default
        $self->{oflag} = 'O_WRONLY';
        if ($options->{reader})
        {
            if ($options->{reader} == 1)
            {
                $oflag = O_RDONLY;
                $self->{oflag} = 'O_RDONLY';
            }
            elsif ($options->{reader} == 2)
            {
                $oflag = O_RDWR;
                $self->{oflag} = 'O_RDWR';
            }
        }
        $self->{mq} = POSIX::RT::MQ->open($self->{name}, $oflag)
            or croak "QueueManager:new cannot open $pname $self->{name}: $!\n";
        $self->{mq}->blocking(0) if ($options->{nowait});
    }
    return $self;
}

sub unlink_queue
{
    my ($name) = @_;
    printf "QueueManager::enqueue unlinkin %s\n", $name;
    POSIX::RT::MQ::mq_unlink  "/".$name;
}

use Inline Python => <<'...';
import  pickle
def __unpickler(s):
    try:
        x =  pickle.loads(str.encode(s))
        return x
    except:
        print("pickle loads failed")
        return None

def __pickler(s):
    try:
        x =  pickle.dumps(s)
        return x
    except:
        print("pickle dumps failed")
        return
...


# method to put something on the queue
sub enqueue {
    my($self, $din)=@_;

    # print "enqueue > ".Dumper($din). "data type ".ref($din)."\n";
    my $in_queue = $self->{mq}->attr()->{mq_curmsgs};
    my $max_size = $self->{mq}->attr()->{mq_msgsize};
    DBG&&$fp->prt("[%s][%s] from[%s] queue_count %s >>",  $self->{name},  $self->{oflag}, GetNameByPID($self->{dt},$$), $in_queue);
    my $item = undef;
    if ($self->{pickle})
    {
        $item = __pickler($din);
        DBG&&$fp->prt("--picked")
    }
    else
    {
        $item = Storable::freeze($din);
        DBG&&$fp->prt("--frozen")
    }
    my $lth = length($item);
    if ($lth > $max_size)
    {
        DBG&&$fp->prt("message size exceeded [%s] this message = %s  max = %s", $self->{name}, $lth, $max_size);
        $self->{WorkerBeeQueue}->enqueue({request => "LOG", fmt => "QueueManager::enqueue message size exceeded [%s] this message = %s  max = %s",
                parms => [$self->{name}, $lth, $max_size]}) if ($self->{WorkerBeeQueue});
        $self->{dt}->do("UPDATE queue_size SET largest_msg = %s WHERE  queue = %s", $lth, $self->{name});
        ## confess "QueueManager::enqueue message size exceeded";
        return;
    }
    my $status = $self->{mq}->send($item);
    if (!$status)
    {
        DBG&&$fp->prt("enqueue cannot send: $!");
    }
    DBG&&$fp->prt("enqueue done [%s]",  $self->{name});
}
#
# method to pull something off the queue
#

sub dequeue {
    my($self, $timeout) = @_; #timeout in seconds
    my $in_queue = $self->{mq}->attr()->{mq_curmsgs};
    DBG&&$fp->prt("current queue count [%s]", $in_queue);
    DBG&&$fp->prt("[%s][%s] timeout = [%s] queue count[%s]",  
        $self->{name},  $self->{oflag}, $timeout||'none',  $in_queue);
    my ($msg,  $prio);
    if ($timeout)
    {
        my @ret  = $self->{mq}->timedreceive($timeout);# or die "QueueManager:dequeue with timeout cannot receive: $!\n";
        if (!@ret)
        {
            DBG&&$fp->prt("[%s][%s], returned nothing, timedout?", $self->{name},$$);
            return
        }
        else
        {
            ($msg,  $prio) = @ret;
            DBG&&$fp->prt("%s, timed returned %s", $self->{name}, substr($msg, 0, 1));
        }
    }
    else
    {
        ($msg,  $prio)  = $self->{mq}->receive or die "cannot receive  $!\n";
    }
    #my $lth = length($msg);

    #if ($lth > $self->{largest_msg})
    #{
           #$self->{dt}->do("UPDATE queue_size SET largest_msg = %s WHERE  queue = %s", $lth, $self->{name});
           #$self->{largest_msg} = $lth;
    #}
    if ($in_queue > $self->{nbr_in_queue})
    {
           $self->{dt}->do("UPDATE queue_size SET nbr_in_queue = %s WHERE  queue = %s", $in_queue, $self->{name});
           $self->{nbr_in_queue} = $in_queue;
    }
    #printf "Dequeue largest[%s][%s:%s][%s]\n", $largest,$toread, $type, $stack;
    #printf "Dequeue largest[%s][%s:%s]\n", $largest, $toread, $type;
    # print "dequeue > ". $data . "type $type\n";
    my $thawed = __unpickler($msg);
    if (!$thawed)
    {
        my %ret = %{Storable::thaw($msg)};
        #DBG&&$fp->prt("Perl message: [%s]", Dumper %ret);
        return \%ret;
    }
    else
    {       
        #DBG&&$fp->prt("Python message[%s]\n", Dumper $thawed);
        return $thawed;
    }
}

sub queue_cnt
{
    my $self = shift;
    return $self->{mq}->attr()->{mq_curmsgs};
}

sub destroy_message_queues
{
    QueueManager::unlink_queue($WorkerBeeQueue_id);
    QueueManager::unlink_queue($ReceiveQueue_id);
    QueueManager::unlink_queue($SendQueue_id);
    QueueManager::unlink_queue($TraceQueue_id);
    QueueManager::unlink_queue($EmailQueue_id);
    QueueManager::unlink_queue($Watchdog_id);
    QueueManager::unlink_queue($ProcessMsgQueue_id);
    QueueManager::unlink_queue($PacketQueue_id);
    QueueManager::unlink_queue($EvaluateQueue_id);
    printf "QueueManager::old queues removed\n";
}

sub create_message_queues
{
    print "creating message queues\n";
    my $WorkerBeeQueue  = QueueManager->new({name =>$WorkerBeeQueue_id, create => 1, message_size => 300, queue_size => 100});
    my $Watchdog        = QueueManager->new({name =>$Watchdog_id, create => 1, message_size => 255, queue_size => 10});
    my $SendQueue       = QueueManager->new({name =>$SendQueue_id, create => 1, message_size => 255, queue_size => 300});
    my $ReceiveQueue    = QueueManager->new({name =>$ReceiveQueue_id, create => 1, message_size => 255, queue_size => 300});
    my $TraceQueue      = QueueManager->new({name =>$TraceQueue_id, create => 1, message_size => 10, queue_size => 10, nowait => 1});
    my $EmailQueue      = QueueManager->new({name =>$EmailQueue_id, create => 1, message_size => 8000, queue_size => 10});
    my $ProcessMsgQueue = QueueManager->new({name =>$ProcessMsgQueue_id, create => 1, message_size => 1000, queue_size => 100});
    my $PacketQueue     = QueueManager->new({name =>$PacketQueue_id, create => 1, message_size => 255, queue_size => 250});
    my $EvaluateQueue   = QueueManager->new({name =>$EvaluateQueue_id, create => 1, message_size => 10, queue_size => 1, nowait => 1});  # this is just a trigger with a timeout

    return ($WorkerBeeQueue, $SendQueue, $ReceiveQueue,$TraceQueue, $EmailQueue, $Watchdog, $ProcessMsgQueue, $PacketQueue, $EvaluateQueue)
}

sub WorkerBeeQueue
{
    my ($options) = @_;
    return  QueueManager->new({name =>$WorkerBeeQueue_id, reader => $options->{reader}, nowait => $options->{nowait}});
}
sub SendQueue
{
    my ($options) = @_;
    return  QueueManager->new({name =>$SendQueue_id, python_reader => $options->{python_reader}, reader => $options->{reader}, nowait => $options->{nowait}});
}
sub ReceiveQueue
{
    my ($options) = @_;
    return  QueueManager->new({name =>$ReceiveQueue_id, reader => $options->{reader}, nowait => $options->{nowait}});
}
sub TraceQueue
{
    my ($options) = @_;
    return  QueueManager->new({name => $TraceQueue_id, reader => $options->{reader}, nowait => $options->{nowait}});
}
sub EmailQueue
{
    my ($options) = @_;
    return  QueueManager->new({name => $EmailQueue_id, reader => $options->{reader}, nowait => $options->{nowait}});
}
sub Watchdog
{
    my ($options) = @_;
    return  QueueManager->new({name => $Watchdog_id, reader => $options->{reader}, nowait => $options->{nowait}});
}
sub ProcessMsgQueue
{
    my ($options) = @_;
    return  QueueManager->new({name => $ProcessMsgQueue_id, reader => $options->{reader}, nowait => $options->{nowait}}) ;
}
sub PacketQueue
{
    my ($options) = @_;
    return  QueueManager->new({name => $PacketQueue_id, reader => $options->{reader}, nowait => $options->{nowait}});
}
sub EvaluateQueue
{
    my ($options) = @_;
    return  QueueManager->new({name => $EvaluateQueue_id, reader => $options->{reader}, nowait => $options->{nowait}});
}


sub GetNameByPID
{
    my ($dt, $pid) = @_;
    my ($status, $name) = $dt->get_rec("select name from processes where pid = %s", $pid);
    return "[$pid]" if ($status == 0);
    return $name;
}
1;
