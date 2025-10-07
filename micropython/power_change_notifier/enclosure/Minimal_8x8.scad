/*
modular enclosure for ESP32-S2 style of wemos D1 Mini 
MIT Licence
Copyright 2023-2025 James Dodgen
this gets copied and renamed for each new enclosure
the the previous enclosures can be configured 
*/

//make_one(letter="D");
//make_relay_lid(letter="D");


module make_one(letter="X")
{
    translate([2,0,0]) make_s2_base();
    make_relay_lid(letter=letter);
}

//make_lids("HHHXXZZTT", chars_per_row=5);
module make_lids(letters, chars_per_row=5)
{
   x_spacing = 55;
   y_spacing = 32;
   char_list = [ for (i = [0 : len(letters) - 1]) letters[i] ];
   
   for (x = [0: floor(len(letters)/chars_per_row)])
   {      
       base = x*chars_per_row;
       echo(">>>> base =",base) 
       
       for (y =  [1:chars_per_row])
       {
           chr_ndx = base+y-1;
           echo("y=",y, " x=",x, "chr_ndx=", chr_ndx)
           if (chr_ndx < len(char_list))
           {
               echo("print this:", char_list[chr_ndx], chr_ndx);
               translate([x*x_spacing, y*y_spacing, 0])
                    make_relay_lid(letter=char_list[chr_ndx]);
           }
       } 
   }
   
    
}
letter="T";
tabs = false;
short_base = true;  // false makes 
overide_z = 10.5; // if  greater than  0 it overrides the short and tall boxes also this + 11 is the total Z
make_somthing = 1;    // 1 base, 2=lid, 3 buttons
if (make_somthing == 1) {
    make_s2_base();
} else if (make_somthing == 2) {
    make_relay_lid(letter=letter);
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
s2_y=27;
s2_x=35;
s2_thickness=4;
shell_wall_thickness = 1.5;
shell_post_d = 7;

usb_c_hole_width = 13;
usb_c_hole_height = 8;


double_cutout_y = 8.3;
double_cutout_x = 13.5;
double_cutout_z = shell_wall_thickness;
double_cutout_y_offset = 14;
double_cut_out = false;

8x8_cutout_x = 21;
8x8_cutout_y = 21;
8x8_loc = [0,0,0];  
8x8_cutout = true;

offset_z = (overide_z > 0) 
    ? overide_z
    : (short_base == true) 
    ? 0 
    : 12.4;  // 13

shell_x = s2_x + (shell_wall_thickness*2);   // adjustments off of S2 D1 Mini
shell_y = s2_y + (shell_wall_thickness*2);
shell_z = offset_z+usb_c_hole_height+shell_wall_thickness*2;

holes_cutout_z = usb_c_hole_height+shell_wall_thickness*2;

button_cutout_z =
    (overide_z > 0) 
    ? holes_cutout_z/2-0.4
    : (short_base == true) 
    ? holes_cutout_z/2-0.4 
    : shell_z-usb_c_hole_height+2.0;

usb_c_hole_z = (overide_z > 0) 
    ? holes_cutout_z/2-usb_c_hole_height/2
    : (short_base == true) 
    ? holes_cutout_z/2-usb_c_hole_height/2 
    : shell_z -usb_c_hole_height-2;

posts_total_height = (holes_cutout_z/2)-2.5; //usb_c_hole_height/2+shell_wall_thickness-2.5;



module make_s2_base() {
    difference()
    {
        union()
        {
            if (short_base == true ||  override_z > 0) 
                make_s2_mini_mount(front_stops=false);
            //translate([-(shell_x-s2_x)+shell_wall_thickness,(-(shell_y-s2_y)/2),0])
            {
                shell();
            }
        }
        
        translate([s2_x+0.5, (shell_y-usb_c_hole_width)/2, usb_c_hole_z])
            usb_c_hole();
        hole_d = 4;
        
        
        translate([shell_x-shell_wall_thickness-(hole_d/2)-2,0, button_cutout_z]){
            rotate([-90,0,0])cylinder(h=shell_y, d=hole_d, $fn=30);
        }
        translate([shell_x-shell_wall_thickness-(hole_d/2)-4, (shell_y-hole_d/2)-2.5, button_cutout_z]) {
            cube([hole_d,hole_d,40]);
        }
        
        if (double_cut_out == true)
            translate([shell_x-double_cutout_x-3, 
            shell_y-double_cutout_y-double_cutout_y_offset, 0])
                cube([double_cutout_x, double_cutout_y, double_cutout_z]);
        if (8x8_cutout == true)
            translate([shell_x*0.6, shell_y*.47, 0])
                    rotate([0,0,90])
                        center_text(letter, size=8, extrude=shell_wall_thickness*2);
        
            
   
    }
    
    
}

//lid_mount_Loc_1 = [shell_x/2,shell_wall_thickness,shell_z-2];
//lid_mount_Loc_2 = [shell_x/2,shell_y-shell_wall_thickness,shell_z-2];

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
        mid_y = shell_y/2-0.5;
       
        make_slot([0,mid_y,   3],height=shell_z-5);
        make_slot([0,mid_y+4, 3],height=shell_z-5);
        make_slot([0,mid_y-4, 3],height=shell_z-5);
        make_slot([0,mid_y+8, 3],height=shell_z-5);
        make_slot([0,mid_y-8, 3],height=shell_z-5);
        //make_slot([0,mid_y-12,3],height=shell_z-5);
        //make_slot([0,mid_y+12,3],height=shell_z-5);
        //make_slot([0,mid_y-16,3],height=shell_z-5);
        //make_slot([0,mid_y+16,3],height=shell_z-5);
        *translate([33,0.5,9])
            rotate([90,0,0])
                center_text("R", size=5, extrude=1.2);
        *translate([33,shell_y+0.7,9])
            rotate([90,0,0])
                center_text("O", size=5, extrude=1.2);       
        
    }
    //lid_mount(lid_mount_Loc_1, rot=0);
    //lid_mount(lid_mount_Loc_2, rot=180); 
}

