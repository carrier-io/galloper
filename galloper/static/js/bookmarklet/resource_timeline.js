function toggleClass(el, className) {
  if (el.classList) {
    el.classList.toggle(className);
  } else {
    // IE doesn't support classList in SVG - also no need for duplication check i.t.m.
    if (el.getAttribute("class").indexOf(className) !== -1) {
      removeClass(el, className)
    } else {
      addClass(el, className)
    }
  }
  return el;
}

function addClass(el, className) {
  if (el.classList) {
    el.classList.add(className);
  } else {
    // IE doesn't support classList in SVG - also no need for duplication check i.t.m.
    el.setAttribute("class", el.getAttribute("class") + " " + className);
  }
  return el;
}

function removeClass(el, className) {
  if (el.classList) {
    el.classList.remove(className);
  } else {
    //IE doesn't support classList in SVG - also no need for duplication check i.t.m.
    el.setAttribute("class", el.getAttribute("class").replace(new RegExp("(\\s|^)" + className + "(\\s|$)", "g"), "$2"));
  }
  return el;
}

function newSvgEl(tagName, settings, css, inner) {
  const el = document.createElementNS('http://www.w3.org/2000/svg', tagName);
  settings = settings || {};
  for (let attr in settings) {
    if (settings.hasOwnProperty(attr) && attr !== 'text') {
      el.setAttributeNS(null, attr, settings[attr]);
    }
  }
  el.textContent = settings.text || '';
  el.style.cssText = css || '';

  if (inner) {
    el.appendChild(inner)
  }

  return el;
}

function newEl(tagName, className, inner) {
  const el = document.createElement(tagName);
  if (className) {
    if (typeof className === 'string') {
      el.classList.add(className);
    } else {
      el.classList.add(...className);
    }
  }

  if (inner) {
    if (typeof inner === 'string' || typeof inner === 'number') {
      el.innerHTML = inner;
    } else {
      el.appendChild(inner);
    }
  }

  return el;
}

function newTextEl(text, y, css) {
  return newSvgEl("text", {
    fill: "#111",
    y: y,
    text: text
  }, (css || "") + " text-shadow:0 0 4px #fff;");
}

function getNodeTextWidth(parent_element, textNode) {
  const tmp = newSvgEl("svg:svg", {}, "visibility:hidden;");
  tmp.appendChild(textNode);
  document.getElementById(parent_element).appendChild(tmp);

  const nodeWidth = textNode.getBBox().width;
  tmp.parentNode.removeChild(tmp);
  return nodeWidth;
}

function endsWith(str, suffix) {
  return str.indexOf(suffix, str.length - suffix.length) !== -1;
}

function getFileType(fileExtension, initiatorType) {
  if (fileExtension) {
    switch (fileExtension) {
      case "jpg" :
      case "jpeg" :
      case "png" :
      case "gif" :
      case "webp" :
      case "svg" :
      case "ico" :
        return "image";
      case "js" :
        return "js";
      case "css":
        return "css";
      case "html":
        return "html";
      case "woff":
      case "woff2":
      case "ttf":
      case "eot":
      case "otf":
        return "font";
      case "swf":
        return "flash";
      case "map":
        return "source-map";
    }
  }
  if (initiatorType) {
    switch (initiatorType) {
      case "xmlhttprequest" :
        return "ajax";
      case "img" :
        return "image";
      case "script" :
        return "js";
      case "internal" :
      case "iframe" :
        return "html"; //actual page
      default :
        return "other"
    }
  }
  return initiatorType;
}

function getItemCount(arr, keyName) {
  let counts = {},
    resultArr = [],
    obj;

  arr.forEach((key) => {
    counts[key] = counts[key] ? counts[key] + 1 : 1;
  });

  //pivot data
  for (let fe in counts) {
    obj = {};
    obj[keyName || "key"] = fe;
    obj.count = counts[fe];

    resultArr.push(obj);
  }
  return resultArr.sort((a, b) => {
    return a.count < b.count ? 1 : -1;
  });
}

