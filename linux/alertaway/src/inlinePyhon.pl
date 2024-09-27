# testing Inline

sub task()
{
    
	use Inline Python => <<'...';

def run_task():
	from  mqtt_processor import mqtt_task
	mqtt_task()
	print("mqtt_task ran")	
...
	run_task()	
}
sleep(2);
print("after sub task defined\n");
sleep(5);
task();
sleep(1);
print("after task called\n");
