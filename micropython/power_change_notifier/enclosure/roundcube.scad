RoundCube([20, 10, 10], center = false, radius = 1);

module RoundCube(size = [1, 1, 1], center = false,radius = 1.5,fn=60, round_top=true){

    obj_translate = (center == false) 
        ? [0, 0, 0] 
        : [ -(size[0] / 2),
            -(size[1] / 2),
            - (size[2] / 2)
          ];
    x = size[0];
    y = size[1];
    z = size[2];
    echo (obj_translate);
    translate(obj_translate) 
    {
        echo("obj_translate=",obj_translate);
        difference()
        {
            // do Z 
            cube(size, center=false); 
            translate([0,0,0]) fillet(0,r=radius,h=z*2, $fn=fn);
            translate([0,y-radius,0]) fillet(-90,r=radius,h=z*2, $fn=fn);
            translate([x-radius,y-radius,0]) fillet(180,r=radius,h=z*2, $fn=fn);
            translate([x-radius,0,0]) fillet(90,r=radius,h=z*2, $fn=fn);
            // do Y bottom
            translate([0,0,radius]) rotate([-90,0,0]) fillet(-90,r=radius,h=y*2, $fn=fn);
            translate([x-radius,0,radius]) rotate([-90,0,0]) fillet(180,r=radius,h=y*2, $fn=fn);
            // do X bottom
            translate([0,0,radius]) rotate([0,90,0]) fillet(90,r=radius,h=x*2, $fn=fn);
            translate([0,y-radius,radius]) rotate([0,90,0]) fillet(180,r=radius,h=x*2, $fn=fn);
            // do tops TBD not needed yet
            //if (round_top == true)
                // do Y top
                // do X top
                

        }
        
    }
}

module fillet(rot, r=1, h=10) {
    translate([r / 2, r / 2, h/2])
    rotate([0,0,rot]) difference() {
        cube([r + 0.01, r + 0.01, h], center = true);
        translate([r/2, r/2, 0])
            cylinder(r = r, h = h + 1, center = true);
    }
}