function getData(resources, marks, measures, timing) {
  const data = {
    resources: resources,
    marks: marks,
    measures: measures,
    perfTiming: timing,
    allResourcesCalc: [],
    isValid: () => isValid
  };

  data.allResourcesCalc = data.resources
    //remove this bookmarklet from the result
    .filter((currR) => !currR.name.match(/http[s]?:\/\/(micmro|nurun).github.io\/performance-bookmarklet\/.*/))
    .map(currR => {
      //crunch the resources data into something easier to work with
      const isRequest = currR.name.indexOf("http") === 0;
      let urlFragments, maybeFileName, fileExtension;

      if (isRequest) {
        urlFragments = currR.name.match(/:\/\/(.[^/]+)([^?]*)\??(.*)/);
        maybeFileName = urlFragments[2].split("/").pop();
        fileExtension = maybeFileName.substr((Math.max(0, maybeFileName.lastIndexOf(".")) || Infinity) + 1);
      } else {
        urlFragments = ["", location.host];
        fileExtension = currR.name.split(":")[0];
      }

      const currRes = {
        name: currR.name,
        domain: urlFragments[1],
        initiatorType: currR.initiatorType || fileExtension || "SourceMap or Not Defined",
        fileExtension: fileExtension || "XHR or Not Defined",
        loadtime: currR.duration,
        fileType: getFileType(fileExtension, currR.initiatorType),
        isRequestToHost: urlFragments[1] === location.host
      };

      for (let attr in currR) {
        if (currR.hasOwnProperty(attr) && typeof currR[attr] !== "function") {
          currRes[attr] = currR[attr];
        }
      }

      if (currR.requestStart) {
        currRes.requestStartDelay = currR.requestStart - currR.startTime;
        currRes.dns = currR.domainLookupEnd - currR.domainLookupStart;
        currRes.tcp = currR.connectEnd - currR.connectStart;
        currRes.ttfb = currR.responseStart - currR.startTime;
        currRes.requestDuration = currR.responseStart - currR.requestStart;
      }
      if (currR.secureConnectionStart) {
        currRes.ssl = currR.connectEnd - currR.secureConnectionStart;
      }

      return currRes;
    });

  //filter out non-http[s] and sourcemaps
  data.requestsOnly = data.allResourcesCalc.filter((currR) => {
    return currR.name.indexOf("http") === 0 && !currR.name.match(/js.map$/);
  });
  //get counts
  data.initiatorTypeCounts = getItemCount(data.requestsOnly.map((currR) => {
    return currR.initiatorType || currR.fileExtension;
  }), "initiatorType");

  data.initiatorTypeCountHostExt = getItemCount(data.requestsOnly.map((currR) => {
    return (currR.initiatorType || currR.fileExtension) + " " + (currR.isRequestToHost ? "(host)" : "(external)");
  }), "initiatorType");

  data.requestsByDomain = getItemCount(data.requestsOnly.map((currR) => currR.domain), "domain");

  data.fileTypeCountHostExt = getItemCount(data.requestsOnly.map((currR) => {
    return currR.fileType + " " + (currR.isRequestToHost ? "(host)" : "(external)");
  }), "fileType");

  data.fileTypeCounts = getItemCount(data.requestsOnly.map((currR) => currR.fileType), "fileType");

  const tempResponseEnd = {};
  //TODO: make immutable
  data.requestsOnly.forEach((currR) => {
    const entry = data.requestsByDomain.filter((a) => a.domain === currR.domain)[0] || {};

    const lastResponseEnd = tempResponseEnd[currR.domain] || 0;

    currR.duration = entry.duration || (currR.responseEnd - currR.startTime);

    if (lastResponseEnd <= currR.startTime) {
      entry.durationTotalParallel = (entry.durationTotalParallel || 0) + currR.duration;
    } else if (lastResponseEnd < currR.responseEnd) {
      entry.durationTotalParallel = (entry.durationTotalParallel || 0) + (currR.responseEnd - lastResponseEnd);
    }
    tempResponseEnd[currR.domain] = currR.responseEnd || 0;
    entry.durationTotal = (entry.durationTotal || 0) + currR.duration;
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

  if (data.allResourcesCalc.length > 0) {
    data.slowestCalls = data.allResourcesCalc
      .filter((a) => a.name !== location.href)
      .sort((a, b) => b.duration - a.duration);

    data.average = Math.floor(data.slowestCalls.reduceRight((a, b) => {
      if (typeof a !== "number") {
        return a.duration + b.duration
      }
      return a + b.duration;
    }) / data.slowestCalls.length);
  }
  return data
}

function newTag(tagName, settings, css) {
  settings = settings || {};
  const tag = document.createElement(tagName);
  for (let attr in settings) {
    if (attr !== "text" && settings.hasOwnProperty(attr)) {
      tag[attr] = settings[attr];
    }
  }
  if (settings.text) {
    tag.textContent = settings.text;
  } else if (settings.childElement) {
    if (typeof settings.childElement === "object") {
      //if childNodes NodeList is passed in
      if (settings.childElement instanceof NodeList) {
        //NodeList is does not inherit from array
        Array.prototype.slice.call(settings.childElement, 0).forEach((childNode) => {
          tag.appendChild(childNode);
        });
      } else {
        tag.appendChild(settings.childElement);
      }
    } else {
      tag.appendChild(newTextNode(settings.childElement));
    }
  }
  if (settings.class) {
    tag.className = settings.class;
  }
  tag.style.cssText = css || "";
  return tag;
}

function getChartData(data, filter) {
  const calc = {
    pageLoadTime: data.perfTiming.loadEventEnd - data.perfTiming.responseStart,
    lastResponseEnd: data.perfTiming.loadEventEnd - data.perfTiming.responseStart,
    blocks: [],
    total: {}
  };

  Object.keys(data.perfTiming).forEach(key => {
    if (data.perfTiming[key] && typeof data.perfTiming[key] === "number") {
      calc[key] = data.perfTiming[key] - data.perfTiming.navigationStart;
    }
  });

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

  if (calc.secureConnectionStart) {
    navigationApiTotal.push(timeBlock("SSL", calc.connectStart, calc.secureConnectionStart, "block-ssl"));
  }
  if (calc.msFirstPaint) {
    navigationApiTotal.push(timeBlock("msFirstPaint Event", calc.msFirstPaint, calc.msFirstPaint, "block-ms-first-paint-event"));
  }
  if (calc.domInteractive) {
    navigationApiTotal.push(timeBlock("domInteractive Event", calc.domInteractive, calc.domInteractive, "block-dom-interactive-event"));
  }
  if (!calc.redirectEnd && !calc.redirectStart && calc.fetchStart > calc.navigationStart) {
    navigationApiTotal.push(timeBlock("Cross-Domain Redirect", calc.navigationStart, calc.fetchStart, "block-redirect"));
  }

  calc.total = timeBlock("Navigation API total", 0, calc.loadEventEnd, "block-navigation-api-total", navigationApiTotal);

  data.allResourcesCalc.filter((resource) => {
    //do not show items up to 15 seconds after onload - else beacon ping etc make diagram useless
    return resource.startTime < (calc.loadEventEnd + 15000)
  }).filter(filter || (() => true)).forEach(resource => {
    const segments = [
      timeBlock("Redirect", resource.redirectStart, resource.redirectEnd, "block-redirect"),
      timeBlock("DNS Lookup", resource.domainLookupStart, resource.domainLookupEnd, "block-dns"),
      timeBlock("Initial Connection (TCP)", resource.connectStart, resource.connectEnd, "block-dns"),
      timeBlock("secureConnect", resource.secureConnectionStart || undefined, resource.connectEnd, "block-ssl"),
      timeBlock("Timer to First Byte", resource.requestStart, resource.responseStart, "block-ttfb"),
      timeBlock("Content Download", resource.responseStart || undefined, resource.responseEnd, "block-response")
    ];

    const resourceTimings = [0, resource.redirectStart, resource.domainLookupStart, resource.connectStart, resource.secureConnectionStart, resource.requestStart, resource.responseStart];

    const firstTiming = resourceTimings.reduce((currMinTiming, currentValue) => {
      if (currentValue > 0 && (currentValue < currMinTiming || currMinTiming <= 0) && currentValue !== resource.startTime) {
        return currentValue;
      } else {
        return currMinTiming;
      }
    });

    if (resource.startTime < firstTiming) {
      segments.unshift(timeBlock("Stalled/Blocking", resource.startTime, firstTiming, "block-blocking"));
    }

    calc.blocks.push(timeBlock(resource.name, resource.startTime, resource.responseEnd, "block-" + resource.initiatorType, segments, resource));
    calc.lastResponseEnd = Math.max(calc.lastResponseEnd || 1, resource.responseEnd);
  });

  return {
    loadDuration: Math.round(Math.max(calc.lastResponseEnd, (data.perfTiming.loadEventEnd - data.perfTiming.navigationStart))),
    blocks: calc.blocks,
    total: calc.total,
    bg: [
      onDomLoad,
      onLoadEvt
    ]
  };
}

function resourcesTimelineComponent(chartElement, selectorElement, resources, marks, measures, timing) {
  const data = getData(resources, marks, measures, timing);
  const chartData = getChartData(data, "");
  const chartHolder = setupTimeLine(chartElement, chartData.loadDuration, chartData.blocks, data.marks, chartData.bg);
  const barHeight = 15;

  const totalChartHolder = document.getElementById('waterfall-total');
  const totalChart = getTimeline(chartData.total, chartData.loadDuration / 100, barHeight);
  totalChartHolder.appendChild(getInfoPopup(chartData.total, barHeight));
  totalChartHolder.appendChild(totalChart);

  addTimeSteps(totalChartHolder, chartData.loadDuration);

  window.addEventListener('resize', () => {
    removeTimeSteps(totalChartHolder);
    addTimeSteps(totalChartHolder, chartData.loadDuration)
  }, { passive: true });

  if (data.requestsByDomain.length > 1) {
    const selector = newTag("select", {
      class: "domain-selector",
      onchange: (e) => {
        domainSelect(e, chartHolder, chartElement, chartData, data)
      }
    });

    selector.appendChild(newTag("option", {
      text: "All",
      value: "all"
    }));

    data.requestsByDomain.forEach((domain) => {
      selector.appendChild(newTag("option", {
        text: domain.domain
      }));
    });

    document.getElementById(selectorElement).appendChild(selector);
  }

  return chartHolder;
}

function addTimeSteps(holder, duration) {
  const seconds = Math.floor(duration / 1000);
  const holderStep = holder.offsetWidth / duration;

  for (let i = 0; i <= seconds; i++) {
    addTimeGrid(holder, `${holderStep * i * 1000}px`, 'time-grid-step', `${i} sec`);
  }
}

function removeTimeSteps(holder) {
  const steps = holder.querySelectorAll('.time-grid-step');
  steps.forEach(child => holder.removeChild(child));
}

function domainSelect(e, chartHolder, chartElement, chartData, data) {
  const domain = e.target.value;

  if (domain === "all") {
    chartData = getChartData(data, "");
  } else {
    chartData = getChartData(data, (resource) => resource.domain === domain);
  }

  chartHolder.replaceWith(setupTimeLine(chartElement, chartData.loadDuration, chartData.blocks, data.marks, chartData.bg));
}

function timeBlock(name, start, end, cssClass, segments, rawResource) {
  return {
    name: name,
    start: start,
    end: end,
    total: ((typeof start !== "number" || typeof end !== "number") ? undefined : (end - start)),
    cssClass: cssClass,
    segments: segments,
    rawResource: rawResource
  }
}

function setupTimeLine(parent_element, durationMs, blocks, marks, lines) {
  const barHeight = 15;
  const unit = durationMs / 100;
  const barsToShow = blocks
    .filter((block) => (typeof block.start == "number" && typeof block.total == "number"))
    .sort((a, b) => (a.start || 0) - (b.start || 0));
  const maxMarkTextLength = marks.length > 0 ? marks.reduce((currMax, currValue) => {
    return Math.max((typeof currMax == "number" ? currMax : 0), getNodeTextWidth(parent_element, newTextEl(currValue.name, "0")));
  }) : 0;
  const diagramHeight = (barsToShow.length + 1) * barHeight;
  const chartHolderHeight = diagramHeight + maxMarkTextLength + 35;

  const chartHolder = newTag("section", {
    class: "resource-timing water-fall-holder chart-holder"
  });
  const timeLineHolder = newSvgEl("svg:svg", {
    height: Math.floor(chartHolderHeight),
    class: "water-fall-chart"
  });

  timeLineHolder.appendChild(createTimeWrapper());
  timeLineHolder.appendChild(renderMarks());

  lines.forEach((block) => timeLineHolder.appendChild(createBgRect(block)));

  const waterfall = document.getElementById('waterfall');
  const tableBody = waterfall.querySelector('tbody');
  tableBody.innerHTML = '';

  barsToShow.forEach(block => {
    const row = newEl('tr');
    const timeLine = getTimeline(block, unit, barHeight);
    const timeLineTd = newEl('td', 'timeline');

    timeLineTd.appendChild(getInfoPopup(block, barHeight));

    const svgHolder = newEl('div', 'svgWrapper');
    svgHolder.appendChild(timeLine);
    timeLineTd.appendChild(svgHolder);

    const nameTd = newEl('td', 'name');
    const nameText = block.name.trim().split('?').shift().split('/').pop();
    nameTd.innerText = nameText || block.name;
    nameTd.setAttribute('title', block.name);

    const durationTd = newEl('td', 'duration');
    durationTd.innerText = Math.round(block.total);

    row.appendChild(nameTd);
    row.appendChild(durationTd);
    row.appendChild(timeLineTd);

    tableBody.append(row);
  });

  return chartHolder;

  function createBgRect(block) {
    const rect = newSvgEl("rect", {
      width: ((block.total || 1) / unit) + "%",
      height: diagramHeight,
      x: ((block.start || 0.001) / unit) + "%",
      y: 0,
      class: block.cssClass || "block-undefined"
    });

    rect.appendChild(newSvgEl("title", {
      text: block.name
    })); // Add tile to wedge path
    return rect;
  }

  function createTimeWrapper() {
    const timeHolder = newSvgEl("g", { class: "time-scale full-width" });
    for (let i = 0, secs = durationMs / 1000, secPerc = 100 / secs; i <= secs; i++) {
      const lineLabel = newTextEl(i + "sec", diagramHeight);
      if (i > secs - 0.2) {
        lineLabel.setAttribute("x", secPerc * i - 0.5 + "%");
        lineLabel.setAttribute("text-anchor", "end");
      } else {
        lineLabel.setAttribute("x", secPerc * i + 0.5 + "%");
      }

      const lineEl = newSvgEl("line", {
        x1: secPerc * i + "%",
        y1: "0",
        x2: secPerc * i + "%",
        y2: diagramHeight
      });
      timeHolder.appendChild(lineEl);
      timeHolder.appendChild(lineLabel);
    }
    return timeHolder;
  }

  function renderMarks() {
    const marksHolder = newSvgEl("g", {
      transform: "scale(1, 1)",
      class: "marker-holder"
    });

    marks.forEach((mark, i) => {
      const x = mark.startTime / unit;
      const markHolder = newSvgEl("g", {
        class: "mark-holder"
      });
      const lineHolder = newSvgEl("g", {
        class: "line-holder"
      });
      const lineLabelHolder = newSvgEl("g", {
        class: "line-label-holder",
        x: x + "%"
      });
      mark.x = x;
      const lineLabel = newTextEl(mark.name, diagramHeight + 25);
      //lineLabel.setAttribute("writing-mode", "tb");
      lineLabel.setAttribute("x", x + "%");
      lineLabel.setAttribute("stroke", "");

      lineHolder.appendChild(newSvgEl("line", {
        x1: x + "%",
        y1: 0,
        x2: x + "%",
        y2: diagramHeight
      }));

      if (marks[i - 1] && mark.x - marks[i - 1].x < 1) {
        lineLabel.setAttribute("x", marks[i - 1].x + 1 + "%");
        mark.x = marks[i - 1].x + 1;
      }

      //would use polyline but can't use percentage for points
      lineHolder.appendChild(newSvgEl("line", {
        x1: x + "%",
        y1: diagramHeight,
        x2: mark.x + "%",
        y2: diagramHeight + 23
      }));

      let isActive = false;
      const onLabelMouseEnter = () => {
        if (!isActive) {
          isActive = true;
          addClass(lineHolder, "active");
          //firefox has issues with this
          markHolder.parentNode.appendChild(markHolder);
        }
      };

      const onLabelMouseLeave = () => {
        isActive = false;
        removeClass(lineHolder, "active");
      };

      lineLabel.addEventListener("mouseenter", onLabelMouseEnter);
      lineLabel.addEventListener("mouseleave", onLabelMouseLeave);
      lineLabelHolder.appendChild(lineLabel);

      markHolder.appendChild(newSvgEl("title", {
        text: mark.name + " (" + Math.round(mark.startTime) + "ms)",
      }));
      markHolder.appendChild(lineHolder);
      marksHolder.appendChild(markHolder);
      markHolder.appendChild(lineLabelHolder);
    });

    return marksHolder;
  }
}

function getInfoPopup(block, barHeight) {
  const el = newEl('div', 'info-popup');
  el.appendChild(getInfo(block));
  return el;

  function getInfo(block) {
    const popupFragment = document.createDocumentFragment();
    const { segments, ...restBlock } = block;
    const unit = restBlock.total / 100;

    popupFragment.appendChild(newEl('h3', 'info-title', block.name));

    const startEndTable = newEl('table', 'info-table');
    const startEl = getInfoRow('Started', restBlock.start);
    const endEl = getInfoRow('Ended', restBlock.end);

    startEndTable.appendChild(startEl);
    startEndTable.appendChild(endEl);
    popupFragment.appendChild(startEndTable);

    const segmentsTableInner = segments.reduce((fragment, segment) => {
      if (segment.total) {
        const timeLine = getTimeline(segment, unit, barHeight, block.start);

        fragment.appendChild(getInfoRow(segment.name, segment.total, timeLine));
      }
      return fragment;
    }, document.createDocumentFragment());

    const totalTimeLine = getTimeline(restBlock, unit, barHeight, block.start);
    const totalRow = getInfoRow('Navigation API total', restBlock.total, totalTimeLine, 'total');
    segmentsTableInner.appendChild(totalRow);

    if (segmentsTableInner.childNodes.length > 0) {
      popupFragment.appendChild(newEl('h4', 'info-subtitle', 'Navigation timing'));
      popupFragment.appendChild(newEl('table', 'info-table', segmentsTableInner));
    }

    return popupFragment;
  }

  function getInfoRow(title, number, middleInner, cssClass) {
    const row = newEl('tr', cssClass);

    const startEl = newEl('td', '', title);
    row.appendChild(startEl);

    if (middleInner) {
      const middleEl = newEl('td', '', middleInner);
      row.appendChild(middleEl)
    }

    const endEl = newEl('td', '', `${(+number).toFixed()} ms`);
    row.appendChild(endEl);

    return row;
  }
}

function getTimeline(block, unit, height, infoStart) {
  const { segments, total, start, end, cssClass, name } = block;

  const width = total || 1;
  const x = infoStart && start ? start - infoStart : (start || 0.001);
  const y = 0;
  const label = name + " (" + start + "ms - " + end + "ms | total: " + total + "ms)";

  const timeLine = createRect(width, height, x, y, unit, cssClass, label, segments);
  const settings = {
    width: total,
    class: "water-fall-chart",
    height,
  };

  return newSvgEl("svg:svg", settings, '', timeLine);
}

function createRect(width, height, x, y, unit, cssClass, label, segments) {
  const rectHeight = height - 1;
  const holder = newSvgEl("g");

  let rectHolder;
  const rect = newSvgEl("rect", {
    width: (width / unit) + "%",
    height: rectHeight,
    x: Math.round((x / unit) * 100) / 100 + "%",
    y: y,
    class: ((segments && segments.length > 0 ? "time-block" : "segment")) + " " + (cssClass || "block-undefined")
  });
  if (label) {
    rect.appendChild(newSvgEl("title", {
      text: label
    })); // Add tile to wedge path
  }

  rect.addEventListener("mouseenter", onRectMouseEnter);
  rect.addEventListener("mouseleave", onRectMouseLeave);

  if (segments && segments.length > 0) {
    rectHolder = newSvgEl("g");
    rectHolder.appendChild(rect);

    segments.forEach((segment) => {
      if (segment.total > 0 && typeof segment.start === "number") {
        rectHolder.appendChild(createRect(segment.total, 8, segment.start || 0.001, y, unit, segment.cssClass, segment.name + " (" + Math.round(segment.start) + "ms - " + Math.round(segment.end) + "ms | total: " + Math.round(segment.total) + "ms)"));
      }
    });
    holder.appendChild(rectHolder);
  } else {
    holder.appendChild(rect);
  }

  return holder;

  function onRectMouseEnter(evt) {
    const targetRect = evt.target;
    const svgHolder = targetRect.closest('.svgWrapper');

    if (svgHolder) {
      addTimeGrid(svgHolder, targetRect.x.baseVal.value + "px", 'start');
      addTimeGrid(svgHolder, targetRect.x.baseVal.value + targetRect.width.baseVal.value - 1 + "px", 'end');
    }

    addClass(targetRect, "active");
  }

  function onRectMouseLeave(evt) {
    const targetRect = evt.target;
    const svgHolder = targetRect.closest('.svgWrapper');

    if (svgHolder) {
      removeTimeGrid(svgHolder, 'start');
      removeTimeGrid(svgHolder, 'end');
    }

    removeClass(evt.target, "active");
  }
}

function addTimeGrid(holder, position, cssClass, title, titlePosition) {
  const line = newEl('div', [cssClass, 'time-grid']);
  line.style.transform = 'translateX(' + position + ")";
  if (title) {
    const positionClass = titlePosition ? `time-grid-${titlePosition}` : `time-grid-right`;
    line.appendChild(newEl('div', [positionClass, 'time-grid-label', 'top'], title));
    line.appendChild(newEl('div', [positionClass, 'time-grid-label', 'bottom'], title));
  }
  holder.appendChild(line);
}

function removeTimeGrid(holder, cssClass) {
  const line = holder.getElementsByClassName(cssClass);

  if (line.length) {
    holder.removeChild(line[0]);
  }
}

function createLegend(className, title, dlArray) {
  const legendHolder = newTag("div", {
    class: "legend-holder"
  });

  legendHolder.appendChild(newTag("h4", {
    text: title
  }));

  const dl = newTag("dl", {
    class: "legend " + className
  });

  dlArray.forEach((definition) => {
    dl.appendChild(newTag("dt", {
      class: "colorBoxHolder",
      childElement: newTag("span", {}, "background:" + definition[1])
    }));
    dl.appendChild(newTag("dd", {
      text: definition[0]
    }));
  });
  legendHolder.appendChild(dl);

  return legendHolder;
}

//Legend
function legend() {
  const legendHolder = document.createDocumentFragment();

  const legendLabel = newTag("label", {
    text: "Legend",
    id: 'legend-label',
    htmlFor: 'legend-checkbox'
  });
  const legendCheckbox = newTag("input", {
    type: "checkbox",
    id: 'legend-checkbox'
  });

  legendHolder.appendChild(legendLabel);
  legendHolder.appendChild(legendCheckbox);

  const legendsHolder = newTag("div", {
    class: "legends-group"
  });
  const legendTitle = newTag("h3", {
    text: "Legend",
  });
  legendsHolder.appendChild(legendTitle);

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
    ["App Cache", "#1f831f"],
    ["DNS Lookup", "#1f7c83"],
    ["TCP", "#e58226"],
    ["SSL Negotiation", "#c141cd"],
    ["Time to First Byte", "#1fe11f"],
    ["Content Download", "#1977dd"],
    ["DOM Processing", "#9cc"],
    ["DOM Content Loaded", "#d888df"],
    ["On Load", "#c0c0ff"]
  ]));

  legendsHolder.appendChild(createLegend("resource-legend", "Resource Timing", [
    ["Stalled/Blocking", "#cdcdcd"],
    ["Redirect", "#ffff60"],
    ["App Cache", "#1f831f"],
    ["DNS Lookup", "#1f7c83"],
    ["TCP", "#e58226"],
    ["SSL Negotiation", "#c141cd"],
    ["Initial Connection (TCP)", "#e58226"],
    ["Time to First Byte", "#1fe11f"],
    ["Content Download", "#1977dd"]
  ]));

  legendHolder.appendChild(legendsHolder);

  return legendHolder;
}

