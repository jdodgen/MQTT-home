package favicon;
require Convert::UU;
# Copyright 2011 by James E Dodgen Jr.  All rights reserved.
# use Convert::UU qw(uudecode);
sub get
{
my $icon = q~begin 644 fav_icon
M```!``$`$!`0```````H`0``%@```"@````0````(`````$`!```````@```
M````````````$```````````````BYEN`,OFDP`F,PH`E,(P````````````
M`````````````````````````````````````````````````S0`1$0`0S``
M-`0B(D!#```T!```0$,``#0`````0P``-`)`!"!#```T`C`#($,`,S,`````
M,S,Q0C````,D$P,4(P``,D$P`#%",`,B$P```Q0C,D$P````,4(D$S`````#
M%$$P,``````Q$P````````,P``````````````",,0``R!,``,O3``#/\P``
MR9,``,F3```/\```!^```(/!``#!@P``X`<``/`'``#X%P``_#\``/Y_``#_
#_P``
`
end~;
my $binary =  Convert::UU::uudecode $icon;
return $binary;
}

sub drop
{
    my ($where) = @_;
    my $icon = get();
    open FILE, ">$where/favicon.ico";
    print FILE $icon;
    close FILE;
}
1;
