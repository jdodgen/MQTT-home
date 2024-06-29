/* jed's water shutoff - Author Jim Dodgen 2024 */
// MIT licence
use <d1_mini_triple.scad>;

lid_title = ""; 
// post_height =  6;

// make something 
lid = 0; // 1 makes lid
enclosure = 1; // 1 makes enclosure
make_tabs = 2;  //2; // 1 makes end tabs, 2 makes small tabs on sides
only_two = true;   // 
vents_wanted = false; // false;
// make_supports = true;  // false
make_lid();
//make_enclosure();


// test area 
*difference() 
{  
	if (enclosure == 1) 
		make_enclosure();
        translate ([-70,35,0]) cube([200,200,100]); //chop all but rpi
		translate ([-70,-40,10]) cube([200,200,100]);  // chop top

		translate ([20,0,0]) cube([200,200,100]); //chop all but rpi
		//translate ([-70,63,0]) cube([200,200,100]); //chop all but rpi
		//translate ([-70,-20,12]) cube([200,200,100]);  // chop top
	//translate ([-68,0,0]) cube([outer_width+2,200,70]); 
	//translate ([0,-20,0]) cube([outer_width,200,70]); 
}

pi_test = 0;   // 1 = remove non pi items

wall_thickness = 2.0;

interior_width  = 88;    // x
interior_depth = 90;     // y
interior_height =  44;

outer_width =  interior_width   + wall_thickness + wall_thickness;
outer_depth = interior_depth  + wall_thickness + wall_thickness;

corner_lid_mount_size = 8;

power_12v_d =       [[0, (interior_depth/6*5), interior_height/2], 1, 8.3];
motor_interface_d = [[interior_width+2, interior_depth/6*4, interior_height/2], 1, 16];

M3_screw_hole = 3.2; 
M3_clearence_hole = 3.6; 
M3_head_clearence_hole = 6.2;

M2_5_screw_hole = 2.75; 
M2_5_clearence_hole = 3.1; 
M2_5_head_clearence_hole = 6.2;
Mx_fn = 6; // self tapping 

post_height =  6;
length_adjustments=0;

//make_slot/fuse values
s_xyz = 0;
s_rotate = 1;
s_width = 2;
s_diameter = 2;
s_height = 3;

//vents
v_x = 0;
v_y = 1;
v_z = 2;
v_rotate = 3;
v_width = 4;
v_height = 5;
vent_count = 8; 
bottom_vents =[corner_lid_mount_size+wall_thickness+2, 0,   post_height+wall_thickness+13, 0, 3, interior_height-(wall_thickness*2)-23];
top_vents =   [corner_lid_mount_size+wall_thickness+2, interior_depth+wall_thickness,   post_height+wall_thickness, 0, 3, interior_height-(wall_thickness*2)-8];
left_vents =  [0, 110+length_adjustments,   post_height+wall_thickness-2, 1, 3, interior_height-(wall_thickness*2)-8];
right_vents =  [interior_width+wall_thickness, 110+length_adjustments,   post_height+wall_thickness-2, 1, 3, interior_height-(wall_thickness*2)-8];
// lid slo
lid_vents1 =[-5, 14, 12.5, 1, 3, 24];
lid_vents2 =[-5, 14, 55, 1, 3, 24];

lid_recess = 2;
lid_recess_width = 10;
lid_thickness = wall_thickness;
// all vectors are indexed by relay_used 
lid_letter_large = [0,7,10,0,10];
lid_letter_medium= [0,4,6,0,6];
lid_letter_small = [0,5,5,0,5];
// part_desc = [0,"Relay","Dual Relay",0,"Quad Relay"];

tab_size = 20;
tab_holes = 5; // 5mm

$fn=40;

if (lid == 1)
{ 
    if (enclosure == 1) 
        translate([outer_width+5,0,0]) make_lid(); // move it out of the way
    else
        make_lid();

}
//translate([0,0,interior_height]) make_all_lid_holes();   

module make_enclosure() 
{
    
