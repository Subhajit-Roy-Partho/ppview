set terminal png
set output "MixedPerformance.png"
set xlabel "Time(SU)"
set ylabel "Energy(SU)"
set title "Mixed Point Performance"
plot "5.ign" u 1:4 w l title "1e-5"
replot "6.ign" u 1:4 w l title "1e-6"
replot "7.ign" u 1:4 w l title "1e-7"
replot "8.ign" u 1:4 w l title "1e-8"
replot "9.ign" u 1:4 w l title "1e-9"

set output "MixedPerformance.png"
replot