function createTiles(parent_id, resources, marks, measures, timing, firstPaint, speedIndex) {
  const data = getData(resources, marks, measures, timing);
  const tilesHolder = document.getElementById(parent_id);

  const leftTile = newTag('div', { class: 'tile-container' });
  [
    createTile("Requests", data.requestsOnly.length || 0, 30, 100, ""),
    createTile("Domains", data.requestsByDomain.length || 0, 3, 5, ""),
    createTile("Total", data.perfTiming.loadEventEnd - data.perfTiming.navigationStart, 3000, 5000, "ms"),
    createTile("Speed Index", speedIndex, 1000, 3000, ""),
  ].forEach(tile => {
    leftTile.appendChild(tile);
  });

  const rightTile = newTag('div', { class: 'tile-container' });
  [
    createTile("Time to First Byte", data.perfTiming.responseStart - data.perfTiming.navigationStart, 200, 1000, "ms"),
    createTile("Time to First Paint", firstPaint, 1000, 3000, " ms"),
    createTile("DOM Content Loading", data.perfTiming.domContentLoadedEventStart - data.perfTiming.domLoading, 1000, 3000, "ms"),
    createTile("DOM Processing", data.perfTiming.domComplete - data.perfTiming.domLoading, 2500, 4500, "ms")
  ].forEach(tile => {
    rightTile.appendChild(tile);
  });

  tilesHolder.appendChild(leftTile);
  tilesHolder.appendChild(rightTile);
}

function createTile(name, number, yellow_limit, red_limit, addon) {
  let color = "ok";
  if (number > yellow_limit && red_limit > number) {
    color = "warning"
  } else if (red_limit < number) {
    color = "error"
  }

  const tile = newTag("div", {
    class: "tile"
  });

  tile.appendChild(newTag("span", {
    class: "title",
    text: name
  }));
  tile.appendChild(newTag("span", {
    class: "value " + color + "-text",
    text: number + " " + addon
  }));

  return tile
}