    difference() 
    {    
        union() 
        {
			difference()
			{				
				cube([outer_width, outer_depth, interior_height]);     
				translate([wall_thickness,wall_thickness,wall_thickness]) 
					cube([interior_width, interior_depth, interior_height]); 
			}
			translate([wall_thickness+3.5,wall_thickness+6, 0])
				make_d1_mini_mount(wall_thickness);
		}       
                        
		fillet(0,wall_thickness, interior_height);
		translate([outer_width-wall_thickness,0,0])
			fillet(90,wall_thickness, interior_height);
		translate([outer_width-wall_thickness,
			outer_depth-wall_thickness,0])
			fillet(180,wall_thickness, interior_height);
		translate([0,
			outer_depth-wall_thickness,0])
			fillet(-90,wall_thickness, interior_height);

        make_simple_hole(power_12v_d);
		make_simple_hole(motor_interface_d);
		
		if (vents_wanted)
		{
			make_vents(bottom_vents, spacing=8, count=9, XorY="x");
			make_vents(left_vents, spacing=8, count=5, XorY="y"); 
			make_vents(right_vents, spacing=8, count=5, XorY="y");
		}
    }
	make_lid_mounts();		

	if (make_tabs == 1)
	{
		translate([wall_thickness,-tab_size+0.1,0]) mounting_tab(0);
		translate([outer_width-wall_thickness, outer_depth+tab_size, 0]) mounting_tab(180);
	}
	if (make_tabs == 2)  // small tabs
	{
		if (only_two == false)
		{
			translate([-tab_size, outer_depth-5, 0]) small_mounting_tab(-90);
			translate([outer_width+tab_size, outer_depth-tab_size-5, 0]) small_mounting_tab(90);
		}
		translate([-tab_size, 20+2, 0]) small_mounting_tab(-90);
		translate([outer_width+tab_size,  2.0, 0]) small_mounting_tab(90);
	}
}



module make_lid() {
    difference()
    { 
        union() {
            make_lid_top();
            make_lid_recess();
        }
        make_all_lid_holes();
		
		rotate([0,90,0]) make_vents(lid_vents1,  spacing=9, count=vent_count,  XorY="y", pointed=0); 
		rotate([0,90,0]) make_vents(lid_vents2,  spacing=9, count=vent_count,  XorY="y", pointed=0);            
    }
    
}
module make_lid_hole(width, length) {
        translate([width,length,0]) {
            total_thickness = lid_thickness+lid_recess;
            //translate([M3_clearence_hole/2,M3_clearence_hole/2,0])
            cylinder(h=total_thickness, d=M3_clearence_hole);  
        }  
}

middle_Mount_offset = 5.5;
far_Y_place = outer_depth-(wall_thickness*2);
left_side_offset = -5;
module make_lid_mounts() {
	
	// right side
	translate([outer_width-(wall_thickness*2),0,0])
		corner_lid_mount(-90, angle_left=1);
	
    
	translate([outer_width-(wall_thickness*2),far_Y_place,0])
		corner_lid_mount(0, angle_left=0);
	
	*translate([outer_width-(wall_thickness*2),(far_Y_place/2)+middle_Mount_offset,0])
		corner_lid_mount(0, rad_cnt=2, angle_left=1);	
	
	// left side
	corner_lid_mount(180);
	translate([0,far_Y_place,0])
		corner_lid_mount(90, angle_left=1);
	*translate([0,(far_Y_place/2+middle_Mount_offset+left_side_offset)-corner_lid_mount_size,0])
		corner_lid_mount(180, rad_cnt=2, angle_left=1);	
}


module make_all_lid_holes(){        
        offset_from_edge = wall_thickness+corner_lid_mount_size/2;        
        // left side
        make_lid_hole(offset_from_edge,  offset_from_edge); 
        make_lid_hole(offset_from_edge,  outer_depth-offset_from_edge);          
        //make_lid_hole(offset_from_edge,  (far_Y_place/2+middle_Mount_offset+left_side_offset)-wall_thickness); 
        //make_lid_hole(offset_from_edge,  (far_Y_place/2)+middle_Mount_offset-wall_thickness);          
        // right side
        make_lid_hole(outer_width-offset_from_edge, offset_from_edge);          
        make_lid_hole(outer_width-offset_from_edge, outer_depth-offset_from_edge);
        //make_lid_hole(outer_width-offset_from_edge, (far_Y_place/2)+middle_Mount_offset-wall_thickness); 
        //make_lid_hole(outer_width-offset_from_edge, (far_Y_place/2+middle_Mount_offset+left_side_offset)-wall_thickness);      
}   

