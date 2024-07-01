//  tools. common shared stuff
lth_y=36;
width_x=82;

pin_d = 2.7;
post_d = pin_d+1.6;
starting_offset_x = 4;
starting_offset_y = 4;
spacing_y = 28;
spacing_x = 20;
set_spacing_x = spacing_x+7;
pad_height = 1;
post_height = pad_height+2;

// base_thickness+3 = base_thickness+3;

difference()
{
    make_d1_mini_mount(0);
    //translate([35,0,0]) cube([50,50,10]);
}
module make_d1_mini_mount(base_thickness)
{
    //translate([0,-lth_y/2,0])
    //difference()
    {
        union () 
        {
            _base(base_thickness);
            translate([starting_offset_x, starting_offset_y,0])
                _make_a_set(base_thickness);
            translate([starting_offset_x+set_spacing_x, starting_offset_y,0])
                _make_a_set(base_thickness);
            translate([starting_offset_x+set_spacing_x*2, starting_offset_y,0])
                _make_a_set(base_thickness);
           
        }
        *translate([starting_offset_x, starting_offset_y, 0])
            make_d1_mini_screw_holes(base_thickness);
    }
}

module _make_a_set(base_thickness)
{
    _post([0,0,0], base_thickness+post_height, post_d);
    _post([0,  spacing_y,0], base_thickness+post_height, post_d);
    _post([spacing_x,0,0],  base_thickness+post_height, post_d);
    _post([spacing_x, spacing_y,0], base_thickness+post_height, post_d);

    _post([0,0,0], base_thickness+post_height+3, pin_d);
    _post([0,  spacing_y,0], base_thickness+post_height+3, pin_d);
    _post([spacing_x,0,0],  base_thickness+post_height+3, pin_d);
    _post([spacing_x, spacing_y,0], base_thickness+post_height+3, pin_d);
}


module make_d1_mini_screw_holes(base_thickness)
{
    _screw_hole([0,0,0], base_thickness+post_height, pin_d);
    _screw_hole([0, spacing_y,0], base_thickness+post_height, pin_d);
    _screw_hole([spacing_x,0,0], base_thickness+post_height, pin_d);
    _screw_hole([spacing_x, spacing_y, 0], base_thickness+post_height, pin_d);
}

module _base(base_thickness)
{
    cube([width_x,lth_y,base_thickness+pad_height]);
}

module _post(loc, height, diameter) {
    translate(loc)
        cylinder(h=height, d=diameter, $fn=120);
}

module _screw_hole(loc, height, screw_hole, fn=12)
{
    translate(loc)
        cylinder(h=height, d=screw_hole, $fn=fn); 
        // fn=Mx_fn makes it self threading
}

