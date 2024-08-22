# testing QueueManager with messages from python process
# as well as now sending/receiving pickled python messages
use Data::Dumper;
use strict;
use tools qw (:debug);
use cfg;
use QueueManager;
use db;
use filterPrint;
use feature 'state';
use constant QUEUE_TIMEOUT => 120;

sub task
{
    
    my ($trace_in, $api, $evaluate_pid) = @_;
    my  $SendQueue= QueueManager::SendQueue({python_reader => 1});
    $SendQueue->enqueue({name => 'from perl living_room_light', value => 'ON'});  # turn on
    {
        my $ReceiveQueue = QueueManager::ReceiveQueue();
        $ReceiveQueue->enqueue({name => 'perl living_room_light', value => 'ON'}); # IS on
    }

    my $ReceiveQueue = QueueManager::ReceiveQueue({reader => 1});
    sleep(4);
    while (1)
    {
       my $message = $ReceiveQueue->dequeue(); # just used mostly for an event
       if (!$message)
       {
        printf("timed out");
       }
       else
       {
        printf("test.message[%s]\n", Dumper $message);
       }
    }
}
task();