module make_lid_top() {
    width = outer_width-(wall_thickness*2);
    difference() 
    {
        cube([outer_width, outer_depth, lid_thickness]); // top
        fillet(0,wall_thickness, lid_thickness);
        translate([outer_width-wall_thickness,0,0])
            fillet(90,wall_thickness, lid_thickness);
        translate([outer_width-wall_thickness,
            outer_depth-wall_thickness,0])
            fillet(180,wall_thickness, lid_thickness);
        translate([0,
            outer_depth-wall_thickness,0])
            fillet(-90,wall_thickness, lid_thickness);        
           translate([37,83,1]) 
            rotate([0,180,-90]) 
            center_text(lid_title, size=10, extrude=1.2);
    }
}

module center_text(text, size, font="Liberation Mono:style=Bold", width=10, length=0, extrude=0.6) {

    translate([length, width, 0]) 
    linear_extrude(extrude) 
    text(text, size=size, font=font, halign="center", valign="center");
}

module make_lid_recess() {
    clearance=0.5;
    length=interior_depth-clearance;
    width=interior_width-clearance;   
    translate([wall_thickness+clearance/2, wall_thickness+clearance/2,lid_thickness]) {
        difference() 
        {    
			
			cube([interior_width-clearance, length, lid_recess]); // recess
			translate([lid_recess_width+clearance/2, lid_recess_width+clearance/2,0]) 
				cube([interior_width-clearance-(lid_recess_width*2), 
					length-(lid_recess_width*2), lid_recess]); // recess
        }
    }
}



module make_vents(s, spacing=10, count=5, XorY="x", pointed=1) {

	for (i = [0 : spacing : (spacing * count)-1])
	{
		if (XorY == "x")
		{
			make_slot([s[v_x]+i, s[v_y], s[v_z]], rotate=s[v_rotate], width=s[v_width], height=s[v_height], pointed=pointed);
		} 
		else 
		{
			make_slot([s[v_x], s[v_y]+i, s[v_z]], rotate=s[v_rotate], width=s[v_width], height=s[v_height], pointed=pointed);
		}
	}

}

// make_slot([0,0,0]);
module make_slot(s, rotate=0, width=20, height=10, pointed=0) {
	thickness= wall_thickness*3;
	//echo ("make_slot",  s[s_xyz]);
	translate(s)
	{ 
		if (rotate == 1)	
		{
			translate([thickness,0,0])
				rotate([0,0,90]) 
				{				    		 
					cube([width, thickness, height]);
					if (pointed == 1) {
						x=sqrt(width*width/2);
						translate([0,0,height])
						rotate([0,45,0]) cube([x, thickness, x]);
					}
				}
		}
		else
		{
			cube([width, thickness, height]);
			if (pointed == 1) {
				x=sqrt(width*width/2);
				translate([0,0,height])
				rotate([0,45,0]) cube([x, thickness, x]);
			}
		}
	}
}
//make_slot_rounded([0,0,0], curved_ends=1);
module make_slot_rounded(s, width=10, height=10, pointed=0, curved_ends=1) {
	thickness= wall_thickness*3;
	//echo ("make_slot",  s[s_xyz]);
	translate(s)
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

module make_simple_hole(s)
{
    //echo("rotate=",rotate,"diameter=", diameter);
    thickness = wall_thickness*3;
    z_val = s[s_rotate] == 1 ? 90:0;
    translate(s[s_xyz])
        rotate([90, 0,z_val])
            translate([0,0,-(thickness/2)])
                cylinder(h=thickness, d=s[s_diameter]);    
}

module inner_enclosure() {
    translate([wall_thickness,wall_thickness,wall_thickness]) 
        cube([interior_width, interior_depth, interior_height]); // real
}

module outer_enclosure() { 
    
