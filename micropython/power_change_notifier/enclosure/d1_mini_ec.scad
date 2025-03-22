//  MIT license copyright 2025 Jim Dodgen
use <usb_hole.scad>
use <fillet.scad>


//LED_top(flat=true, height=3.7, cut_text="U", xoff=9,yoff=32) ; //3.7);
LED_top(flat=true, height=3.7, cut_text="+", xoff=9,yoff=32) ; //3.7);

//rotate([180,0,0]) 
   //LED_pizo_buzzer_top();
   //empty_top();
//translate([-8,0,0]) 

//make_button();
// rotate([180,0,0]) LED_pizo_buzzer_top();
//
//base_unit();

lth_y=25.4;
width_x=34.3;

base_x = 63;
base_y = 50;

wall_thickness = 2;

outer_x = base_x+wall_thickness;
outer_y = base_y+wall_thickness;
font = "Futura Black Regular"; //"Cambria:style=Bold"; /// "Futura Black Regular" princess font
base_thickness=2.5;

usb_hole_height = base_thickness + 3;
support_wall = 2;

bottom_wall_height = base_thickness+16;

top_wall_height = 15;
top_thickness=2.5;

total_height = base_thickness+3;

hole_d = 2.0;
hole_offset_x = 3; 
hole1_offset_y = 2.5;
hole2_offset_y= hole1_offset_y+20.4;

inner_r=23;
offset = -12;
cover_wall_r = 2;

cover_z= 25;
M3_screw_hole = 3.1; 
M3_clearence_hole = 3.6; 
M3_head_clearence_hole = 6.3;
M3_Mx_fn = 6; // self tapping 

M2_5_screw_hole = 2.75; 
M2_5_clearence_hole = 3.1; 
M2_5_head_clearence_hole = 6.2;


// M2 screws
m2_screw_hole = 2.2;
Mx_fn = 10; // self tapping 

m2_hole1_loc = [hole_offset_x, hole1_offset_y,0];
m2_hole2_loc = [hole_offset_x, hole2_offset_y,0];
m2_post_d = m2_screw_hole+1.5;

suport_x = width_x - m2_post_d/2;
suport_post1_loc = [suport_x, hole1_offset_y+1, 0];
suport_post2_loc = [suport_x, hole2_offset_y, 0];



module base_unit()
{
difference()
{
    union()
    {
        translate([11,0,0]) hw_mount();
            support(usb_hole_height, support_wall);
        
        translate([22.5,0,0])
        {
            difference()
            {
                union()
                {
                    translate([0,0,base_thickness/2])
                    {
                    // Base 
                        cube([base_x, base_y, base_thickness], center=true) ;
                    }
                    translate([0,0,bottom_wall_height/2]){
                        difference()
                        {
                            // lower shell
                            
                            cube([outer_x, outer_y, bottom_wall_height], center=true) ;
                            cube([base_x, base_y, bottom_wall_height], center=true) ;
                        }
                        case_mounts();
                    }
                }
                translate([0,0,bottom_wall_height*1.5])
                {
                    case_mount_holes();
                }

            }
        }
        
    }
    cutout(usb_hole_height);
    translate([base_x,0,base_thickness+2]) color("red") make_usb_b_slot(rotate=90);
}
}


// make custom top here
button_diameter=8;
button_length=12;
tab_length = 1.9;
module make_button()
{
    $fn=60;
    cylinder(h = button_length, d = button_diameter);
    cylinder(h = tab_length, d = button_diameter*1.5);
    translate([0,0,button_length]) scale([1,1,0.5]) sphere(d=button_diameter);
}


module LED_pizo_buzzer_top()
{
    bung_thickness=top_thickness*2;
    button_hole=9;
    bung_loc=[21,26,-top_thickness-3];
    button_loc=[21,26,-bung_thickness-top_thickness];
    led_loc = [31,20,-top_thickness];
    led_hole = 7.5;
    vent_indent_y = 19;
    pezo_vent_x=48;
    vent_spacing=3;
    
    
    difference() 
    {
        $fn = 120;
        union()
        {
            bubble_top();
            // additions, inverted viewing at interface
            translate(bung_loc)
                cylinder(h = bung_thickness, d = button_hole*1.5);
            //usb_stop();
            //translate([0, outer_y/2-usb_width/2, -(usb_limit-top_thickness)])
                //cube([usb_depth, usb_width, usb_limit]);
        }
        // cutouts
        //translate([0,0,-top_thickness])
        {
        translate(led_loc)
            cylinder(h = top_thickness, d = led_hole);

        translate(button_loc)
            cylinder(h = bung_thickness*2, d = button_hole);
        pezo_vent_y = -top_thickness;
        translate([pezo_vent_x, vent_indent_y, pezo_vent_y])
            cube([2, outer_y-vent_indent_y*2, top_thickness]);
        translate([pezo_vent_x+vent_spacing, vent_indent_y, pezo_vent_y])
            cube([2, outer_y-vent_indent_y*2, top_thickness]);
        translate([pezo_vent_x-vent_spacing, vent_indent_y, pezo_vent_y])
            cube([2, outer_y-vent_indent_y*2, top_thickness]);
        }
    }
}

