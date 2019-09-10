function addClass (el, className) {
	if(el.classList){
		el.classList.add(className);
	}else{
		// IE doesn't support classList in SVG - also no need for dublication check i.t.m.
		el.setAttribute("class", el.getAttribute("class") + " " + className);
	}
	return el;
};


function removeClass (el, className) {
	if(el.classList){
		el.classList.remove(className);
	}else{
		//IE doesn't support classList in SVG - also no need for dublication check i.t.m.
        el.setAttribute("class", el.getAttribute("class").replace(new RegExp("(\\s|^)" + className + "(\\s|$)", "g"), "$2"));
	}
	return el;
};

function newEl (tagName, settings, css){
	const el = document.createElementNS("http://www.w3.org/2000/svg", tagName);
	settings = settings || {};
	for(let attr in settings){
		if(attr != "text"){
			el.setAttributeNS(null, attr, settings[attr]);
		}
	}
	el.textContent = settings.text||"";
	el.style.cssText = css||"";
	return el;
};

function newTextEl (text, y, css) {
	return newEl("text", {
			fill : "#111",
			y : y,
			text : text
		}, (css||"") + " text-shadow:0 0 4px #fff;");
};

function getNodeTextWidth (parent_element, textNode) {
	const tmp = newEl("svg:svg", {}, "visibility:hidden;");
	tmp.appendChild(textNode);
	document.getElementById(parent_element).appendChild(tmp);

	const nodeWidth = textNode.getBBox().width;
	tmp.parentNode.removeChild(tmp);
	return nodeWidth;
};

function endsWith(str, suffix) {
	return str.indexOf(suffix, str.length - suffix.length) !== -1;
};

function getFileType(fileExtension, initiatorType) {
	if(fileExtension){
		switch(fileExtension){
			case "jpg" :
			case "jpeg" :
			case "png" :
			case "gif" :
			case "webp" :
			case "svg" :
			case "ico" :
				return "image";
			case "js" :
				return "js"
			case "css":
				return "css"
			case "html":
				return "html"
			case "woff":
			case "woff2":
			case "ttf":
			case "eot":
			case "otf":
				return "font"
			case "swf":
				return "flash"
			case "map":
				return "source-map"
		}
	}
	if(initiatorType){
		switch(initiatorType){
			case "xmlhttprequest" :
				return "ajax"
			case "img" :
				return "image"
			case "script" :
				return "js"
			case "internal" :
			case "iframe" :
				return "html" //actual page
			default :
				return "other"
		}
	}
	return initiatorType;
};

function getItemCount(arr, keyName) {
	let counts = {},
		resultArr = [],
		obj;

	arr.forEach((key) => {
		counts[key] = counts[key] ? counts[key]+1 : 1;
	});

	//pivot data
	for(let fe in counts){
		obj = {};
		obj[keyName||"key"] = fe;
		obj.count = counts[fe];

		resultArr.push(obj);
	}
	return resultArr.sort((a, b) => {
		return a.count < b.count ? 1 : -1;
	});
};