    cube([outer_width, outer_depth, interior_height]); // real    
}

//corner_lid_mount(0, angle_left=0); 
module corner_lid_mount(rot, rad_cnt=1, angle_left=0) {
    //height=interior_height-lid_recess;
    height=5;
    translate([wall_thickness,wall_thickness,interior_height-lid_recess-height]) 
		rotate([0,0,rot])  
			translate([-(corner_lid_mount_size), -(corner_lid_mount_size),0]) 
				difference() 
				{ 
					union()
					{
						cube([corner_lid_mount_size, corner_lid_mount_size,height]);						
						if (angle_left == 1)
						{
							translate([0,0,0])
								rotate([0,45,0]) color("red")
									cube([20, corner_lid_mount_size, corner_lid_mount_size]);
						} else {
							translate([corner_lid_mount_size,0,0])
								rotate([0,45,90]) color("red")
									cube([20, corner_lid_mount_size, corner_lid_mount_size]);
						} 														
					}
					translate([corner_lid_mount_size/2, corner_lid_mount_size/2,0]) // screw hole
						cylinder(h=height, d=M3_screw_hole, $fn=Mx_fn);                  
					if (rad_cnt > 0) {
						translate([0,0,-height]) fillet(0,corner_lid_mount_size/2, height*2);
					}
					if (rad_cnt > 1) {
						rotate([0,0,-90]) translate([-corner_lid_mount_size,0,-height]) fillet(0,corner_lid_mount_size/2, height*2);
					}
					translate([corner_lid_mount_size,0,-50]) cube([50,corner_lid_mount_size,100]); 
					translate([0,corner_lid_mount_size,-50]) cube([50,corner_lid_mount_size*2,100]);
					translate([0,0,height]) color("green") cube([corner_lid_mount_size,corner_lid_mount_size,20]);
				}                   
}

//[         name,      [location],                 height,      length, width, mount_length, mount_width,  mount_offsetx, mount_offsety]

//relay=     ["relay",  [8,68,0],                 post_height, 34.5,     25.5,      28,             19.5,         3,               3];

//translate([-2,-1,0]) cube([55,28,2]); 
//make_relay_posts([0,0,0]);

module make_outline(s, name="huh", width=10, length=20) {
	translate(s) color("red") 
	{
		translate([0,0,wall_thickness])
		{ 
			difference()
			{
				cube([length, width, 1]);
				translate([1,1,0]) 
					cube([length-2, width-2, 1]);
			}	
			center_text(name, size=6,               
			width=width/2,length=length/2); 
		}
	}
}                

module post(height, radius, screw_hole) {
    
    difference() 
	{
        cylinder(h=height, r=radius);
        if (screw_hole > 0) {
            cylinder(h=height, d=screw_hole, $fn=Mx_fn);
			translate([0,0,height*0.6])
				cylinder(h=screw_hole*3*0.8, r2=screw_hole*2, r1=0);
        // fn=Mx_fn makes it self threading
		}
    }
}

			 
//make_posts(rpib);
module make_posts(s, posts=[[1,2],[3,4]], offset_x=3, offset_y=3,  post_radius = 3, screw_hole=M3_screw_hole) {    
    translate(s)
    {    
		for (l = posts)
		{
			translate([offset_x+l[0],offset_y+l[1],wall_thickness]) 
				post(post_height, post_radius, screw_hole);
		}		
	}       
}

module phono_jack() {
    cylinder(h=wall_thickness, d=phono_jack_hole_diameter);    
}

module term_post(height) {
    
