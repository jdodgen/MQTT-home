/*
modular enclosure for ESP32-S2 style of wemos D1 Mini 
current shell lid is for a style of relay 
MIT 
Copyright 2023 James Dodgen

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”), 
to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, 
sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, 
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, 
DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN 
CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

version 1.1
*/

type = "proto"; //"cpu"; "relay"; "proto";

make_somthing = 2;    // 1 base, 2=lid, 3 buttons
if (make_somthing == 1) {
    make_s2_base();
} else if (make_somthing == 2) {
    make_relay_lid();
} else if (make_somthing == 3) {
    make_button();
    translate([6,0,0]) 
        make_button(long=true); // two needed, short for the "O" long for the "RST"
}

Mx_fn = 12; // self tapping 
M3_screw_hole = 2.8; 
M3_clearence_hole = 3.6; 
M3_head_clearence_hole = 6.3;

M2_5_screw_hole = 2.7; 
M2_5_clearence_hole = 3.1; 
M2_5_head_clearence_hole = 6.2;

M2_screw_hole = 2.16; 
M2_clearence_hole = 2.6; 

drill_length = 20;


shell_x = 34.3 + 10;   // adjustments off of S2 D1 Mini
shell_y = 25.4 + 17;

shell_z = 20;
shell_wall_thickness = 1.5;
shell_post_d = 7;



module make_s2_base() {
    difference()
    {
        union()
        {
            make_s2_mini_mount(front_stops=false);
            translate([-(shell_x-s2_x)+shell_wall_thickness,(-(shell_y-s2_y)/2),0])
            {
                shell();
            }
        }
        make_s2_mini_mount_cutout();
    }
}

lid_mount_Loc_1 = [shell_x/2,shell_wall_thickness,shell_z-2];
lid_mount_Loc_2 = [shell_x/2,shell_y-shell_wall_thickness,shell_z-2];

//shell();
module shell()
{
    difference()
    {
        cube([shell_x, shell_y, shell_z]) ;
        translate([shell_wall_thickness, shell_wall_thickness ,shell_wall_thickness])
        {
            cube([shell_x - (shell_wall_thickness*2), shell_y-shell_wall_thickness*2, shell_z]);
        }
        mid_y = shell_y/2;
        make_slot([0,mid_y,3],height=shell_z-5);
        make_slot([0,mid_y+4,3],height=shell_z-5);
        make_slot([0,mid_y-4,3],height=shell_z-5);
        make_slot([0,mid_y+8,3],height=shell_z-5);
        make_slot([0,mid_y-8,3],height=shell_z-5);
        make_slot([0,mid_y-12,3],height=shell_z-5);
        make_slot([0,mid_y+12,3],height=shell_z-5);
        make_slot([0,mid_y-16,3],height=shell_z-5);
        make_slot([0,mid_y+16,3],height=shell_z-5);
        translate([33,0.5,9])
            rotate([90,0,0])
                center_text("R", size=5, extrude=1.2);
        translate([33,shell_y+0.7,9])
            rotate([90,0,0])
                center_text("O", size=5, extrude=1.2);       
        
    }
    lid_mount(lid_mount_Loc_1, rot=0);
    lid_mount(lid_mount_Loc_2, rot=180); 
}

//make_relay_lid();
module make_relay_lid()
{
    hat_x = 32;
    hat_y = 26.5;
    lip_depth = 1.9;
    shrinkage = 0.25;
    lip_width = 4.7;