function getData(resources, marks, measures, timing) {
    const data = {
	    resources: resources,
	    marks: marks,
	    measures: measures,
	    perfTiming: timing,
	    allResourcesCalc: [],
	    isValid : () => isValid
    };

    data.allResourcesCalc = data.resources
		//remove this bookmarklet from the result
		.filter((currR) => !currR.name.match(/http[s]?\:\/\/(micmro|nurun).github.io\/performance-bookmarklet\/.*/))
		.map((currR, i, arr) => {
			//crunch the resources data into something easier to work with
			const isRequest = currR.name.indexOf("http") === 0;
			let  urlFragments, maybeFileName, fileExtension;

			if(isRequest){
				urlFragments = currR.name.match(/:\/\/(.[^/]+)([^?]*)\??(.*)/);
				maybeFileName = urlFragments[2].split("/").pop();
				fileExtension = maybeFileName.substr((Math.max(0, maybeFileName.lastIndexOf(".")) || Infinity) + 1);
			}else{
				urlFragments = ["", location.host];
				fileExtension = currR.name.split(":")[0];
			}

			const currRes = {
				name : currR.name,
				domain : urlFragments[1],
				initiatorType : currR.initiatorType || fileExtension || "SourceMap or Not Defined",
				fileExtension : fileExtension || "XHR or Not Defined",
				loadtime : currR.duration,
				fileType : getFileType(fileExtension, currR.initiatorType),
				isRequestToHost : urlFragments[1] === location.host
			};

			for(let attr in currR){
				if(typeof currR[attr] !== "function") {
					currRes[attr] = currR[attr];
				}
			}

			if(currR.requestStart){
				currRes.requestStartDelay = currR.requestStart - currR.startTime;
				currRes.dns = currR.domainLookupEnd - currR.domainLookupStart;
				currRes.tcp = currR.connectEnd - currR.connectStart;
				currRes.ttfb = currR.responseStart - currR.startTime;
				currRes.requestDuration = currR.responseStart - currR.requestStart;
			}
			if(currR.secureConnectionStart){
				currRes.ssl = currR.connectEnd - currR.secureConnectionStart;
			}

			return currRes;
		});

	//filter out non-http[s] and sourcemaps
	data.requestsOnly = data.allResourcesCalc.filter((currR) => {
		return currR.name.indexOf("http") === 0 && !currR.name.match(/js.map$/);
	});
	//get counts
	data.initiatorTypeCounts = getItemCount(data.requestsOnly.map((currR, i, arr) => {
		return currR.initiatorType || currR.fileExtension;
	}), "initiatorType");

	data.initiatorTypeCountHostExt = getItemCount(data.requestsOnly.map((currR, i, arr) => {
		return (currR.initiatorType  || currR.fileExtension) + " " + (currR.isRequestToHost ? "(host)" : "(external)");
	}), "initiatorType");

	data.requestsByDomain = getItemCount(data.requestsOnly.map((currR, i, arr) => currR.domain), "domain");

	data.fileTypeCountHostExt = getItemCount(data.requestsOnly.map((currR, i, arr) => {
		return currR.fileType  + " " + (currR.isRequestToHost ? "(host)" : "(external)");
	}), "fileType");

	data.fileTypeCounts = getItemCount(data.requestsOnly.map((currR, i, arr) => currR.fileType), "fileType");

	const tempResponseEnd = {};
	//TODO: make immutable
	data.requestsOnly.forEach((currR) => {
		const entry = data.requestsByDomain.filter((a) => a.domain == currR.domain)[0]||{};

		const lastResponseEnd = tempResponseEnd[currR.domain]||0;

		currR.duration = entry.duration||(currR.responseEnd - currR.startTime);

		if(lastResponseEnd <= currR.startTime){
			entry.durationTotalParallel = (entry.durationTotalParallel||0) + currR.duration;
		} else if (lastResponseEnd < currR.responseEnd){
			entry.durationTotalParallel = (entry.durationTotalParallel||0) + (currR.responseEnd - lastResponseEnd);
		}
		tempResponseEnd[currR.domain] = currR.responseEnd||0;
		entry.durationTotal = (entry.durationTotal||0) + currR.duration;
	});


	//Request counts
	data.hostRequests = data.requestsOnly
		.filter((domain) => domain.domain === location.host).length;

	data.currAndSubdomainRequests = data.requestsOnly
		.filter((domain) => domain.domain.split(".").slice(-2).join(".") === location.host.split(".").slice(-2).join("."))
		.length;

	data.crossDocDomainRequests = data.requestsOnly
		.filter((domain) => !endsWith(domain.domain, document.domain)).length;

	data.hostSubdomains = data.requestsByDomain
		.filter((domain) => endsWith(domain.domain, location.host.split(".").slice(-2).join(".")) && domain.domain !== location.host)
		.length;


	data.slowestCalls = [];
	data.average = undefined;

	if(data.allResourcesCalc.length > 0){
		data.slowestCalls = data.allResourcesCalc
			.filter((a) => a.name !== location.href)
			.sort((a, b) => b.duration - a.duration);

		data.average = Math.floor(data.slowestCalls.reduceRight((a,b) => {
			if(typeof a !== "number"){
				return a.duration + b.duration
			}
			return a + b.duration;
		}) / data.slowestCalls.length);
	}
	return data
}

