set terminal png
set output "FloatPerformance.png"
set xlabel "Time(SU)"
set ylabel "Energy(SU)"
set xrange [0:10]
set title "Floating Point Performance"
plot "5f.ign" u 1:4 w l title "1e-5"
replot "6f.ign" u 1:4 w l title "1e-6"
replot "7f.ign" u 1:4 w l title "1e-7"
replot "8f.ign" u 1:4 w l title "1e-8"

set output "FloatPerformance.png"
replot