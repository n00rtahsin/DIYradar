// Ultrasonic Radar Visualizer (Processing)
// Works with serial input formatted as: angle,distance.
// Each reading must end with a '.' (e.g., "37,18.")

import processing.serial.*;

Serial myPort;

// ---- Config ----
final String PORT_NAME = "COM7";   // ← change to your Arduino port if needed (e.g., "COM7")
final int    BAUD      = 9600;
final int    MAX_CM    = 40;       // sensor visualization max range (cm)

// ---- State ----
String angle   = "";
String distance= "";
int    iAngle  = 0;
int    iDistance = 0;
String noObject = "";

float pixsDistance = 0;

void setup() {
  size(1366, 768);
  smooth();
  surface.setTitle("Ultrasonic Radar");

  // Show available ports in the console to help pick the right one
  println("Serial ports:", Serial.list());

  // Open the configured port
  myPort = new Serial(this, PORT_NAME, BAUD);
  // Read until '.' (delimiter). The returned string includes the delimiter.
  myPort.bufferUntil('.');
}

void draw() {
  // Motion blur / fade
  noStroke();
  fill(0, 4);
  rect(0, 0, width, height - height * 0.065);

  // Radar drawing color
  fill(98, 245, 31);

  drawRadar();
  drawSweepLine();
  drawDetectedObject();
  drawHudText();
}

void serialEvent(Serial p) {
  // Read up to and including '.'
  String data = p.readStringUntil('.');
  if (data == null) return;

  data = trim(data);
  if (data.length() == 0) return;

  // Remove the trailing '.' safely (if present)
  if (data.charAt(data.length()-1) == '.') {
    data = data.substring(0, data.length()-1);
  }

  // Expect "angle,distance"
  String[] parts = splitTokens(data, ",");
  if (parts == null || parts.length < 2) return;

  // Parse angle and distance with guards
  try {
    iAngle = constrain(parseInt(trim(parts[0])), 0, 180);
  } catch (Exception e) {
    // keep previous angle on parse failure
  }
  try {
    iDistance = max(0, parseInt(trim(parts[1])));
  } catch (Exception e) {
    // keep previous distance on parse failure
  }
}

void drawRadar() {
  pushMatrix();
  translate(width/2, height - height*0.074); // Radar origin at bottom center
  noFill();
  strokeWeight(2);
  stroke(98, 245, 31);

  // Concentric arcs (range rings)
  arc(0, 0, (width - width*0.0625), (width - width*0.0625), PI, TWO_PI);
  arc(0, 0, (width - width*0.27),   (width - width*0.27),   PI, TWO_PI);
  arc(0, 0, (width - width*0.479),  (width - width*0.479),  PI, TWO_PI);
  arc(0, 0, (width - width*0.687),  (width - width*0.687),  PI, TWO_PI);

  // Angle spokes
  line(-width/2, 0, width/2, 0); // 0°
  line(0, 0, (-width/2)*cos(radians(30)),  (-width/2)*sin(radians(30)));
  line(0, 0, (-width/2)*cos(radians(60)),  (-width/2)*sin(radians(60)));
  line(0, 0, (-width/2)*cos(radians(90)),  (-width/2)*sin(radians(90)));
  line(0, 0, (-width/2)*cos(radians(120)), (-width/2)*sin(radians(120)));
  line(0, 0, (-width/2)*cos(radians(150)), (-width/2)*sin(radians(150)));
  line((-width/2)*cos(radians(30)), 0, width/2, 0);

  popMatrix();
}

void drawDetectedObject() {
  pushMatrix();
  translate(width/2, height - height*0.074);
  strokeWeight(9);
  stroke(255, 10, 10);

  // Map distance (cm) to pixels along the sweep line
  float maxRadius = (width - width*0.505);
  float d = constrain(iDistance, 0, MAX_CM);
  pixsDistance = map(d, 0, MAX_CM, 0, maxRadius);

  if (iDistance <= MAX_CM) {
    float ax = pixsDistance * cos(radians(iAngle));
    float ay = -pixsDistance * sin(radians(iAngle));
    float lx = maxRadius * cos(radians(iAngle));
    float ly = -maxRadius  * sin(radians(iAngle));
    line(ax, ay, lx, ly);
  }

  popMatrix();
}

void drawSweepLine() {
  pushMatrix();
  strokeWeight(9);
  stroke(30, 250, 60);
  translate(width/2, height - height*0.074);

  float r = (height - height*0.12);
  line(0, 0, r * cos(radians(iAngle)), -r * sin(radians(iAngle)));

  popMatrix();
}

void drawHudText() {
  pushMatrix();

  noObject = (iDistance > MAX_CM) ? "Out of Range" : "In Range";

  // Bottom HUD bar
  fill(0, 0, 0);
  noStroke();
  rect(0, height - height*0.0648, width, height);

  fill(98, 245, 31);
  textSize(25);
  text("10cm", width - width*0.3854, height - height*0.0833);
  text("20cm", width - width*0.2810, height - height*0.0833);
  text("30cm", width - width*0.1770, height - height*0.0833);
  text("40cm", width - width*0.0729, height - height*0.0833);

  textSize(40);
  text("Ultrasonic Radar", width - width*0.875, height - height*0.0277);
  text("Angle: " + iAngle + " °",      width - width*0.48,  height - height*0.0277);
  text("Distance: ",                    width - width*0.26,  height - height*0.0277);
  if (iDistance <= MAX_CM) {
    text(iDistance + " cm",            width - width*0.18,  height - height*0.0277);
  } else {
    text(noObject,                     width - width*0.18,  height - height*0.0277);
  }

  // Angle labels on the arc
  textSize(25);
  fill(98, 245, 60);

  pushMatrix();
  translate((width - width*0.4994) + width/2*cos(radians(30)),  (height - height*0.0907) - width/2*sin(radians(30)));
  rotate(radians(60));
  text("30°", 0, 0);
  popMatrix();

  pushMatrix();
  translate((width - width*0.5030) + width/2*cos(radians(60)),  (height - height*0.0888) - width/2*sin(radians(60)));
  rotate(radians(30));
  text("60°", 0, 0);
  popMatrix();

  pushMatrix();
  translate((width - width*0.5070) + width/2*cos(radians(90)),  (height - height*0.0833) - width/2*sin(radians(90)));
  rotate(0);
  text("90°", 0, 0);
  popMatrix();

  pushMatrix();
  translate((width - width*0.5130) + width/2*cos(radians(120)), (height - height*0.07129) - width/2*sin(radians(120)));
  rotate(radians(-30));
  text("120°", 0, 0);
  popMatrix();

  pushMatrix();
  translate((width - width*0.5104) + width/2*cos(radians(150)), (height - height*0.0574) - width/2*sin(radians(150)));
  rotate(radians(-60));
  text("150°", 0, 0);
  popMatrix();

  popMatrix();
}