function newTag (tagName, settings, css) {
	settings = settings || {};
	const tag = document.createElement(tagName);
	for(let attr in settings){
		if(attr != "text"){
			tag[attr] = settings[attr];
		}
	}
	if(settings.text){
		tag.textContent = settings.text;
	}else if(settings.childElement){
		if(typeof settings.childElement === "object"){
			//if childNodes NodeList is passed in
			if(settings.childElement instanceof NodeList){
				//NodeList is does not inherit from array
				Array.prototype.slice.call(settings.childElement,0).forEach((childNode) => {
					tag.appendChild(childNode);
				});
			}else{
				tag.appendChild(settings.childElement);
			}
		}else{
			tag.appendChild(newTextNode(settings.childElement));
		}
	}
	if(settings.class){
		tag.className = settings.class;
	}
	tag.style.cssText = css||"";
	return tag;
};

function getChartData (data, filter) {
	const calc = {
		pageLoadTime : data.perfTiming.loadEventEnd - data.perfTiming.responseStart,
		lastResponseEnd : data.perfTiming.loadEventEnd - data.perfTiming.responseStart,
	};

	for (let perfProp in data.perfTiming) {
		if(data.perfTiming[perfProp] && typeof data.perfTiming[perfProp] === "number"){
			calc[perfProp] = data.perfTiming[perfProp] - data.perfTiming.navigationStart;
		}
	}

	const onDomLoad = timeBlock("domContentLoaded Event", calc.domContentLoadedEventStart, calc.domContentLoadedEventEnd, "block-dom-content-loaded");
	const onLoadEvt = timeBlock("Onload Event", calc.loadEventStart, calc.loadEventEnd, "block-onload");
	const navigationApiTotal = [
		timeBlock("Unload", calc.unloadEventStart, calc.unloadEventEnd, "block-unload"),
		timeBlock("Redirect", calc.redirectStart, calc.redirectEnd, "block-redirect"),
		timeBlock("App cache", calc.fetchStart, calc.domainLookupStart, "block-appcache"),
		timeBlock("DNS", calc.domainLookupStart, calc.domainLookupEnd, "block-dns"),
		timeBlock("TCP", calc.connectStart, calc.connectEnd, "block-tcp"),
		timeBlock("Timer to First Byte", calc.requestStart, calc.responseStart, "block-ttfb"),
		timeBlock("Response", calc.responseStart, calc.responseEnd, "block-response"),
		timeBlock("DOM Processing", calc.domLoading, calc.domComplete, "block-dom"),
		onDomLoad,
		onLoadEvt
	];

	if(calc.secureConnectionStart){
		navigationApiTotal.push(timeBlock("SSL", calc.connectStart, calc.secureConnectionStart, "block-ssl"));
	}
	if(calc.msFirstPaint){
		navigationApiTotal.push(timeBlock("msFirstPaint Event", calc.msFirstPaint, calc.msFirstPaint, "block-ms-first-paint-event"));
	}
	if(calc.domInteractive){
		navigationApiTotal.push(timeBlock("domInteractive Event", calc.domInteractive, calc.domInteractive, "block-dom-interactive-event"));
	}
	if(!calc.redirectEnd && !calc.redirectStart && calc.fetchStart > calc.navigationStart){
		navigationApiTotal.push(timeBlock("Cross-Domain Redirect", calc.navigationStart, calc.fetchStart, "block-redirect"));
	}

	calc.blocks = [
		timeBlock("Navigation API total", 0, calc.loadEventEnd, "block-navigation-api-total", navigationApiTotal),
	];

	data.allResourcesCalc.filter((resource) => {
			//do not show items up to 15 seconds after onload - else beacon ping etc make diagram useless
			return resource.startTime < (calc.loadEventEnd + 15000)
		})
		.filter(filter||(() => true))
		.forEach((resource, i) => {
			const segments = [
				timeBlock("Redirect", resource.redirectStart, resource.redirectEnd, "block-redirect"),
				timeBlock("DNS Lookup", resource.domainLookupStart, resource.domainLookupEnd, "block-dns"),
				timeBlock("Initial Connection (TCP)", resource.connectStart, resource.connectEnd, "block-dns"),
				timeBlock("secureConnect", resource.secureConnectionStart||undefined, resource.connectEnd, "block-ssl"),
				timeBlock("Timer to First Byte", resource.requestStart, resource.responseStart, "block-ttfb"),
				timeBlock("Content Download", resource.responseStart||undefined, resource.responseEnd, "block-response")
			];

			const resourceTimings = [0, resource.redirectStart, resource.domainLookupStart, resource.connectStart, resource.secureConnectionStart, resource.requestStart, resource.responseStart];

			const firstTiming = resourceTimings.reduce((currMinTiming, currentValue) => {
				if(currentValue > 0 && (currentValue < currMinTiming || currMinTiming <= 0) && currentValue != resource.startTime){
					return currentValue;
				} else {
					return currMinTiming;
				}
			});

			if(resource.startTime < firstTiming){
				segments.unshift(timeBlock("Stalled/Blocking", resource.startTime, firstTiming, "block-blocking"));
			}

			calc.blocks.push(timeBlock(resource.name, resource.startTime, resource.responseEnd, "block-" + resource.initiatorType, segments, resource));
			calc.lastResponseEnd = Math.max(calc.lastResponseEnd || 1,resource.responseEnd);
		});
	return {
		loadDuration : Math.round(Math.max(calc.lastResponseEnd, (data.perfTiming.loadEventEnd-data.perfTiming.navigationStart))),
		blocks : calc.blocks,
		bg : [
			onDomLoad,
			onLoadEvt
		]
	};
};