//make_relay_lid();

module make_relay_lid(letter="W")
{
    hat_x = 32;
    hat_y = 26.5;
    lip_depth = 2.5;
    shrinkage = 0.25;
    lip_width = 4.7;
    slop = (shrinkage+shell_wall_thickness);
    tab_height= 3.5;
    led_view_hole = 4;
    lip_x = shell_x-slop*2;
    lip_y = shell_y-slop*2;
    rotate([0,180.0])  // print upside down
    {
    difference()
    {
        union()
        {
            
            difference()
            {
                union()
                {
                    color("orange") cube([shell_x, shell_y, shell_wall_thickness]);
                    if (8x8_cutout == false)
                    {
                        hold_down_width=6;
                        translate([3,(shell_y-hold_down_width)/2, -tab_height]) 
                            cube([3,hold_down_width,tab_height]);
                    }
                    difference()
                    {
                        //translate([shrinkage+shell_wall_thickness, 
                             //shrinkage+shell_wall_thickness,-lip_depth])
                        translate([(shell_x-lip_x)/2, (shell_y-lip_y)/2, -lip_depth])
                        {
                            color("green") cube([lip_x, lip_y, lip_depth]);
                        }
                        cut_out_x = lip_x-lip_width*2+10;
                        cut_out_y = lip_y-lip_width*2+4.5;
                        //translate([shrinkage+shell_wall_thickness/2, 
                        //shrinkage+shell_wall_thickness/2,   0])
                        translate([(shell_x-cut_out_x)/2-shrinkage, (shell_y-cut_out_y)/2,  -lip_depth])
                                cube([cut_out_x, cut_out_y, lip_depth]);
                    }
                    hold_down_h = 6.7;
                    hold_down_d = 3;
                    if (8x8_cutout == false)
                    {
                        translate([(lip_x+hold_down_d/2+shrinkage)-hold_down_d/2, 
                                  (hold_down_d/2+shrinkage)+hold_down_d/2,   -hold_down_h])
                            cylinder(d=3, h=hold_down_h, $fn=40);
                        translate([(lip_x+hold_down_d/2+shrinkage)-hold_down_d/2,
                            lip_y-(hold_down_d/2-shrinkage)+hold_down_d/2,-hold_down_h])
                            cylinder(d=3, h=hold_down_h, $fn=40);
                    }
                }
                
                view_hole_h = shell_wall_thickness+lip_depth;
                if (8x8_cutout == true)
                {
                    translate([shell_x-8x8_cutout_x-9, 
                        shell_y-8x8_cutout_y/2-15, 0])
                    cube([8x8_cutout_x, 8x8_cutout_y, shell_wall_thickness]);
                } else {
                translate([slop, (-led_view_hole/2)+shell_y/4.16, 
                        -view_hole_h+shell_wall_thickness])
                    cube([led_view_hole,led_view_hole, view_hole_h]); 
                if (overide_z > 0)
                    translate([shell_x*0.6, shell_y*.47, 0])
                        rotate([0,0,90])
                            center_text(letter, size=8, extrude=shell_wall_thickness*2);
                }                
            }
            
            
        }
    }
    if (tabs == true)
    {
        width=12;
        translate([(shell_x/2)+(width/2),shell_y-4,0]) //[4,((shell_y)/2)+(width/2),0])
            rotate([0,0,90])
                tab(width=width, thickness=shell_wall_thickness,hole_d=5, $fn=60);
        translate([(shell_x/2)-(width/2),(width/2)-2,0])
            rotate([0,0,-90])
                tab(width=width, thickness=shell_wall_thickness,hole_d=5, $fn=60);
    }
    }
    
}
*translate([4,(shell_y-slop*2)/2,0])
rotate([0,0,180])
tab();
module tab(width=10, thickness=3,hole_d=3)
{
    difference()
    {
        union()
        {
         cube([width,width,thickness]); 
         translate([width,width/2,0])
                cylinder(d=width, h=thickness);
        }
        translate([width,width/2,0])
            cylinder(d=hole_d, h=thickness*2);
    }
}

