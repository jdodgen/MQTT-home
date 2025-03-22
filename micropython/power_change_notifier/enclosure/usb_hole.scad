$fn=60;
z_lenght = 20-4.4;
y_width=13.2;
x_depth = 5.1;
x_offset=1;
y_offset=2;
min_y = y_width+y_offset*2;
min_x = x_depth+x_offset*2;
wall = 2;

*difference()
{
    support(5, wall);
    color("red") cutout(5);
}

module make_usb()
{
        usb_a_male([10,20,2]);
}

module make_usb_cutout()
{
    // translate([0.2,(-min_y/2),0])
        cutout(3);
}

module usb_a_male(xyz)
{

    cube([min_x,min_y, xyz[2]]);
    pin_wall();
    translate([0,0,z_lenght]) 
        pin_cap(xyz[2]);

}

module pin_cap(thick)
{
    cube([thick+1, min_y, thick]);
}

module pin_wall()
{
    cube([x_offset,min_y, z_lenght]);
    cube([x_offset+2,y_offset, z_lenght]);
    translate([0,min_y-y_offset,0])
        cube([x_offset+2,y_offset, z_lenght]);
    post_from_edge = 11.5;
    post_spread=6;
    post_offset=(y_width-post_spread) /2;
    translate([x_offset,y_offset+post_offset,post_from_edge]) 
    {
        post();
        translate([0,post_spread,0])
            post();
    }
}

module support(height, wall)
{   
    translate([-x_depth-wall,(-y_width/2)-wall,0])
        cube([x_depth+wall*2,y_width+(wall*2), height]);
}

/*module cutout(height)
{
    translate([x_offset,y_offset,0])
        cube([x_height,y_width, height]);
}*/

module cutout(height)
{
    translate([-x_depth, -y_width/2, 0])
        cube([x_depth, y_width, height]);
}


module post(height=1.6, diameter=2.5) 
{
    rotate([0,90,0])
        cylinder(h=height, d=diameter, $fn=30);
}

rotate([90,0,0]) 
    color("blue")   
        make_usb_b_slot_plug();

module make_usb_b_slot_plug(s, thickness=4, rotate=0, offset=0.2) { 
        make_slot_rounded(width=10-offset,  height=8-offset, thickness=thickness);
        translate([0,0,-1])make_slot_rounded(width=12,  height=10, thickness=1.5);
}
module make_usb_b_slot(s, thickness=10, rotate=0) { 
    rotate([0,0,rotate])
        make_slot_rounded(width=10,  height=8, thickness=thickness);
}

module make_slot_rounded(s, width=10, height=10, pointed=0, curved_ends=1, thickness=5) {
	translate([-width/2,0,0])
	{ 
		cube([width, thickness, height]);
		if (curved_ends == 1) {
			translate([0, thickness, height/2])
				rotate([90,0,0]) 
				scale([0.7,1,1]) 
					cylinder(h = thickness, d = height, center=false);
			 
			translate([width, thickness, height/2])
				rotate([90,0,0])
				scale([0.7,1,1]) 
					cylinder(h = thickness, d = height, center=false); 
		}
	}
}