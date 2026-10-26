set terminal png
    set output "plot.png"
    set xlabel "Time (SU)"
    set ylabel "Energy (SU)"
    set logscale x
    
replot "output/0.010/energy.ign" u 1:4 w l t "T=0.010"
replot "output/0.015/energy.ign" u 1:4 w l t "T=0.015"
replot "output/0.020/energy.ign" u 1:4 w l t "T=0.020"
replot "output/0.025/energy.ign" u 1:4 w l t "T=0.025"
replot "output/0.030/energy.ign" u 1:4 w l t "T=0.030"
replot "output/0.035/energy.ign" u 1:4 w l t "T=0.035"
replot "output/0.040/energy.ign" u 1:4 w l t "T=0.040"
replot "output/0.045/energy.ign" u 1:4 w l t "T=0.045"
replot "output/0.050/energy.ign" u 1:4 w l t "T=0.050"
replot "output/0.055/energy.ign" u 1:4 w l t "T=0.055"
set output 'plot.png'
    replot
