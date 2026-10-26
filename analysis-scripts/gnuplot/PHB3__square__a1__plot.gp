set terminal png
    set output "plot.png"
    set xlabel "Time (SU)"
    set ylabel "Energy (SU)"
    set logscale x
    
plot "output/0.02/energy.ign" u 1:4 w l t "T=0.02"
replot "output/0.04/energy.ign" u 1:4 w l t "T=0.04"
replot "output/0.06/energy.ign" u 1:4 w l t "T=0.06"
replot "output/0.08/energy.ign" u 1:4 w l t "T=0.08"
replot "output/0.10/energy.ign" u 1:4 w l t "T=0.10"
replot "output/0.12/energy.ign" u 1:4 w l t "T=0.12"
replot "output/0.14/energy.ign" u 1:4 w l t "T=0.14"
replot "output/0.16/energy.ign" u 1:4 w l t "T=0.16"
replot "output/0.18/energy.ign" u 1:4 w l t "T=0.18"
replot "output/0.20/energy.ign" u 1:4 w l t "T=0.20"
set output 'plot.png'
    replot