function resourcesTimelineComponent(parent_element, resources, marks, measures, timing, labels_nodes) {
	var data = getData(resources, marks, measures, timing);
	var chartData = getChartData(data, "");
	const chartHolder = setupTimeLine(parent_element, chartData.loadDuration, chartData.blocks, data.marks, chartData.bg);

	if(data.requestsByDomain.length > 1){
		const selectBox = newTag("select", {
			class : "domain-selector",
			onchange : () => {
				const domain = document.getElementsByClassName("domain-selector")[0].options[document.getElementsByClassName("domain-selector")[0].selectedIndex].value;
				if(domain === "all"){
					chartData = getChartData(data, "");
				}else{
					chartData = getChartData(data, (resource) => resource.domain === domain);
				}
				const tempChartHolder = setupTimeLine(parent_element, chartData.loadDuration, chartData.blocks, data.marks, chartData.bg, "Temp");
				const oldSVG = chartHolder.getElementsByClassName("water-fall-chart")[0];
				const newSVG = tempChartHolder.getElementsByClassName("water-fall-chart")[0];
				chartHolder.replaceChild(newSVG, oldSVG);
			}
		});

		selectBox.appendChild(newTag("option", {
			text : "show all",
			value : "all"
		}));

		data.requestsByDomain.forEach((domain) => {
			selectBox.appendChild(newTag("option", {
				text : domain.domain
			}));
		});
		const chartSvg = chartHolder.getElementsByClassName("water-fall-chart")[0];
		document.getElementById(labels_nodes).parentNode.insertBefore(selectBox, document.getElementById(labels_nodes));
	}

	return chartHolder;
};

