import { getFileType, getItemCount, endsWith } from "./helpers.js"



export function getData(resources, marks, measures, timing) {
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