module empty_top()
{
    led_loc = [31,20,-top_thickness];
    led_hole = 7;

    flat_top();

}
//
module LED_top(flat=false, height=top_thickness,cut_text=false, xoff=20, yoff=12)
{
    led_loc = [29.5,-21,-height/2];
    led_hole = 7;
    
    difference() 
    {
        $fn = 80;
        if (flat == false)
            bubble_top();
        else
            flat_top(height=height);
        // cutouts
        translate(led_loc)
            cylinder(h = height, d = led_hole);
        if (cut_text)
        {
            color("red") translate([xoff,-yoff, height*3/2])
                rotate([180,0,90]) 
                    linear_extrude(height*3)
                        text(cut_text, size=12, font=font);
        }
    }
    
}
 

//LED3_top(flat=true, height=5) ; //3.7);
module LED3_top(flat=false, height=top_thickness)
{
    spacing = 2.54*2;
    led_loc1 = [29.5,-21,-height/2];
    led_loc2 = [29.5+spacing,-21,-height/2];
    led_loc3 = [29.5+(spacing*2),-21,-height/2];
    led_hole = 7;
    $fn = 120;
    difference() 
    {
       
        if (flat == false)
            bubble_top();
        else
            flat_top(height=height);
        // cutouts
        translate(led_loc1)
            cylinder(h = height, d = led_hole);
        translate(led_loc2)
            cylinder(h = height, d = led_hole);
        translate(led_loc3)
            cylinder(h = height, d = led_hole);
        translate([15,4,5])
            rotate([90,0,0]) 
                cylinder(h = 20, d = 5);
    }
    
}

module board_stop(height=top_wall_height)
{
    limit=height-2.5;
    width = 17;
    depth=10;
    translate([outer_x/2-depth, -width/2, -height/2+0.3])
    difference() 
    {
        cube([depth, width, height]);
        translate([9,0,0])
            rotate([-0,35,0])
                color("green") cube([depth, width, height*2]);
    }
}

//usb_stop();
module usb_stop(height=top_wall_height)
{
    usb_limit=height-2.5;
    usb_width = 15;
    usb_depth=8;
    translate([-outer_x/2, -usb_width/2, -usb_limit+height/2])
    difference() 
    {
        cube([usb_depth, usb_width, usb_limit]);
        translate([9,0,0])
            rotate([-0,-35,0])
                color("red") cube([usb_depth, usb_width, usb_limit*2]);
    }
}

//translate([0,80,0]) 
//flat_top(height=3.7);
module flat_top(height=3.7)
{
    shrink=-2;
    fillet_adjustment = -7;
    rotate([180,0,0,]) 
    translate([outer_x/2,outer_y/2,-height/2]) //-top_thickness]) 
    {
        difference()
        {
            difference()
            {  
                union()
                {
                    difference()
                    {
                        cube([outer_x, outer_y, 5], center=true) ;
                        translate([0, 0, -top_thickness/2]) 
                            shell(height=height, shrink=shrink, fillets=true, adjust_fillet_r=fillet_adjustment);
                    }
                    case_mounts(height=height, filler_cubes=true);
                    usb_stop(height=height);
                    board_stop(height=height);
                }
            }
            difference()
            {
                cube([outer_x, outer_y, height+10], center=true) ;
                 shell(height=height, fillets=true,  adjust_fillet_r=fillet_adjustment);
            }
            translate([0, 0, height/2])
                case_mount_holes(height=height, size=M3_clearence_hole, fn=30, lid_cutouts=true,tab_thickness=1.5);

        }
        /*translate([0, 0, height/2])
            case_mount_holes(height=height, size=M3_clearence_hole, fn=30, lid_cutouts=true); */

    }
}

