set terminal png
set output 'plot.png'

set xlabel "Time (SU)"
set ylabel "Energy (SU)"

set title "PHB Simulation strength =1"
set yrange[:-38]

plot "output/0.01/energy.ign" u 1:4 w l title "T=0.01", \
     "output/0.08/energy.ign" u 1:4 w l title "T=0.08", \
     "output/0.15/energy.ign" u 1:4 w l title "T=0.15", \
     "output/0.22/energy.ign" u 1:4 w l title "T=0.22", \
     "output/0.29/energy.ign" u 1:4 w l title "T=0.29", \
     "output/0.36/energy.ign" u 1:4 w l title "T=0.36", \
     "output/0.43/energy.ign" u 1:4 w l title "T=0.43", \
     "output/0.50/energy.ign" u 1:4 w l title "T=0.50", \
     "output/0.57/energy.ign" u 1:4 w l title "T=0.57", \
     "output/0.64/energy.ign" u 1:4 w l title "T=0.64", \
     "output/0.71/energy.ign" u 1:4 w l title "T=0.71", \
     "output/0.78/energy.ign" u 1:4 w l title "T=0.78"