    rotate([0,180.0])  // print upside down
    difference()
    {
        union()
        {
            difference()
            {
                slop = (shrinkage+shell_wall_thickness);
                lip_x = shell_x-slop*2;
                lip_y = shell_y-slop*2;
                union()
                {
                    color("orange") cube([shell_x, shell_y, shell_wall_thickness*2]);
                    if (type == "cpu")   // make usb-c hold down post
                    {
                        height= 9;
                        width=5;
                        translate([3,(shell_y-width)/2, -height]) cube([2,width,height]);
                    }
                    difference()
                    {
                        translate([shrinkage+shell_wall_thickness, shrinkage+shell_wall_thickness,-shell_wall_thickness])
                        {
                            color("green") cube([lip_x, lip_y, lip_depth]);
                        }
                    }
                }
                
                if (type == "relay" ||  type == "cpu")
                {
                    cut_out_x = lip_x-lip_width*2;
                    cut_out_y = lip_y-lip_width*2;
                    translate([shrinkage+shell_wall_thickness, shrinkage+shell_wall_thickness,-shell_wall_thickness+1])
                        translate([(lip_x-cut_out_x)/2,(lip_y-cut_out_y)/2,-shell_wall_thickness])
                                    cube([cut_out_x, cut_out_y, lip_depth+shell_wall_thickness]);
                }
                if (type == "relay") // cut out relay slot
                 {
                    translate([shell_x-hat_x,(shell_y - hat_y)/2,-10]) 
                        cube([hat_x, hat_y, 20]);
                 }
                if (type == "proto")  // add slot for some wires
                {
                    // cut wire hole
                    translate([shell_x-6,(shell_y)/2, -5]) 
                        rotate([0,30,0])
                            scale([4,1,1])
                                cylinder(h = 10, r = 2, $fn=48);
                    // make room for proto board
                    cut_out_x = lip_x;
                    cut_out_y = lip_y-lip_width*2;
                    translate([-1, shrinkage+shell_wall_thickness,-shell_wall_thickness+1])
                        translate([(lip_x-cut_out_x)/2,(lip_y-cut_out_y)/2,-shell_wall_thickness])
                                    cube([cut_out_x, cut_out_y, lip_depth+shell_wall_thickness]);
                }
                lid_mount_clearance_hole(lid_mount_Loc_1, rot=0);
                lid_mount_clearance_hole(lid_mount_Loc_2, rot=180);

            relay_y = 16.2;
            relay_x= 31;
            relay_z = 10;
            
            *difference()  // resess for pcb
            {
                translate([shell_x-relay_x-2,(shell_y - hat_y-2)/2,shell_wall_thickness+0.3]) 
                    color("blue") cube([relay_x+2,hat_y+2,-(shell_wall_thickness-0.3)]);
                translate([shell_x-relay_x,(shell_y - relay_y)/2,0]) 
                    cube([relay_x,relay_y,relay_z]);
            }
        }
        }
        if (type == "relay")
        {
            /// relay cut outs for led and letters
            *translate([0,0,drill_length/2+shell_wall_thickness]) {
                lid_mount_clearance_hole(lid_mount_Loc_1, rot=0,hole_size=M3_head_clearence_hole);
                lid_mount_clearance_hole(lid_mount_Loc_2, rot=180,hole_size=M3_head_clearence_hole); 
            }
            translate([41,7,2])
                rotate([0,0,90])
                    center_text("NO", size=5, extrude=2);  
            translate([41,35,2])
                rotate([0,0,90])
                    center_text("NC", size=5, extrude=1.2);  
            // LED cutout
            translate([35,30,-5])
                    cube([3,4,20]);
        } 
    }
}

module lid_mount(xyz,  width=6, height=8, rot=0) {
    
    echo ("rotate", rot);
    if (rot == 0) { 
        translate([xyz.x+width/2, xyz.y, xyz.z])
            rotate([0,180,rot])
                raw_lid_mount(width=6, height=8);
    } else if ((rot == -90) || (rot == 270 )) {
        translate([xyz.x, xyz.y-width/2, xyz.z])
            rotate([0,180,rot])
                raw_lid_mount(width=6, height=8);
    } else if (rot == 90) {
        translate([xyz.x, xyz.y+width/2, xyz.z])
            rotate([0,180,rot])
                raw_lid_mount(width=6, height=8);
    } else if (rot == 180) {
        translate([xyz.x-width/2, xyz.y, xyz.z])
            rotate([0,180,rot])
                raw_lid_mount(width=6, height=8);
    }
}