    difference() {
        cylinder(h=term_strip_post_height, r1=post_radius,r2=post_radius/1);
        cylinder(h=term_strip_post_height, d=M3_screw_hole, $fn=Mx_fn);
    }
}

module fillet(rot, r, h) {
    translate([r / 2, r / 2, h/2])
    rotate([0,0,rot]) difference() {
        cube([r + 0.01, r + 0.01, h], center = true);
        translate([r/2, r/2, 0])
            cylinder(r = r, h = h + 1, center = true);
    }
}

//mounting_tab(0);
module mounting_tab(rot) {
    tab_thickness = wall_thickness*1.5;
    width = outer_width-(wall_thickness*2);
    hole_from_end = (width/3)/2;
    half_tab_size = tab_size/2;
    rotate([0,0,rot]) {
        difference() {
            cube([width,tab_size,tab_thickness]);
            fillet(0,half_tab_size, tab_thickness);
            translate([width-(tab_size/2),0,0]) 
                fillet(90,half_tab_size, tab_thickness);
            translate([hole_from_end,half_tab_size,tab_thickness/2]) 
                cylinder(d = tab_holes, h = tab_thickness, center = true);
            translate([width-hole_from_end,half_tab_size,tab_thickness/2]) 
                cylinder(d = tab_holes, h = tab_thickness, center = true);
        }
        translate([width,tab_size,tab_thickness*2])
            rotate([180,90,0])
                fillet(90,tab_thickness, width);
    }
}
//small_mounting_tab(rot);
module small_mounting_tab(rot) {
    tab_thickness = wall_thickness*1.5;
    width = 20;
    hole_from_end = width/2;
    half_tab_size = tab_size/2;
    rotate([0,0,rot]) {
        difference() {
            cube([width,tab_size,tab_thickness]);
            fillet(0,half_tab_size, tab_thickness);
            translate([width-(tab_size/2),0,0]) 
                fillet(90,half_tab_size, tab_thickness);
            translate([hole_from_end,half_tab_size,tab_thickness/2]) 
                cylinder(d = tab_holes, h = tab_thickness, center = true);
            *translate([width-hole_from_end,half_tab_size,tab_thickness/2]) 
                cylinder(d = tab_holes, h = tab_thickness, center = true);
        }
        translate([width,tab_size,tab_thickness*2])
            rotate([180,90,0])
                fillet(90,tab_thickness, width);
    }
}

module make_rpi_b_posts(y=4) {
//rpib_y = 4;  //  adjust the y offset
// /[  name,      [location],    height,    ength, width, mount_length,   mount_width,  mount_offsetx, mount_offsety]

rpib= ["RPIB",   [3,rpib_y,0],  post_height,  85,     56,  85-25.5-5,     56-18-12.5,     25.5,              18];
	
	length = 85.6;
	width = 54;
	
	post_x= length - 5-25.5;
	post_y = width - 18-12.5   +2; // seems the B drawings are off so need the "+2"
    echo("post_Y", post_y);
		
	post_locs=[[0,0], [0,post_y], [post_x,0], [post_x, post_y]];
		
	make_posts([wall_thickness+1,y,0], post_locs, offset_x=25.5, offset_y=18);
	make_outline([wall_thickness+1,y,0], name="RPI B", width=width, length=length); 

}

module make_rpi_3_posts(y=4) {
    // board size
	length = 85;
	width = 56;
	// posts 
	post_x=  58.2;
	post_y = 49;
    echo("post_Y", post_y);
		
	post_locs=[[0,0], [0,post_y], [post_x,0], [post_x, post_y]];
		
	make_posts  ([wall_thickness+2,y,0], post_locs, offset_x=3.2, offset_y=3.7, screw_hole=M2_5_screw_hole);
	make_outline([wall_thickness+1,y,0], name="RPI3 v2", width=width, length=length); 

}

module make_rpi_z_posts(y=4) {

	length = 65;
	width = 30;
	
	post_x=  58;
	post_y = 23;
    echo("post_Y", post_y);
		
	post_locs=[[0,0], [0,post_y], [post_x,0], [post_x, post_y]];
		
	make_posts  ([wall_thickness+1,y,0], post_locs, offset_x=3.4, offset_y=3.7, screw_hole=M2_5_screw_hole);
	make_outline([wall_thickness+1,y,0], name="RPIZ v1", width=width, length=length); 

}
