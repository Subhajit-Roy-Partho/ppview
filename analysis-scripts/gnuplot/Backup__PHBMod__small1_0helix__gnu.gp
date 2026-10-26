set terminal png
set output 'plot.png'

set xlabel "Time *500 (SU)"
set ylabel "Energy (SU)"
set logscale x

set yrange[:-40]


set title "PHB Simulation high strength"

plot "./output/0.01/energy.ign" u ($0):4 w l title "T=0.01"
replot "./output/0.08/energy.ign" u ($0):4 w l title "T=0.08"
replot "./output/0.15/energy.ign" u ($0):4 w l title "T=0.15"
replot "./output/0.22/energy.ign" u ($0):4 w l title "T=0.22"
replot "./output/0.29/energy.ign" u ($0):4 w l title "T=0.29"
replot "./output/0.36/energy.ign" u ($0):4 w l title "T=0.36"
replot "./output/0.43/energy.ign" u ($0):4 w l title "T=0.43"
replot "./output/0.50/energy.ign" u ($0):4 w l title "T=0.50"
replot "./output/0.57/energy.ign" u ($0):4 w l title "T=0.57"
replot "./output/0.64/energy.ign" u ($0):4 w l title "T=0.64"
replot "./output/0.71/energy.ign" u ($0):4 w l title "T=0.71"
replot "./output/0.78/energy.ign" u ($0):4 w l title "T=0.78"

set output 'plot.png'
replot