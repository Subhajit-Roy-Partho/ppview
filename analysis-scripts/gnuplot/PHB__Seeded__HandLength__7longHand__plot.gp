set terminal png
    set output "plot.png"
    set xlabel "Time (SU)"
    set ylabel "Energy (SU)"
    set logscale x
    
plot "output/0.070/energy.ign" u 1:4 w l t "T=0.070"
replot "output/0.074/energy.ign" u 1:4 w l t "T=0.074"
replot "output/0.078/energy.ign" u 1:4 w l t "T=0.078"
replot "output/0.082/energy.ign" u 1:4 w l t "T=0.082"
replot "output/0.086/energy.ign" u 1:4 w l t "T=0.086"
set output 'plot.png'
    replot
