const int zpin = A1;

const int Z_THRESHOLD = 335;

void setup()
{
  Serial.begin(9600);

  pinMode(LED_BUILTIN, OUTPUT);
}
void loop()
{
  int z = analogRead(zpin);
  delay(10);
  
  Serial.print(z < Z_THRESHOLD ? "Upsidedown" : "Rightside up");
  digitalWrite(LED_BUILTIN, z < Z_THRESHOLD ? HIGH : LOW);
  
  Serial.print("\n");
}
