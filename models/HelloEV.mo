// HelloEV: a minimal 1-D vehicle used to prove the toolchain works.
// A constant drive force accelerates the car against rolling resistance
// and aerodynamic drag. Speed settles at the value where the forces balance:
//   v_top = sqrt((F_drive - Crr*m*g) / (0.5*rho*CdA))  ≈ 33.7 m/s (≈ 121 km/h)
// Generic, publicly typical parameters only.
model HelloEV
  parameter Real m = 1600 "Vehicle mass [kg]";
  parameter Real F_drive = 600 "Constant drive force at the wheels [N]";
  parameter Real Crr = 0.01 "Rolling resistance coefficient [-]";
  parameter Real CdA = 0.65 "Drag coefficient x frontal area [m2]";
  parameter Real rho = 1.2 "Air density [kg/m3]";
  parameter Real g = 9.81 "Gravity [m/s2]";

  Real v(start = 0, fixed = true) "Vehicle speed [m/s]";
  Real x(start = 0, fixed = true) "Distance travelled [m]";
  Real v_kph "Vehicle speed [km/h]";
  Real F_roll "Rolling resistance force [N]";
  Real F_aero "Aerodynamic drag force [N]";
equation
  F_roll = Crr * m * g;
  F_aero = 0.5 * rho * CdA * v^2;
  m * der(v) = F_drive - F_roll - F_aero;
  der(x) = v;
  v_kph = 3.6 * v;
end HelloEV;
