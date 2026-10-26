set terminal png
set output 'plot.png'

set xlabel "Time *500  logscale (SU)"
set ylabel "Energy (SU)"
set logscale x

set yrange[:-42.6]


set title "PHB Simulation high strength"

plot "./output/0.01/energy.ign" u ($0):4 w l title "T=0.01"
replot "./output/0.08/energy.ign" u ($0):4 w l title "T=0.08"
replot "./output/0.15/energy.ign" u ($0):4 w l title "T=0.15"
replot "./output/0.22/energy.ign" u ($0):4 w l title "T=0.22"
replot "./output/0.29/energy.ign" u ($0):4 w l title "T=0.29"

set output 'plot.png'
replot