//bubble_top();
module bubble_top()
{
    shrink=-2;
    //rotate([180,0,0,]) 
    //translate([outer_x/2,outer_y/2,-top_wall_height/2]) //-top_thickness]) 
    {
        difference()
        {
            difference()
            {  
                union()
                {
                    difference()
                    {
                        cube([outer_x, outer_y, top_wall_height], center=true) ;
                        translate([0, 0, -top_thickness/2]) 
                            shell(shrink=shrink, adjust_fillet_r=-1);
                    }
                    case_mounts(top_wall_height, filler_cubes=true);
                    usb_stop();
                }
                //translate([0, 0, -top_thickness/2]) 
                    //shell(shrink=shrink, adjust_fillet_r=-1);
            }
            difference()
            {
                cube([outer_x, outer_y, top_wall_height+10], center=true) ;
                shell();
            }
        //}{
            translate([0, 0, top_wall_height/2])
            {
                case_mount_holes(height=top_wall_height, size=M3_clearence_hole, fn=30, lid_cutouts=true);
            }
            //translate([0,0,0]) shell();
            // translate([-shrinkage_forwall, -shrinkage_forwall/2, shrinkage_forwall/2])
            //translate([0, 0, -top_thickness/2]) 
                //shell(shrink=shrinkage_forwall, adjust_fillet_r=-1);
            //translate([50,0,0]) cube([100,100,100], center=true);
        }
        /*translate([0, 0, top_wall_height/2])
            {
                case_mount_holes(height=top_wall_height, size=M3_clearence_hole, fn=30, lid_cutouts=true);
            } */
    }
}

//shell();
module shell(height=top_wall_height, shrink=0, adjust_fillet_r=0, fillets=true)
{
    $fn=180;
    testing=0;
    difference()
    {
        fillet_r=10+adjust_fillet_r;
        x=outer_x+shrink;
        y=outer_y+shrink;
        top=height; //+shrink;
        if (adjust_fillet_r != 0)
            union()
            {
                cube([x, y, top], center=true);
                case_mounts(height,filler_cubes=true);
            }
        else
            cube([x, y, top], center=true);
        if (fillets == true)
        {
            $fn=180;    
            fillet_z = top/2-fillet_r;
            translate([x/2-fillet_r, y/2-testing, fillet_z]) 
                rotate([90,0,0]) 
                    color("red") fillet(rot=180, r=fillet_r, h=y);
            translate([-x/2, y/2-testing, fillet_z]) 
                rotate([90,0,0]) 
                    color("red") fillet(rot=270, r=fillet_r, h=y);

            translate([x/2, y/2-testing, fillet_z]) 
                rotate([90,0,-90]) 
                    color("green") fillet(rot=270, r=fillet_r, h=x);
            translate([x/2, -y/2+fillet_r-testing, fillet_z]) 
                rotate([90,0,-90]) 
                    color("green") fillet(rot=-180, r=fillet_r, h=x);
        }

        //cube([base_x, base_y, height], center=true);
    }
}


*difference()
{
    case_mounts(filler_cubes=true);
    case_mount_holes(top_wall_height, size=M3_clearence_hole, fn=30, lid_cutouts=true);
}
//LED_pizo_buzzer_top();
case_mount_d=M3_head_clearence_hole+0.5;
case_offset = (case_mount_d/2)-wall_thickness;
screw_tab_thickness = 2;  // default
filler_size=7;
board_holddown = 14;
filler_adjustment = 1.7;
filler_scale = 0.65;
module case_mounts(height=bottom_wall_height, filler_cubes=false)
{
    
    case_mount_1 = [(base_x/2)-case_offset, (base_y/2)-case_offset,-height/2];
    case_mount_2 = [-(base_x/2)+case_offset, -(base_y/2)+case_offset,-height/2];
    case_mount_3 = [-(base_x/2)+case_offset, (base_y/2)-case_offset,-height/2];
    case_mount_4 = [(base_x/2)-case_offset, -(base_y/2)+case_offset,-height/2];

    post(case_mount_1, height, case_mount_d);
    post(case_mount_2, height, case_mount_d);
    post(case_mount_3, height, case_mount_d);
    post(case_mount_4, height, case_mount_d);

