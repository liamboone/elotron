


    //*******************************************************************
    //  DRAW THE CHORD DIAGRAM
    //*******************************************************************
    function drawChords (matrix, mmap) {
        var w = 980, h = 800, r1 = h / 2, r0 = r1 - 110;

        var fill = d3.scale.category20c();

        var chord = d3.layout.chord()
            .padding(.02)
            .sortSubgroups(d3.descending)
            .sortChords(d3.descending);

        var arc = d3.svg.arc()
            .innerRadius(r0)
            .outerRadius(r0 + 20);

        var svg = d3.select("#chart-chord").append("svg:svg")
            .attr("width", w)
            .attr("height", h)
            .append("svg:g")
            .attr("id", "circle")
            .attr("transform", "translate(" + w / 2 + "," + h / 2 + ")");

        svg.append("circle")
            .attr("r", r0 + 20);

        var rdr = chordRdr(matrix, mmap);
        chord.matrix(matrix);

        var g = svg.selectAll("g.group")
            .data(chord.groups())
            .enter().append("svg:g")
            .attr("class", "group")
            .on("mouseover", mouseover)
            .on("mouseout", mouseout);

        g.append("svg:path")
            .style("stroke", "black")
            .style("fill", function(d) { return fill(rdr(d).gname); })
            .attr("d", arc);

        g.append("svg:text")
            .each(function(d) { d.angle = (d.startAngle + d.endAngle) / 2; })
            .attr("dy", ".35em")
            .style("font-family", "helvetica, arial, sans-serif")
            .style("font-size", "9px")
            .attr("text-anchor", function(d) { return d.angle > Math.PI ? "end" : null; })
            .attr("transform", function(d) {
                    return "rotate(" + (d.angle * 180 / Math.PI - 90) + ")"
                    + "translate(" + (r0 + 26) + ")"
                    + (d.angle > Math.PI ? "rotate(180)" : "");
                    })
        .text(function(d) { return rdr(d).gname; });

        var chordPaths = svg.selectAll("path.chord")
            .data(chord.chords())
            .enter().append("svg:path")
            .attr("class", "chord")
            .style("stroke", function(d) { return d3.rgb(fill(rdr(d).sname)).darker(); })
            .style("fill", function(d) { return fill(rdr(d).sname); })
            .attr("d", d3.svg.chord().radius(r0))
            .on("mouseover", function (d, i) {
                    d3.select("#tooltip")
                    .style("visibility", "visible")
                    .html(chordTip(rdr(d)))
                    //.style("top", function () { return (d3.event.pageY - 10)+"px"})
                    //.style("left", function () { return (d3.event.pageX - 10)+"px";})
                 chordPaths.classed("fade", function(p) {
                        return p.source.index != d.source.index && p.target.index != d.source.index;
                        });
		})
        .on("mouseout", function (d) { d3.select("#tooltip").style("visibility", "hidden") });

        function chordTip (d) {
            var p = d3.format(".1%"), q = d3.format(",.2f")
                return "Chord Info:<br/>"
                +  d.sname + " average game score against " + d.tname
                + ": " + q(d.svalue) + " pts<br/>"
                + "<br/>"
                + d.tname + " average game score against " + d.sname
                + ": " + q(d.tvalue) + " pts<br/>";
        }

        function groupTip (d) {
            var p = d3.format(".1%"), q = d3.format(",.2f")
                return "" + d.gname + " average overall score per game: (coming soon) pts<br/>"
                + "(coming soon)% of average average score in Elotron ((coming soon) pts)"
        }

        function mouseover(d, i) {
            d3.select("#tooltip")
                .style("visibility", "visible")
                .html(groupTip(rdr(d)))
                //.style("top", function () { return (d3.event.pageY - 10)+"px"})
                //.style("left", function () { return (d3.event.pageX - 10)+"px";})

                chordPaths.classed("fade", function(p) {
                        return p.source.index != i
                        && p.target.index != i;
                        });
        }
	function mouseout(d) {
		chordPaths.classed("fade", function(p) {return false; });
		d3.select("#tooltip").style("visibility", "hidden");	
	}
    }
