start=0.01
stop=0.8
step=0.07

set terminal png
set output 'plot.png'

set xlabel "Time *500 (SU)"
set ylabel "Energy (SU)"

set title "PHB Simulation high strength"

do for [i=0:11] {
    id=0.01 + i * 0.07
    file = gprintf("output/%.2f/energy.ign",id)
    temp = gprintf("T=%.2f",id)
    # file="output/".id."/energy.ign"
    if(i==0){
        plot file u 1:4 w l title temp
    }else{
        replot file u 1:4 w l title temp
    }
}

set output 'plot.png'
replot