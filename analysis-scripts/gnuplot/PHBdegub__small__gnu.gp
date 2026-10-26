set terminal png
set output 'histogram.png'

set xlabel "Time *500 (SU)"
set ylabel "Energy (SU)"

set title "PHB Simulation high strength"

plot "./output/0.01/energy.ign" u ($0):4 w l title "T=0.01"
replot "./output/0.05/energy.ign" u ($0):4 w l title "T=0.05"
replot "./output/0.09/energy.ign" u ($0):4 w l title "T=0.09"
replot "./output/0.13/energy.ign" u ($0):4 w l title "T=0.13"
replot "./output/0.17/energy.ign" u ($0):4 w l title "T=0.17"
replot "./output/0.21/energy.ign" u ($0):4 w l title "T=0.21"
replot "./output/0.25/energy.ign" u ($0):4 w l title "T=0.25"
replot "./output/0.29/energy.ign" u ($0):4 w l title "T=0.29"
replot "./output/0.33/energy.ign" u ($0):4 w l title "T=0.33"
replot "./output/0.37/energy.ign" u ($0):4 w l title "T=0.37"

set output 'histogram.png'
replot