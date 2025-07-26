module fillet(rot, r, h) {
    //translate([r / 2, r / 2, h/2])
		//rotate([0,0,rot]) 
			difference() {
				//cube([r + 0.01, r + 0.01, h], center = true);
				fillet_cube(rot=rot, r=r, h=h);
				fillet_cylinder(rot=rot, r=r, h=h);
				
				//translate([r/2, r/2, 0])
					//cylinder(r = r, h = h + 1, center = true);
			}
}

module fillet_cube(rot=0, r=0, h=0)
{
	translate([r / 2, r / 2, h/2])
	rotate([0,0,rot]) 
		cube([r + 0.01, r + 0.01, h], center = true);
}

module fillet_cylinder(rot, r, h)
{
	translate([r / 2, r / 2, h/2])
	rotate([0,0,rot]) 
		translate([r/2, r/2, 0])
			cylinder(r = r, h = h + 1, center = true);	
}

