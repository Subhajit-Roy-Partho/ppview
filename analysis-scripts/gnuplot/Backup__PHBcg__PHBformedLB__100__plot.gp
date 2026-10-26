set terminal png
set output 'plot.png'
set title "PHB box 500"
set xlabel "Time 5e2 SU"
set ylabel "Energy SU"

plot "<(sed -n '10,$p' output/0.06/out2.txt)" u ($0-1):5 title "T=0.06"
replot "<(sed -n '10,$p' output/0.11/out2.txt)" u ($0-1):5 title "T=0.11"
replot "<(sed -n '10,$p' output/0.16/out2.txt)" u ($0-1):5 title "T=0.16"
replot "<(sed -n '10,$p' output/0.21/out2.txt)" u ($0-1):5 title "T=0.21"
replot "<(sed -n '10,$p' output/0.26/out2.txt)" u ($0-1):5 title "T=0.26"
replot "<(sed -n '10,$p' output/0.31/out2.txt)" u ($0-1):5 title "T=0.31"
replot "<(sed -n '10,$p' output/0.36/out2.txt)" u ($0-1):5 title "T=0.36"

set output 'plot.png'
replot