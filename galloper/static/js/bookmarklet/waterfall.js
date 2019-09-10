/*
Helper to create waterfall timelines
*/
import { newEl, getNodeTextWidth, newTextEl } from "./svg.js";
import { addClass, removeClass, newTag } from "./dom.js";

const waterfall = {};


//model for block and segment
export function timeBlock(name, start, end, cssClass, segments, rawResource){
	return {
		name : name,
		start : start,
		end : end,
		total : ((typeof start !== "number" || typeof end !== "number") ? undefined : (end - start)),
		cssClass : cssClass,
		segments : segments,
		rawResource : rawResource
	}
};

export function setupTimeLine (parent_element, durationMs, blocks, marks, lines, title) {
	const unit = durationMs / 100,
		barsToShow = blocks
			.filter((block) => (typeof block.start == "number" && typeof block.total == "number"))
			.sort((a, b) => (a.start||0) - (b.start||0)),
		maxMarkTextLength = marks.length > 0 ? marks.reduce((currMax, currValue) => {
			return Math.max((typeof currMax == "number" ? currMax : 0), getNodeTextWidth(parent_element, newTextEl(currValue.name, "0")));
		}) : 0,
		diagramHeight = (barsToShow.length + 1) * 25,
		chartHolderHeight = diagramHeight + maxMarkTextLength + 35;

	const chartHolder = newTag("section", {
		class : "resource-timing water-fall-holder chart-holder"
	});
	const timeLineHolder = newEl("svg:svg", {
		height : Math.floor(chartHolderHeight),
		class : "water-fall-chart"
	});
	const timeLineLabelHolder = newEl("g", {class : "labels"});

	const endLine = newEl("line", {
		x1 : "0",
		y1 : "0",
		x2 : "0",
		y2 : diagramHeight,
		class : "line-end"
	});

	const startLine = newEl("line", {
		x1 : "0",
		y1 : "0",
		x2 : "0",
		y2 : diagramHeight,
		class : "line-start"
	});

	const onRectMouseEnter = (evt) => {
		const targetRect = evt.target;
		addClass(targetRect, "active");

		const xPosEnd = targetRect.x.baseVal.valueInSpecifiedUnits + targetRect.width.baseVal.valueInSpecifiedUnits + "%";
		const xPosStart = targetRect.x.baseVal.valueInSpecifiedUnits + "%";

		endLine.x1.baseVal.valueAsString = xPosEnd;
		endLine.x2.baseVal.valueAsString = xPosEnd;
		startLine.x1.baseVal.valueAsString = xPosStart;
		startLine.x2.baseVal.valueAsString = xPosStart;
		addClass(endLine, "active");
		addClass(startLine, "active");

		targetRect.parentNode.appendChild(endLine);
		targetRect.parentNode.appendChild(startLine);
	};

	const onRectMouseLeave = (evt) => {
		removeClass(evt.target, "active");
		removeClass(endLine, "active");
		removeClass(startLine, "active");
	};

	const createRect = (width, height, x, y, cssClass, label, segments) => {
		let rectHolder;
		const rect = newEl("rect", {
			width : (width / unit) + "%",
			height : height-1,
			x :  Math.round((x / unit)*100)/100 + "%",
			y : y,
			class : ((segments && segments.length > 0 ? "time-block" : "segment")) + " " +  (cssClass || "block-undefined")
		});
		if(label){
			rect.appendChild(newEl("title", {
				text : label
			})); // Add tile to wedge path
		}

		rect.addEventListener("mouseenter", onRectMouseEnter);
		rect.addEventListener("mouseleave", onRectMouseLeave);

		if(segments && segments.length > 0){
			rectHolder = newEl("g");
			rectHolder.appendChild(rect);
			segments.forEach((segment) => {
				if(segment.total > 0 && typeof segment.start === "number"){
					rectHolder.appendChild(createRect(segment.total, 8, segment.start||0.001, y, segment.cssClass, segment.name + " (" + Math.round(segment.start) + "ms - " +  Math.round(segment.end) + "ms | total: " + Math.round(segment.total) + "ms)"));
				}
			});
			return rectHolder;
		}else{
			return rect;
		}
	};

	const createBgRect = (block) => {
	    console.log(JSON.stringify(block));
	    console.log(unit);
		const rect = newEl("rect", {
			width : ((block.total || 1) / unit) + "%",
			height : diagramHeight,
			x :  ((block.start||0.001) / unit) + "%",
			y : 0,
			class : block.cssClass || "block-undefined"
		});

		rect.appendChild(newEl("title", {
			text : block.name
		})); // Add tile to wedge path
		return rect;
	};

	const createTimeWrapper = () => {
		const timeHolder = newEl("g", { class : "time-scale full-width" });
		for(let i = 0, secs = durationMs / 1000, secPerc = 100 / secs; i <= secs; i++){
			const lineLabel = newTextEl(i + "sec",  diagramHeight);
			if(i > secs - 0.2){
				lineLabel.setAttribute("x", secPerc * i - 0.5 + "%");
				lineLabel.setAttribute("text-anchor", "end");
			}else{
				lineLabel.setAttribute("x", secPerc * i + 0.5 + "%");
			}

			const lineEl = newEl("line", {
				x1 : secPerc * i + "%",
				y1 : "0",
				x2 : secPerc * i + "%",
				y2 : diagramHeight
			});
			timeHolder.appendChild(lineEl);
			timeHolder.appendChild(lineLabel);
		}
		return timeHolder;
	};


	const renderMarks = () => {
		const marksHolder = newEl("g", {
			transform : "scale(1, 1)",
			class : "marker-holder"
		});

		marks.forEach((mark, i) => {
			const x = mark.startTime / unit;
			const markHolder = newEl("g", {
				class : "mark-holder"
			});
			const lineHolder = newEl("g", {
				class : "line-holder"
			});
			const lineLabelHolder = newEl("g", {
				class : "line-label-holder",
				x : x + "%"
			});
			mark.x = x;
			const lineLabel = newTextEl(mark.name,  diagramHeight + 25 );
			//lineLabel.setAttribute("writing-mode", "tb");
			lineLabel.setAttribute("x", x + "%");
			lineLabel.setAttribute("stroke", "");


			lineHolder.appendChild(newEl("line", {
				x1 : x + "%",
				y1 : 0,
				x2 : x + "%",
				y2 : diagramHeight
			}));

			if(marks[i-1] && mark.x - marks[i-1].x < 1){
				lineLabel.setAttribute("x", marks[i-1].x+1 + "%");
				mark.x = marks[i-1].x+1;
			}

			//would use polyline but can't use percentage for points
			lineHolder.appendChild(newEl("line", {
				x1 : x + "%",
				y1 : diagramHeight,
				x2 : mark.x + "%",
				y2 : diagramHeight + 23
			}));

			let isActive = false;
			const onLabelMouseEnter = (evt) => {
				if(!isActive){
					isActive = true;
					addClass(lineHolder, "active");
					//firefox has issues with this
					markHolder.parentNode.appendChild(markHolder);
				}
			};

			const onLabelMouseLeave = (evt) => {
				isActive = false;
				removeClass(lineHolder, "active");
			};

			lineLabel.addEventListener("mouseenter", onLabelMouseEnter);
			lineLabel.addEventListener("mouseleave", onLabelMouseLeave);
			lineLabelHolder.appendChild(lineLabel);

			markHolder.appendChild(newEl("title", {
				text : mark.name + " (" + Math.round(mark.startTime) + "ms)",
			}));
			markHolder.appendChild(lineHolder);
			marksHolder.appendChild(markHolder);
			markHolder.appendChild(lineLabelHolder);
		});

		return marksHolder;
	};

	timeLineHolder.appendChild(createTimeWrapper());
	timeLineHolder.appendChild(renderMarks());

	lines.forEach((block, i) => {
		timeLineHolder.appendChild(createBgRect(block));
	});

	barsToShow.forEach((block, i) => {
		const blockWidth = block.total||1;

		const y = 25 * i;
		timeLineHolder.appendChild(createRect(blockWidth, 25, block.start||0.001, y, block.cssClass, block.name + " (" + block.start + "ms - " + block.end + "ms | total: " + block.total + "ms)", block.segments));

		const blockLabel = newTextEl(block.name + " (" + Math.round(block.total) + "ms)", (y + (block.segments? 20 : 17)));

		if(((block.total||1) / unit) > 10 && getNodeTextWidth(parent_element, blockLabel) < 200){
			blockLabel.setAttribute("class", "inner-label");
			blockLabel.setAttribute("x", ((block.start||0.001) / unit) + 0.5 + "%");
			blockLabel.setAttribute("width", (blockWidth / unit) + "%");
		}else if(((block.start||0.001) / unit) + (blockWidth / unit) < 80){
			blockLabel.setAttribute("x", ((block.start||0.001) / unit) + (blockWidth / unit) + 0.5 + "%");
		}else {
			blockLabel.setAttribute("x", (block.start||0.001) / unit - 0.5 + "%");
			blockLabel.setAttribute("text-anchor", "end");
		}
		blockLabel.style.opacity = block.name.match(/js.map$/) ? "0.5" : "1";
		timeLineLabelHolder.appendChild(blockLabel);
	});

	timeLineHolder.appendChild(timeLineLabelHolder);

	if(title){
		chartHolder.appendChild(newTag("h3", {
			text : title
		}));
	}
	chartHolder.appendChild(timeLineHolder);
	return chartHolder;
};
