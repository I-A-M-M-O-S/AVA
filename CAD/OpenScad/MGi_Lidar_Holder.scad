drilling_d = 3;

linear_extrude(2){
	difference(){
		translate([-5,-5,0]){
			minkowski(){
				square([80,40]);
				circle(d=5, $fn=50);
			}
		}
		
		// D1
		translate([0,0,0]){
			circle(d=drilling_d, $fn=50);
		}
		
		// D2
		translate([71,0,0]){
			circle(d=drilling_d, $fn=50);
		}
		
		// D3
		translate([64,26,0]){
			circle(d=drilling_d, $fn=50);
		}
		
		// D4
		translate([7,26,0]){
			circle(d=drilling_d, $fn=50);
		}
	}
}