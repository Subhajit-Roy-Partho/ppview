set terminal png
set output 'plot.png'

set xlabel "Time *500 (SU)"
set ylabel "Energy (SU)"
set logscale x

# set yrange[:-40]


set title "PHB Simulation high strength"

plot "./output/0.08/energy.ign" u ($0):4 w l title "T=0.08"
replot "./output/0.10/energy.ign" u ($0):4 w l title "T=0.10"
replot "./output/0.12/energy.ign" u ($0):4 w l title "T=0.12"
replot "./output/0.14/energy.ign" u ($0):4 w l title "T=0.14"
replot "./output/0.16/energy.ign" u ($0):4 w l title "T=0.16"
replot "./output/0.18/energy.ign" u ($0):4 w l title "T=0.18"
replot "./output/0.20/energy.ign" u ($0):4 w l title "T=0.20"
replot "./output/0.22/energy.ign" u ($0):4 w l title "T=0.22"
replot "./output/0.24/energy.ign" u ($0):4 w l title "T=0.24"
replot "./output/0.26/energy.ign" u ($0):4 w l title "T=0.26"
replot "./output/0.28/energy.ign" u ($0):4 w l title "T=0.28"
replot "./output/0.30/energy.ign" u ($0):4 w l title "T=0.30"

set output 'plot.png'
replot