    if (filler_cubes == true) 
    {
        filler_block([base_x/2-filler_size+filler_adjustment, base_y/2-filler_size+filler_adjustment, -height/2], height); 
        filler_block([base_x/2-filler_size+0.5, -(base_y/2)-0.5, -height/2], height, rotate=90+45); 
        filler_block([-base_x/2+0.7, -(base_y/2)+filler_adjustment-1, -height/2], height, rotate=-45-90); 
        filler_block([-base_x/2-0.5, (base_y/2)-filler_size+0.5, -height/2], height,  rotate=-45); 

        /*filler_block([base_x/2-filler_size+filler_adjustment, base_y/2-filler_size+filler_adjustment, -height/2], height); 
        filler_block([base_x/2-filler_size+0.5, -(base_y/2)-0.5, -height/2], height,                    rotate=90+45); 
        holddown=14;
        holddown_block([0, -(base_y/2),              -height/2], height=height, size=holddown); 
        holddown_block([-(base_x+holddown)/2,        (base_y/2-holddown),     -height/2], height=height, size=holddown); */
        
    }
}

module filler_block(t, height, rotate=45)
{
    translate(t)  
        rotate([0,0,-rotate]) 
            scale([1,filler_scale,1]) 
                rotate([0,0,rotate]) 
                    cube([filler_size,filler_size,height]);    
}

/*module holddown_block(t, size=7,height=100)
{
    translate(t)  
        cube([size,size,height]);    
}
*/
// case_mount_holes();
module case_mount_holes(height=bottom_wall_height, size=M3_screw_hole, fn=M3_Mx_fn, lid_cutouts=false, tab_thickness=screw_tab_thickness)
{
    
    case_mount_1 = [(base_x/2)-case_offset,  (base_y/2)-case_offset,  -height];
    case_mount_2 = [-(base_x/2)+case_offset, -(base_y/2)+case_offset, -height];
    case_mount_3 = [-(base_x/2)+case_offset, (base_y/2)-case_offset,  -height];
    case_mount_4 = [(base_x/2)-case_offset, -(base_y/2)+case_offset,  -height];

    color("green")
    {
        screw_hole(case_mount_1, height, size, fn=fn);
        screw_hole(case_mount_2, height, size, fn=fn);
        screw_hole(case_mount_3, height, size, fn=fn);
        screw_hole(case_mount_4, height, size, fn=fn);
    }
    echo("height=", height);
    echo("tab_thickness", tab_thickness);
    
    if (lid_cutouts == true)
    {
        screw_cutout_d = case_mount_d+1;
        echo("tab_thickness", tab_thickness);
        
        color("red")
        
        //translate([0,0,-tab_thickness+(height/2)]) 
        translate([0,0,tab_thickness]) 
        {
            post(case_mount_1, height, screw_cutout_d);
            post(case_mount_2, height, screw_cutout_d);
            post(case_mount_3, height, screw_cutout_d);
            post(case_mount_4, height, screw_cutout_d);
         }
    }
}

module cover(usb_hole_height)
{
    {
       difference()
       {
           cylinder(r=inner_r+cover_wall_r,h=cover_z);
           cylinder(r=inner_r,h=cover_z);   
       } 
    }
}

module hw_mount()
{
   //make_usb();
    translate([0,-lth_y/2,0]) 
        //rotate(90) 
            make_mount(base_thickness = base_thickness);
}

module hw_mount_cutout()
{
    make_usb_cutout();
    translate([0,-width_x/2,0]) 
        rotate(90) 
            make_mount_cutout(base_thickness = base_thickness);
}


module make_mount(base_thickness)
{
    difference()
    {
        union () 
        {
            base(base_thickness);
            post(m2_hole1_loc, total_height, m2_post_d);
            post(m2_hole2_loc, total_height, m2_post_d);
            post(suport_post1_loc, total_height, m2_post_d);
            post(suport_post2_loc, total_height, m2_post_d);
        }
        make_screw_holes();
    }
}

module make_screw_holes(base_thickness)
{
    screw_hole(m2_hole1_loc, total_height, m2_screw_hole);
    screw_hole(m2_hole2_loc, total_height, m2_screw_hole);
    //antenna_cutout(base_thickness);
}

module base(base_thickness)
{
    cube([width_x,lth_y,base_thickness]);
}


module post(loc, height, diameter) {
    translate(loc)
        cylinder(h=height, d=diameter, $fn=120);
}

module screw_hole(loc, height, screw_hole, fn=Mx_fn)
{
    translate(loc)
        cylinder(h=height, d=screw_hole, $fn=fn); 
}

module antenna_cutout(base_thickness)
{
    translate([0,hole1_offset_y+(m2_post_d/2)+0.7,0])
        cube([6, lth_y-hole1_offset_y-(m2_post_d*2), base_thickness]);
}
