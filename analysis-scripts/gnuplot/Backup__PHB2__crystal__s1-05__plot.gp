set terminal png
set output "plot.png"
set xlabel "Time *500 (SU)"
set ylabel "Energy (SU)"
set logscale x
set yrange[:-43]

plot "output/0.02/energ.ign" u 1:4 w l t "T=0.02"
replot "output/0.04/energ.ign" u 1:4 w l t "T=0.04"
replot "output/0.06/energ.ign" u 1:4 w l t "T=0.06"
replot "output/0.08/energ.ign" u 1:4 w l t "T=0.08"
replot "output/0.10/energ.ign" u 1:4 w l t "T=0.10"
replot "output/0.12/energ.ign" u 1:4 w l t "T=0.12"
replot "output/0.14/energ.ign" u 1:4 w l t "T=0.14"
replot "output/0.16/energ.ign" u 1:4 w l t "T=0.16"
replot "output/0.18/energ.ign" u 1:4 w l t "T=0.18"
replot "output/0.20/energ.ign" u 1:4 w l t "T=0.20"
set output 'plot.png'
replot