function timeBlock(name, start, end, cssClass, segments, rawResource){
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

function setupTimeLine (parent_element, durationMs, blocks, marks, lines, title) {
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


function createLegend (className, title, dlArray) {
	const legendHolder = newTag("div", {
		class : "legend-holder"
	});

	legendHolder.appendChild(newTag("h4", {
		text : title
	}));

	const dl = newTag("dl", {
		class : "legend " + className
	});

	dlArray.forEach((definition) => {
		dl.appendChild(newTag("dt", {
			class : "colorBoxHolder",
			childElement :  newTag("span", {}, "background:"+definition[1])
		}));
		dl.appendChild(newTag("dd", {
			text : definition[0]
		}));
	});
	legendHolder.appendChild(dl);

	return legendHolder;
};

//Legend
function legend() {

	const chartHolder = newTag("section", {
		class : "resource-timing chart-holder"
	});

	chartHolder.appendChild(newTag("h3", {
		text : "Legend"
	}));

	const legendsHolder = newTag("div", {
		class : "legends-group "
	});

	legendsHolder.appendChild(createLegend("initiator-type-legend", "Block color: Initiator Type", [
		["css", "#afd899"],
		["iframe", "#85b3f2"],
		["img", "#bc9dd6"],
		["script", "#e7bd8c"],
		["link", "#89afe6"],
		["swf", "#4db3ba"],
		//["font", "#e96859"],
		["xmlhttprequest", "#e7d98c"]
	]));

	legendsHolder.appendChild(createLegend("navigation-legend", "Navigation Timing", [
		["Redirect", "#ffff60"],
		["App Cache","#1f831f"],
		["DNS Lookup", "#1f7c83"],
		["TCP","#e58226"],
		["SSL Negotiation","#c141cd"],
		["Time to First Byte", "#1fe11f"],
		["Content Download", "#1977dd"],
		["DOM Processing", "#9cc"],
		["DOM Content Loaded", "#d888df"],
		["On Load", "#c0c0ff"]
	]));

	legendsHolder.appendChild(createLegend("resource-legend", "Resource Timing", [
		["Stalled/Blocking", "#cdcdcd"],
		["Redirect", "#ffff60"],
		["App Cache","#1f831f"],
		["DNS Lookup", "#1f7c83"],
		["TCP","#e58226"],
		["SSL Negotiation","#c141cd"],
		["Initial Connection (TCP)", "#e58226"],
		["Time to First Byte", "#1fe11f"],
		["Content Download", "#1977dd"]
	]));

	chartHolder.appendChild(legendsHolder);

	return chartHolder;
};

function createTiles(parent_id, resources, marks, measures, timing, firstPaint, speedIndex) {
    var data = getData(resources, marks, measures, timing);
    [
		createTile("Requests", data.requestsOnly.length||0, 30, 100, ""),
		createTile("Domains", data.requestsByDomain.length||0, 3, 5, ""),
		createTile("Total", data.perfTiming.loadEventEnd - data.perfTiming.navigationStart, 3000, 5000, " ms"),
		createTile("Speed Index", speedIndex, 1000, 3000, ""),
	].forEach(tile => {
		document.getElementById(parent_id+"1").appendChild(tile);
	});
	[
		createTile("Time to First Byte", data.perfTiming.responseStart - data.perfTiming.navigationStart, 200, 1000, " ms"),
		createTile("Time to First Paint", firstPaint, 1000, 3000, " ms"),
		createTile("DOM Content Loading", data.perfTiming.domContentLoadedEventStart - data.perfTiming.domLoading, 1000, 3000, " ms"),
		createTile("DOM Processing", data.perfTiming.domComplete - data.perfTiming.domLoading, 2500, 4500, " ms")
	].forEach(tile => {
		document.getElementById(parent_id+"2").appendChild(tile);
	});
}


function createTile(name, number, yellow_limit, red_limit, addon){
    var color = "ok"
    if (number > yellow_limit && red_limit > number) {
        color = "warning"
    } else if (red_limit < number) {
        color = "error"
    }

    const tile = newTag("div", {
		class : "inline"
	});

	tile.appendChild(newTag("span", {
	    class: "label normal " + color + " tile",
        text: name + ": " + number + addon
	}));
	return tile
}