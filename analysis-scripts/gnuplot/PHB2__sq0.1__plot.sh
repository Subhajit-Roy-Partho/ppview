start=0.02
stop=0.2
step=0.02

echo 'set terminal png
set output "plot.png"
set xlabel "Time *500 (SU)"
set ylabel "Energy (SU)"
set logscale x
set yrange[:-43]
'>plot.gp


for i in $(seq $start $step $stop); do
    if [ "$i" = "$start" ]; then
        echo 'plot "output/'$i'/energy.ign" u 1:4 w l t "T='$i'"'>>plot.gp
    else
        echo 'replot "output/'$i'/energy.ign" u 1:4 w l t "T='$i'"'>>plot.gp
    fi
    cd "output/$i"
    rm -rf last.mgl
    terminal autoconvert -i "square.phb" -d "last_conf.dat" -o "last.mgl" &
    cd ../..
done

echo "set output 'plot.png'
replot">>plot.gp
gnuplot plot.gp