//lid_mount([10,10,-2], rot=180); 
//lid_mount_clearance_hole([10,10,-2], rot=180); 
module lid_mount_clearance_hole(xyz,  width=6, height=8, rot=0, hole_size=M3_clearence_hole) {
 
    echo ("rotate", rot);
    if (rot == 0) { 
        translate([xyz.x, xyz.y+width/2, -drill_length/2])
           cylinder(h=drill_length, d=hole_size, $fn=40);
    } else if ((rot == -90) || (rot == 270 )) {
        translate([xyz.x+width/2, xyz.y, -drill_length/2])
            cylinder(h=drill_length, d=hole_size, $fn=40);
    } else if (rot == 90) {
        translate([xyz.x-width/2, xyz.y, -drill_length/2])
            cylinder(h=drill_length, d=hole_size, $fn=40);
    } else if (rot == 180) {
        translate([xyz.x, xyz.y-width/2, -drill_length/2])
            cylinder(h=drill_length, d=hole_size, $fn=40);   
    }
}

//raw_lid_mount();
module raw_lid_mount(width=6, height=8) {
    raw_height =20;
    //screw_depth= height*0.75;
    difference() 
    { 
        cube([width, width,raw_height]);			
        // chop off at 45 
        rotate([-45,0,0]) 
            translate([0,-50,height])
                cube([width, 100, raw_height*2]);		
        // screw hole
        translate([width/2, width/2,-2]) 
            cylinder(h=raw_height, d=M3_screw_hole, $fn=Mx_fn);                  
        translate([width/2,width/2,-2]) 
            fillet(180,width/2, raw_height+2, $fn=30);
        translate([0,width/2,-2]) 
                fillet(-90,width/2, raw_height+2, $fn=30);
    }                   
}

*difference() {
    make_s2_mini_mount(button_guides=false);
    make_s2_mini_mount_cutout();
    //translate([10,-50,0]) cube([100,100,100]);
}

/* 
START Wemos S2 Mini mount code
*/
s2_y=25.4;
s2_x=34.3;
s2_thickness=4;

total_height = s2_thickness+3;
usb_c_hole_width = 14;
usb_c_hole_height = 9;

hole_offset_x = 3; 
hole1_offset_y = 2.5;
hole2_offset_y= hole1_offset_y+20.4;  

hole1_loc = [hole_offset_x, hole1_offset_y,0];
hole2_loc = [hole_offset_x, hole2_offset_y,0];
post_d = M2_screw_hole+1.5;
button_hole_d = 4;
module make_s2_mini_mount(button_guides=true, front_stops=true)
{
    
    suport_x = s2_x - post_d/2;
    suport_post1_loc = [suport_x, hole1_offset_y+1, 0];
    suport_post2_loc = [suport_x, hole2_offset_y, 0];
    
    translate([-1,-1,0]) cube([s2_x+2,s2_y+2,s2_thickness]);
    if (button_guides == true) {
        translate([s2_x-8,-3.5,0]) 
            cube([8, 2, 13]);
        translate([s2_x-8,s2_y+3,0]) 
            cube([8, 2, 13]);
    }
    post(hole1_loc, total_height, post_d);
    post(hole2_loc, total_height, post_d);
    post(suport_post1_loc, total_height, post_d);
    post(suport_post2_loc, total_height, post_d);

    // side supports
    translate([-2.4,-2.3,0]) cube([28,2,10]);
    translate([-2.4,s2_y+0.3,0]) cube([29,2,10]);

    // end sppports
    translate([-2.4, -0.5, 0]) cube([2,5,10]);
    translate([-2.4, s2_y-5+0.5, 0]) cube([2,5,10]);
    
