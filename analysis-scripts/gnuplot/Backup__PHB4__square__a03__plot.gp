set terminal png
    set output "plot.png"
    set xlabel "Time (SU)"
    set ylabel "Energy (SU)"
    set logscale x
    
plot "output/0.066/energy.ign" u 1:4 w l t "T=0.066"
replot "output/0.072/energy.ign" u 1:4 w l t "T=0.072"
replot "output/0.078/energy.ign" u 1:4 w l t "T=0.078"
replot "output/0.084/energy.ign" u 1:4 w l t "T=0.084"
replot "output/0.090/energy.ign" u 1:4 w l t "T=0.090"
replot "output/0.096/energy.ign" u 1:4 w l t "T=0.096"
replot "output/0.102/energy.ign" u 1:4 w l t "T=0.102"
replot "output/0.108/energy.ign" u 1:4 w l t "T=0.108"
replot "output/0.114/energy.ign" u 1:4 w l t "T=0.114"
replot "output/0.120/energy.ign" u 1:4 w l t "T=0.120"
set output 'plot.png'
    replot
