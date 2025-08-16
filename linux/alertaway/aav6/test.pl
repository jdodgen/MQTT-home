
my $options;
$options->{items} = [1,2,3,4];

if ($options->{items})
{
        foreach my $g (@{$options->{items}})
        {
            print"$g\n";
            push(@work, $g);
        }
         push(@work, (@{$options->{items}}));

}
print @work;












#package foobar;
#use filterPrint;
#use constant DBG => 1;
#my $fp = filterPrint->new();

#$fp->prt("main $xbee_serial_port");
#foo();
#sub foo
#{
    #$fp->prt("foo");
#}

#use strict;
#use feature "current_sub";
#use Sub::Identify qw/sub_fullname/;

#print "\e[1;3;31mSTARTED\e[0m";
#start();
#printf  ">>>>>>>> [%s]\n", (caller(0))[3]||"main";

#printf  "package %s sub %s \n", __PACKAGE__, sub_fullname(__SUB__);
#;

#sub start
#{
    #printf ">>>>start>>>[%s]\n", (caller(0))[3]||"main";
    #foo::foobar();
#}


#sub whocalled  {
    ##printf ">>>whocalled>>[%s]\n", (caller(1))[3]||"main";
    ##printf  "package %s sub %s \n", __PACKAGE__, __SUB__;
    #my ($package,$filename, $line, $subroutine) = caller(1);
    #my $tail = "";
    #my $depth=3;
    #while (1)
    #{
        #my ($package,$filename, $line, $subroutine) = caller($depth++);
        #last if (!$subroutine);
        #$tail .= ">".$subroutine." @ ".$line;
    #}

    #my $called_by1 = (caller(2))[3];
    #my $from = $called_by1?$called_by1:$package; # top check
    #return $subroutine.">".$from." Line ".$line.$tail;
#}


#package foo;

#sub foobar
#{
    #printf  ">>>foobar>>>[%s]\n", (caller(0))[3]||"main";
    #shitbox::sb();
#}

#package shitbox;

#sub sb {
    #printf  ">>>>sb>>[%s]\n", (caller(0))[3]||"main";
    #printf  "package %s sub %s \n", __PACKAGE__, __SUB__;
    ##printf "%s\n",  main::whocalled();
    #d::deep();
#}

#package d;

#sub deep {
    #printf  ">>>deep>>[%s]\n", (caller(0))[3]||"main";
    ##printf "%s\n",  main::whocalled();
#}