    if (front_stops == true) {  // where usb-c is
        translate([s2_x+0.5, -0.2, 0]) cube([2,5,10]);
        translate([s2_x+0.5, s2_y-5+0.2, 0]) cube([2,5,10]);
    }
}

//make_button();
module make_button(long=false) 
{
  lth=long?11:9;
  cylinder(h = lth , d = button_hole_d*0.8, $fn = 40); 
  cylinder(h = 1 , d = 4.5, $fn = 40); 
}

module make_s2_mini_mount_cutout()
{
    {
        screw_hole(hole1_loc, total_height, M2_screw_hole);
        screw_hole(hole2_loc, total_height, M2_screw_hole);
        antenna_cutout();
        color("purple")
        {
        //base_x = s2_x; // + 10;
        //base_y = s2_y; // + 17;
        //base_z = 20;
        //base_wall_thickness = 1.5;
            
        translate([s2_x+0.5, (s2_y-usb_c_hole_width)/2, s2_thickness+1])
            usb_c_hole();
        
       translate([s2_x-3.9, 0.5, s2_thickness+5]) 
            rotate([90,0.0])
                cylinder(h = 20 , d = button_hole_d, $fn = 40, center=false);
        
       translate([s2_x-3.9, s2_y, s2_thickness+5.2]) 
            rotate([270,0.0])
                cylinder(h = 20, d = button_hole_d, $fn = 40, center=false);
        }
    }
}

module post(loc,height, diameter) {
    translate(loc)
        cylinder(h=height, d=diameter, $fn=30);
}

module screw_hole(loc,height, screw_hole)
{
    translate(loc)
        cylinder(h=height, d=screw_hole, $fn=Mx_fn); 
        // fn=Mx_fn makes it self threading
}
module antenna_cutout()
{
    translate([-1,hole1_offset_y+(post_d/2)+0.7,0])
        cube([7, s2_y-hole1_offset_y-(post_d*2), s2_thickness]);
}

//usb_c_hole();
module usb_c_hole()
{
    cut_out_height = 20; //base_wall_thickness+4;
    translate([-2,usb_c_hole_height/2,usb_c_hole_height/2])
    {
        color("green") 
        rotate([0,90,0])
            cylinder(h = cut_out_height, d = usb_c_hole_height, center=false, $fn = 60);
    }
    translate([-2, usb_c_hole_width-(usb_c_hole_height/2), usb_c_hole_height/2])
    {
        color("orange") 
        rotate([0,90,0])
            cylinder(h = cut_out_height, d = usb_c_hole_height, center=false, $fn = 60);
    }
    filler_block = usb_c_hole_width-usb_c_hole_height-0.2;
    translate([-2,filler_block,0])
        cube ([cut_out_height, filler_block, usb_c_hole_height]);
    
    *translate([0.1,0,0])
        cube ([shell_wall_thickness, usb_c_hole_width, usb_c_hole_height]);
}
/*
END  wemos s2 mini mount */

// service routines

module fillet(rot, r, h) {
    translate([r / 2, r / 2, h/2])
    rotate([0,0,rot]) difference() {
        cube([r + 0.01, r + 0.01, h], center = true);
        translate([r/2, r/2, 0])
            cylinder(r = r, h = h + 1, center = true);
    }
}

//make_slot([0,0,0,]);
//make_slot([0,0,0,], rotate=1);
module make_slot(s, rotate=0, width=1.7, height=10) {
	thickness = 5;

    if (rotate == 1)	
    {
        translate([s.x-width/2, s.y-thickness/2, s.z])
        cube([width, thickness, height]);		
    }
    else
    {
        translate([s.x-thickness/2, s.y, s.z])
        cube([thickness, width, height]);
    }

}

module center_text(text, size, font="Liberation Mono:style=bold", width=0, length=0, extrude=0.6) {
    $fn = 30;
    translate([length, width, 0]) 
        linear_extrude(extrude) 
            text(text, size=size, font=font, halign="center", valign="center");
}