/* 
START old Wemos S2 Mini mount code
*/



post_d = M2_screw_hole+1.5;
hole_offset_x = shell_wall_thickness+post_d/2; 
hole1_offset_y = shell_wall_thickness+(post_d/2)+1;
hole2_offset_y= hole1_offset_y+20.4;  

hole1_loc = [hole_offset_x, hole1_offset_y,0];
hole2_loc = [hole_offset_x, hole2_offset_y,0];
button_hole_d = 4;
module make_s2_mini_mount(button_guides=true, front_stops=true)
{
    
    suport_x = s2_x - post_d/2;
    suport_post1_loc = [suport_x, hole1_offset_y, 0];
    suport_post2_loc = [suport_x, hole2_offset_y, 0];
    
    //translate([-1,-1,0]) cube([s2_x+2,s2_y+2,s2_thickness]);
    *if (button_guides == true) {
        translate([s2_x-8,-3.5,0]) 
            cube([8, 2, 13]);
        translate([s2_x-8,s2_y+3,0]) 
            cube([8, 2, 13]);
    }
    post(hole1_loc, posts_total_height, post_d);
    post(hole2_loc, posts_total_height, post_d);
    post(suport_post1_loc, posts_total_height, post_d);
    post(suport_post2_loc, posts_total_height, post_d);

    // side supports
    //translate([-2.4,-2.3,0]) cube([28,2,10]);
    //translate([-2.4,s2_y+0.3,0]) cube([29,2,10]);

    // end sppports
    //translate([-2.4, -0.5, 0]) cube([2,5,10]);
    //translate([-2.4, s2_y-5+0.5, 0]) cube([2,5,10]);
    
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
        //screw_hole(hole1_loc, posts_total_height, M2_screw_hole);
        //screw_hole(hole2_loc, posts_total_height, M2_screw_hole);
        //antenna_cutout();
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
    translate([-2, usb_c_hole_height/2, usb_c_hole_height/2])
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
    filler_block_y = usb_c_hole_width - usb_c_hole_height;
    translate([-2,usb_c_hole_height/2,0])
        cube ([cut_out_height, filler_block_y, usb_c_hole_height]);
    
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

//linear_extrude(height = 5) import(file="stencil_TNH.dxf", layer="A", scale=1);
//center_text("B", size=7, extrude=shell_wall_thickness); 
module center_text(text, size, font="Liberation Mono:style=Regular", width=0, length=0, extrude=0.6) {
    $fn = 30;
    translate([-5.5, -4, -extrude/2]) 
      scale([1.3,1,1])
        linear_extrude(extrude) 
            import(file="stencil_TNH.dxf", layer=text, scale=1);
            //text(text, size=size, font=font, halign="center", valign="center");
}
