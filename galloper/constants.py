#   Copyright 2019 getcarrier.io
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.

from os import environ
from datetime import datetime
from urllib.parse import urlparse

LOCAL_DEV = False

ALLOWED_EXTENSIONS = ['zip', 'py']
CURRENT_RELEASE = 'latest'
REDIS_USER = environ.get('REDIS_USER', '')
REDIS_PASSWORD = environ.get('REDIS_PASSWORD', 'password')
REDIS_HOST = environ.get('REDIS_HOST', 'localhost')
REDIS_PORT = environ.get('REDIS_PORT', '6379')
REDIS_DB = environ.get('REDIS_DB', 2)
RABBIT_HOST = environ.get('RABBIT_HOST', 'carrier-rabbit')
RABBIT_USER = environ.get('RABBIT_USER', 'user')
RABBIT_PASSWORD = environ.get('RABBIT_PASSWORD', 'password')
RABBIT_PORT = environ.get('RABBIT_PORT', '5672')
RABBIT_QUEUE_NAME = environ.get('RABBIT_QUEUE_NAME', 'default')
APP_HOST = environ.get('APP_HOST', 'localhost')
GF_API_KEY = environ.get('GF_API_KEY', '')
INFLUX_PASSWORD = environ.get('INFLUX_PASSWORD', '')
INFLUX_USER = environ.get('INFLUX_USER', '')
INFLUX_PORT = 8086
LOKI_PORT = 3100
_url = urlparse(APP_HOST)
EXTERNAL_LOKI_HOST = f"http://{_url.netloc.split('@')[1]}" if "@" in APP_HOST else APP_HOST.replace("https://", "http://")
INTERNAL_LOKI_HOST = "http://carrier-loki"
APP_IP = urlparse(EXTERNAL_LOKI_HOST).netloc
POST_PROCESSOR_PATH = "https://github.com/carrier-io/performance_post_processor/raw/master/package/post_processing.zip"
CONTROL_TOWER_PATH = "https://github.com/carrier-io/control_tower/raw/master/package/control-tower.zip"
EMAIL_NOTIFICATION_PATH = "https://github.com/carrier-io/performance_email_notification/raw/master/package/email_notifications.zip"
MINIO_ENDPOINT = environ.get('MINIO_HOST', 'http://127.0.0.1:9000' if LOCAL_DEV else 'http://carrier-minio:9000')
MINIO_ACCESS = environ.get('MINIO_ACCESS_KEY', 'admin')
MINIO_SECRET = environ.get('MINIO_SECRET_KEY', 'password')
MINIO_REGION = environ.get('MINIO_REGION', 'us-east-1')
LOKI_HOST = environ.get('LOKI', 'http://carrier-loki:3100')
MAX_DOTS_ON_CHART = 100
VAULT_URL = environ.get('VAULT_URL', 'http://127.0.0.1:8200' if LOCAL_DEV else 'http://carrier-vault:8200')
VAULT_DB_PK = 1
GRID_ROUTER_URL = environ.get("GRID_ROUTER_URL", f"{EXTERNAL_LOKI_HOST}:4444/quota")

NAME_CONTAINER_MAPPING = {
    "Python 3.7": 'lambda:python3.7',
    "Python 3.8": 'lambda:python3.8',
    "Python 3.6": 'lambda:python3.6',
    "Python 2.7": 'lambda:python2.7',
    ".NET Core 2.0 (C#)": 'lambda:dotnetcore2.0',
    ".NET Core 2.1 (C#/PowerShell)": 'lambda:dotnetcore2.1',
    "Go 1.x": "lambda:go1.x",
    "Java 8": "lambda:java8",
    "Java 11": "lambda:java11",
    "Node.js 6.10": 'nodejs6.10',
    "Node.js 8.10": 'lambda:nodejs8.10',
    "Node.js 10.x": 'lambda:nodejs10.x',
    "Node.js 12.x": 'lambda:nodejs12.x',
    "Ruby 2.5": 'lambda:ruby2.5'
}

JOB_CONTAINER_MAPPING = {
    "v5.3": {
        "container": f"getcarrier/perfmeter:{CURRENT_RELEASE}-5.3",
        "job_type": "perfmeter",
        "influx_db": "{{secret.jmeter_db}}"
    },
    "v5.2.1": {
        "container": f"getcarrier/perfmeter:{CURRENT_RELEASE}-5.2.1",
        "job_type": "perfmeter",
        "influx_db": "{{secret.jmeter_db}}"
    },
    "v5.2": {
        "container": f"getcarrier/perfmeter:{CURRENT_RELEASE}-5.2",
        "job_type": "perfmeter",
        "influx_db": "{{secret.jmeter_db}}"
    },
    "v5.1.1": {
        "container": f"getcarrier/perfmeter:{CURRENT_RELEASE}-5.1.1",
        "job_type": "perfmeter",
        "influx_db": "{{secret.jmeter_db}}"
    },
    "v5.1": {
        "container": f"getcarrier/perfmeter:{CURRENT_RELEASE}-5.1",
        "job_type": "perfmeter",
        "influx_db": "{{secret.jmeter_db}}"
    },
    "v5.0": {
        "container": f"getcarrier/perfmeter:{CURRENT_RELEASE}-5.0",
        "job_type": "perfmeter",
        "influx_db": "{{secret.jmeter_db}}"
    },
    "v4.0": {
        "container": f"getcarrier/perfmeter:{CURRENT_RELEASE}-4.0",
        "job_type": "perfmeter",
        "influx_db": "{{secret.jmeter_db}}"
    },
    "v3.1": {
        "container": f"getcarrier/perfgun:{CURRENT_RELEASE}-3.1",
        "job_type": "perfgun",
        "influx_db": "{{secret.gatling_db}}"
    },
    "v2.3": {
        "container": f"getcarrier/perfgun:{CURRENT_RELEASE}-2.3",
        "job_type": "perfgun",
        "influx_db": "{{secret.gatling_db}}"
    }
}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def str_to_timestamp(str_ts):
    timestamp = str_ts.replace("Z", "")
    if "." not in timestamp:
        timestamp += "."
    timestamp += "".join(["0" for _ in range(26 - len(timestamp))])
    timestamp = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S.%f").timestamp()
    return timestamp


UNZIP_DOCKERFILE = """FROM kubeless/unzip:latest
ADD {localfile} /tmp/{docker_path}
ENTRYPOINT ["unzip", "/tmp/{docker_path}", "-d", "/tmp/unzipped"]
"""


UNZIP_DOCKER_COMPOSE = """version: '3'
services:
  unzip:
    build: {path}
    volumes:
      - {volume}:/tmp/unzipped
    labels:
      - 'traefik.enable=false'
    container_name: unzip-{task_id}
volumes:
  {volume}:
    external: true
"""


check_ui_performance = '''return (function() {
var metas=Array.prototype.slice.call(document.querySelectorAll('meta[name][content]'));
var navigation = window.performance.getEntriesByType('navigation');
var docUrl = document.URL;
var docDomain = document.domain;
var docHead = document.head;
var docTitle = document.title;
var performanceObj = window.performance;
var navStart = performanceObj.timing.navigationStart;
var timing = performanceObj.timing;
var marks=[],
	measures=[]
if (window.performance && window.performance.getEntriesByType) {
	var marks = window.performance.getEntriesByType('mark');
	var measures = window.performance.getEntriesByType('measure');
}
var resources = performance.getEntriesByType('resource');
var navigation = performance.getEntriesByType('navigation');
var images = Array.prototype.slice.call(document.getElementsByTagName('img'));
var links = Array.prototype.slice.call(document.getElementsByTagName('link'));
var linksInHead = Array.prototype.slice.call(docHead.getElementsByTagName('link'));
var scripts = Array.prototype.slice.call(docHead.getElementsByTagName('script'));
var html = document.getElementsByTagName('html')
var styles = Array.prototype.slice.call(docHead.getElementsByTagName('style'));
var patterns = ['ajax.googleapis.com', 'apis.google.com', '.google-analytics.com',
				'connect.facebook.net', 'platform.twitter.com', 'code.jquery.com',
				'platform.linkedin.com', '.disqus.com', 'assets.pinterest.com',
				'widgets.digg.com', '.addthis.com', 'code.jquery.com',
				'ad.doubleclick.net', '.lognormal.com', 'embed.spotify.com'];
var browsers_regex = /(Chrome|Firefox|Safari)\/(\S+)/


function getHostname(url) {
    return new URL(url).hostname
}

function getConnectionType() {
	if (navigation && navigation[0] && navigation[0].nextHopProtocol) {
		return navigation[0].nextHopProtocol;
	} else if (performanceObj && window.performance.getEntriesByType && resources) {
		if (resources.length > 1 && resources[0].nextHopProtocol) {
			for (var i = 0, len = resources.length; i < len; i++) {
				if (docDomain === getHostname(resources[i].name)) return resources[i].nextHopProtocol;
			}
		}
	}
    return 'unknown';
}

function getTransferSize(url) {
    var result = resources.filter(resource => resource.name === url);
    if (result.length === 1 && typeof result[0].transferSize === 'number') {
        return result[0].transferSize;
    } else {
        return 0;
    }
}

function getAbsoluteURL(url) {
    return new URL(url).href
}

function exists(element, array) {
    return array.some(function (e) {
        return e === element;
    });
}

function getSynchJSFiles(element) {
    var scripts = Array.prototype.slice.call(element.getElementsByTagName('script'));
    return scripts
        .filter(function (script) {
            return !script.async && script.src && !script.defer;
        })
        .map(function (s) {
            return getAbsoluteURL(s.src);
        });
}

function getAsynchJSFiles(element) {
	var scripts = Array.prototype.slice.call(element.getElementsByTagName('script'));
    return scripts.filter(function(s) {
        return s.async && s.src;
      }).map(function(s) {
        return getAbsoluteURL(s.src);
      });
}

function amp() {
	if ((html[0] && html[0].getAttribute('amp-version')) || window.AMP) {
	    return html[0].getAttribute('amp-version') || true;
	} else {
	    return false;
	}
}

function getCSSFiles() {
    return linksInHead
        .filter(function (link) {
            return link.rel === 'stylesheet' && !link.href.startsWith('data:');
        })
        .map(function (link) {
            return getAbsoluteURL(link.href);
        });
}

function isHTTP2() {
    var type = connectionType.toLowerCase();
    return type === 'h2' || type.startsWith('spdy');
}

function getResourceHintsHrefs (type) {
	return links.filter(function(link) {
		return link.rel === type;
	}).map(function(link) {
		return link.href;
	});
}

var connectionType = getConnectionType();
var pageIsHTTP2 = isHTTP2()
var synchJsScript = getSynchJSFiles(docHead)
var thirdPartyScript = getSynchJSFiles(document)
var cssFilesInHead = getCSSFiles()


function checkAccessibility() {
	var headings=['h6','h5','h4','h3','h2','h1']
	var landmarks = ['article','aside','footer','header','nav','main'];
	function accessAltImage(){
		var offending=[];
		var missing=0;
		var score=0;
		var tooLong=0;
		var unique={};
		images.forEach(function(image){
			if(!image.alt||image.alt===''){
				score+=10;
				missing++;
				if(image.src){
					unique[image.src]=1
				}
			}
			else if(image.alt&&image.alt.length>125){
				score+=5;
				tooLong++
			}
		})
		return[Math.max(0, 100 - score),unique,missing,tooLong]
	}
	function accessHeadings(obj){
		var headingData=[];
		var headings_count = 0;
		var score = 100;
		var a = !1;
		headings.forEach(function(heading){
				var entry=obj.getElementsByTagName(heading).length;
				headings_count+=entry;
				a && 0 === entry && (score -= 10, headingData.push(heading)), 0 < entry && (a = !0)
		});
		return [score, headingData]
	}
	function accessLabelOnInput(){
		function getMatchingLabel(id,labels)
			{return labels.filter(function(entry){return entry.attributes.for&&entry.attributes.for.value===id})}
		function hasLabel(input,labels)
			{return input.id&&getMatchingLabel(input.id,labels).length>0}
		function isExcluded(input,excludedInputTypes)
			{return excludedInputTypes.includes(input.type)}
		function isInsideLabel(input)
			{return input.parentElement.nodeName==='LABEL'}
		var labels=Array.prototype.slice.call(window.document.getElementsByTagName('label'));
		var score=0;
		var offending=[];
		var inputs=Array.prototype.slice.call(window.document.querySelectorAll('input, textarea, select'));
		var excludedInputTypes=['button','hidden','image','reset','submit'];
		inputs.forEach(function(input){
			if(isExcluded(input,excludedInputTypes)||isInsideLabel(input)||hasLabel(input,labels)){return}
			offending.push(input.id||input.name||input.outerHTML);
			score+=10
		});
		return[Math.max(0, 100 - score), offending]
	}
	function accessLandmark(){
		var t = 0;
		landmarks.forEach(function(landmark){
			t+=Array.prototype.slice.call(window.document.getElementsByTagName(landmark)).length
		});
		return [t  > 0 ? 100 : 0, t]
	}
	function accessNeverSuppressZoom(){
		function caseInsensitiveAttributeValueFilter(){
			return function(item){
				var attribute=item.getAttribute('name') || '';
				if(attribute.toLowerCase()==='viewport')
					{return item}
				return undefined
			}
		}
		var metasData=[]
		score = 100
		metas.filter(caseInsensitiveAttributeValueFilter()).forEach(function(meta){
			-1 < meta.content.indexOf("user-scalable=no") ||  -1 < meta.content.indexOf("initial-scale=1.0; maximum-scale=1.0") && (score = 0, metasData.push(meta.content))
		})
		return [score, metasData]
	}
	function accessSection(){
		var sections=Array.prototype.slice.call(window.document.getElementsByTagName('section'));
		var sectionData=0;
		var score = 100;
		sections.forEach(function(section){
			res = accessHeadings(section);
			if (res[0] != 100) {
				sectionData += res[1].length;
				score -= (100 - res[0]);
			}
		});
		return [Math.max(0, score), sectionData]
	}
	function accessTable(){
		var tables=Array.prototype.slice.call(window.document.getElementsByTagName('table'));
		var tableData=[]
		var score = 100;
		tables.forEach(function(table){
			var trs=table.getElementsByTagName('tr');
			if(table.getElementsByTagName('caption').length===0 || (trs[0]&&trs[0].getElementsByTagName('th').length===0)){
				if (table.id) {
					tableData.push("@id="+table.id);
				} else if (table.className) {
					tableData.push("@class="+table.className);
				}
				score -= 5
			}
		})
		return [score, tableData]
	}
	return {
		altImage:accessAltImage(),
		heading:accessHeadings(window.document),
		labelOnInput:accessLabelOnInput(),
		landmark:accessLandmark(),
		neverSuppressZoom:accessNeverSuppressZoom(),
		section:accessSection(),
		table:accessTable()
	}
}

function checkBestPractice() {

	function bestPracticeCharset() {
		var charSet = document.characterSet;
		var score = 100;
		if (charSet === null) score = 0
			else if (charSet !== 'UTF-8') score=50;
		return [score, charSet]
	}

    function bestPracticeDoctype() {
        var score = 100
        var docType = document.doctype;
        if (docType === null) score = 0
			else if (!(docType.name.toLowerCase() === 'html' && (docType.systemId === '' || docType.systemId.toLowerCase() === 'about:legacy-compat'))) score = 25
        return [score, ""]
    }

    function bestPracticeHttpsH2() {
        var score = 100
		var protocol = new URL(docUrl).protocol
        if (protocol === 'https:' && connectionType.indexOf('h2') === -1 ) score = 0;
        return [score, protocol, connectionType]
    }

    function bestPracticeLanguage() {
		var language = 'undefined',
			score = 100;
        if ((html.length > 0 && html[0].getAttribute('lang') === null ) || html.length === null) score = 0
			else language = html[0].getAttribute('lang');
        return [score, language]
    }

    function bestPracticeMetaDescription() {
        var score = 100
        var metas_local = metas.filter(metas => metas.name == 'description');
        var description = metas_local.length > 0 ? metas_local[0].getAttribute('content') : '';

        if (description.length === 0) score = 0
			else if (description.length > 155) score = 50;
        return [score, description.length]
    }

    function bestPracticePageTitle() {
        var score = 100;
        var title = docTitle.length;
        if (title === 0) score = 0
			else if (title > 60) score = 50;
        return [score, title]
    }

    function bestPracticeSPDY() {
        var score = 100
        if (connectionType.indexOf('spdy') !== -1) score = 0;
        return [score, connectionType]
    }

    function bestPracticePageURL() {
		var score = 100
		var result = {
			session_id: docUrl.indexOf('?') > -1 && docUrl.indexOf('jsessionid') > docUrl.indexOf('?'),
			parameters: (docUrl.match(/&/g) || []).length,
			len: docUrl.length,
			spaces: docUrl.indexOf(' ') > -1 || docUrl.indexOf('%20') > -1
		}
        if (result.session_id) score = 0;
		if (result.parameters > 1) score -= 50;
		if (result.len > 100) score -= 10;
		if (result.spaces) score -= 10;
		return [score, result]
    }

    return {
        'bestPracticeCharset': bestPracticeCharset(),
        'bestPracticeDoctype': bestPracticeDoctype(),
        'bestPracticeHttpsH2': bestPracticeHttpsH2(),
        'bestPracticeLanguage': bestPracticeLanguage(),
        'bestPracticeMetaDescription': bestPracticeMetaDescription(),
        'bestPracticePageTitle': bestPracticePageTitle(),
        'bestPracticeSPDY': bestPracticeSPDY(),
        'bestPracticePageURL': bestPracticePageURL()
    }
}

function checkPerformance() {

    function avoidScalingImages() {
        var offending = [];
        images.forEach(image => {
			if (image.clientWidth + 100 < image.naturalWidth && image.clientWidth > 0) offending.push(getAbsoluteURL(image.currentSrc))
		})
        return [Math.max(0, 100-(offending.length * 10)), offending]
    }

    function cssPrint() {
        var offending = [];
        links.forEach(link => {
            link.media === 'print' ? offending.push(getAbsoluteURL(link.href)) : null
        });
        return [Math.max(0, 100-offending.length*10), offending]
    }

    function fastRender() {
        var score = 0;
        var blockingCSS = [];
        var blockingJS = [];
        var domains = [];

        function testByType(assetUrl) {
            var domain = getHostname(assetUrl);
            if (domain !== docDomain) {
                if (!exists(domain, domains)) {
                    score += exists(domain, preconnectDomains) ? 5 : 10;
                    domains.push(domain);
                }
                score += 5;
            } else {
                score += 5;
            }
        }

		var preconnectDomains = linksInHead.filter(function (link) {
			return link.rel === 'preconnect';
		}).map(function (link) {
			return getHostname(link.href);
		});


        if (pageIsHTTP2) {
            if (cssFilesInHead.length > 0) {
                cssFilesInHead.forEach(function (url) {
                    if (getTransferSize(url) > 14500) {
                        blockingCSS.push(url);
                        score += 5;
                    }
                });
            }
            if (synchJsScript.length > 0) {
                score += synchJsScript.length * 10;
                synchJsScript.forEach(function (url) {
                    blockingJS.push(url);
                });
            }
        }
        else {
            cssFilesInHead.forEach(function (style) {
                testByType(style);
            });
            blockingCSS = cssFilesInHead;
            synchJsScript.forEach(function (script) {
                testByType(script);
            });
            blockingJS = synchJsScript;
        }

        return [Math.max(0, 100-score), {blockingJS: blockingJS, blockingCSS: blockingCSS, isHTTP2: pageIsHTTP2}]

    }

    function googleTagManager() {
        var score = 100;
        if (window.google_tag_manager) {
            score = 0;
        }
        return [score, window.google_tag_manager]
    }

    function inlineCss() {
        var score = 0;
        if (pageIsHTTP2 && cssFilesInHead.length > 0 && styles.length >= 0 ) {
                score += 10 * cssFilesInHead.length;
				if ( styles.length > 0 ) score += 5;
        }
        return [Math.max(0, 100-score), {isHTTP2: pageIsHTTP2, head_css: cssFilesInHead.length, style_css: styles.length}]
    }

    function pageJquery() {
        var versions = [];
        if (typeof window.jQuery === 'function') {
            versions.push(window.jQuery.fn.jquery);
            var old = window.jQuery;
            while (old.fn && old.fn.jquery) {
                old = window.jQuery.noConflict(true);
                if (!window.jQuery || !window.jQuery.fn) {
                    break;
                }
                if (old.fn.jquery === window.jQuery.fn.jquery) {
                    break;
                }
                versions.push(window.jQuery.fn.jquery);
            }
        }
        var score = versions.length > 1 ? 0 : 100
        return [score, versions]
    }

    function spof() {
        var score = 0;
        var offending = [];
        var offendingDomains = [];

        function checkDomain(element) {
            var elementDomain = getHostname(element);
            if (elementDomain !== docDomain) {
                offending.push(element);
                if (offendingDomains.indexOf(elementDomain) === -1) {
                    offendingDomains.push(elementDomain);
                    score += 10;
                }
            }
        }

        cssFilesInHead.forEach(function (style) {
            checkDomain(style)
        });

        synchJsScript.forEach(function (script) {
            checkDomain(script)
        });

        return [Math.max(0, 100 - score), offending]
    }

    function thirdPartyAsyncJs() {
        var score = 0;
        var offending = [];

        function is3rdParty(url) {
            var hostname = getHostname(url);
            var re;
            for (var i = 0; i < patterns.length; i++) {
                re = new RegExp(patterns[i]);
                if (re.test(hostname)) {
                    return true;
                }
            }
            return false;
        }

        thirdPartyScript.forEach(function (script) {
            if (is3rdParty(script)) {
                offending.push(script);
                score += 10;
            }
        })

        return [Math.max(0, 100 - score), offending]
    }

    return {
        'performanceScalingImages': avoidScalingImages(),
        'performanceCssPrint': cssPrint(),
        'performanceFastRender': fastRender(),
        'performanceGoogleTagManager': googleTagManager(),
        'performanceInlineCss': inlineCss(),
        'performanceJQuery': pageJquery(),
        'performanceSPOF': spof(),
        'performanceThirdPartyAsyncJs': thirdPartyAsyncJs()
    }
}

function checkInfo() {
	function browser(){
		var match = window.navigator.userAgent.match(browsers_regex);
		return match ? match[1] + ' ' + match[2] : 'unknown';
	}

	function domDepth(document) {
		function numParents(elem) {
			var n = 0;
			if (elem.parentNode) {
				while ((elem = elem.parentNode)) {
		        	n++;
				}
			}
			return n;
		}
		var allElems = document.getElementsByTagName('*');
		var allElemsLen = allElems.length;
		var totalParents = 0;
		var maxParents = 0;
		while (allElemsLen--) {
			var parents = numParents(allElems[allElemsLen]);
			if (parents > maxParents) {
		        maxParents = parents;
			}
			totalParents += parents;
		}
		var average = totalParents / allElems.length;
		return {
			avg: Math.round(average),
			max: maxParents
		};
	}

	function storageSize(storage) {
		if (storage) {
			var keys = storage.length || Object.keys(storage).length;
			var bytes = 0;
			for (var i = 0; i < keys; i++) {
				var key = storage.key(i);
				var val = storage.getItem(key);
				bytes += key.length + val.length;
			}
			return bytes;
		} else {
			return 0;
		}
	}

	function metadataDescription(){
		var description = document.querySelector('meta[name="description"]');
		var og = document.querySelector('meta[property="og:description"]');
		if (description) {
			return description.getAttribute('content');
		} else if (og) {
			return og.getAttribute('content');
		} else {
			return '';
		}
  	}

	function isResponsive(){
		var isResponsive = true;
		var bodyScrollWidth = document.body.scrollWidth;
		var windowInnerWidth = window.innerWidth;
		var nodes = document.body.children;
		if (bodyScrollWidth > windowInnerWidth) {
			isResponsive = false;
		}
		for (var i in nodes) {
			if (nodes[i].scrollWidth > windowInnerWidth) {
				isResponsive = false;
			}
		}
		return isResponsive;
	}

	function serviceWorker(){
		if ('serviceWorker' in navigator) {
		    // Only report activated service workers
		    if (navigator.serviceWorker.controller) {
		      if (navigator.serviceWorker.controller.state === 'activated') {
		        return navigator.serviceWorker.controller.scriptURL;
		      } else return false;
		    } else {
		      return false;
		    }
		  } else {
		    return false;
		  }
	}

	function storageSize(storage) {
	    var keys = storage.length || Object.keys(storage).length;
	    var bytes = 0;

	    for (var i = 0; i < keys; i++) {
	      var key = storage.key(i);
	      var val = storage.getItem(key);
	      bytes += key.length + val.length;
	    }
	    return bytes;
	}
	function windowSize() {
		var width =
	    	window.innerWidth ||
			document.documentElement.clientWidth ||
			document.body.clientWidth;
		var height =
	    	window.innerHeight ||
			document.documentElement.clientHeight ||
			document.body.clientHeight;
		return width + 'x' + height;
	}

	return {
		amp: amp(),
		browser: browser(),
		documentHeight: Math.max(document.body.scrollHeight,document.body.offsetHeight, document.documentElement.clientHeight,document.documentElement.scrollHeight,document.documentElement.offsetHeight),
		documentWidth: Math.max(document.body.scrollWidth,document.body.offsetWidth,document.documentElement.clientWidth,document.documentElement.scrollWidth,document.documentElement.offsetWidth),
		connectionType: connectionType,
		title: docTitle,
		domDepth: domDepth(document),
		domElements: document.getElementsByTagName('*').length,
		head: {jssync: synchJsScript,jsasync: getAsynchJSFiles(docHead),css: getCSSFiles},
		iframes: document.getElementsByTagName('iframe').length,
		jsframework: {
			angular: window.angular ? window.angular.version.full : false,
		    backbone: window.Backbone ? window.Backbone.VERSION : false,
		    preact: window.preact ? true : false,
		    vue: window.Vue ? true : false
		},
		storageSize: storageSize(window.localStorage),
		networkConncetionType: window.navigator.connection ? window.navigator.connection.effectiveType : 'unknown',
		resourceHint: {
			dnsprefetch: getResourceHintsHrefs('dns-prefetch'),
			preconnect: getResourceHintsHrefs('preconnect'),
			prefetch: getResourceHintsHrefs('prefetch'),
			prerender: getResourceHintsHrefs('prerender')
		},
		isResponsive: isResponsive(),
		scripts: scripts.length,
		serializedDomSize: document.body.innerHTML.length,
		serviceWorker: serviceWorker(),
		sessionStorageSize: storageSize(window.sessionStorage),
		thirdParty: {
			boomerang: window.BOOMR ? window.BOOMR.version : false,
			facebook: window.FB ? true : false,
			gtm: window.google_tag_manager ? true : false,
			ga: window.ga ? true : false,
			jquery: window.jQuery ? window.jQuery.fn.jquery : false,
			newrelic: window.newrelic ? true : false,
			matomo: window.Piwik ? true : window.Matomo ? true : false
		},
		userTiming: {
			marks: measures.length,
			measures: marks.length
	    },
		windowSize: windowSize()

	}
}

function checkPrivacy(){
	function survilance() {
		var score = 100;
		var offending = [];
		var offenders = ['.google.', 'facebook.com', 'youtube.', 'yahoo.com'];

		for (var i = 0; i < offenders.length; i++) {
			if (docDomain.indexOf(offenders[i]) > -1) {
				score = 0;
				offending.push(docDomain);
			}
		}
		return [score, offending]
	}
	return {
		amp: [amp() ? 0 : 100, amp()],
		facebook: [window.FB ? 0 : 100, window.FB],
		ga: [window.ga && window.ga.create ? 0 : 100, window.ga && window.ga.create],
		https: [docUrl.indexOf('https://') === -1 ? 0 : 100, new URL(docUrl).protocol],
		survilance: survilance(),
		youtube: [window.YT? 0 : 100, window.YT]
	}
}

function checkTiming() {
	function GetFirstPaint() {
		// Try the standardized paint timing api
		var win=window;
		var doc = win.document;
		var firstPaint = undefined
	    try {
	      var entries = performanceObj.getEntriesByType('paint');
	      for (var i = 0; i < entries.length; i++) {
	        if (entries[i]['name'] == 'first-paint') {
	          navStart = performanceObj.getEntriesByType("navigation")[0].startTime;
	          firstPaint = entries[i].startTime - navStart;
	          break;
	        }
	      }
	    } catch(e) {
	    }
	    // If the browser supports a first paint event, just use what the browser reports
	    if (firstPaint === undefined && 'msFirstPaint' in win.performance.timing)
	      firstPaint = performanceObj.timing.msFirstPaint - navStart;
	    // For browsers that don't support first-paint or where we get insane values,
	    // use the time of the last non-async script or css from the head.
	    if (firstPaint === undefined || firstPaint < 0 || firstPaint > 120000) {
	      firstPaint = performanceObj.timing.responseStart - navStart;
	      var headURLs = {};
	      var headElements = doc.getElementsByTagName('head')[0].children;
	      for (var i = 0; i < headElements.length; i++) {
	        var el = headElements[i];
	        if (el.tagName == 'SCRIPT' && el.src && !el.async)
	          headURLs[el.src] = true;
	        if (el.tagName == 'LINK' && el.rel == 'stylesheet' && el.href)
	          headURLs[el.href] = true;
	      }
	      var requests = performanceObj.getEntriesByType("resource");
	      var doneCritical = false;
	      for (var j = 0; j < requests.length; j++) {
	        if (!doneCritical &&
	            headURLs[requests[j].name] &&
	           (requests[j].initiatorType == 'script' || requests[j].initiatorType == 'link')) {
	          var requestEnd = requests[j].responseEnd;
	          if (firstPaint === undefined || requestEnd > firstPaint)
	            firstPaint = requestEnd;
	        } else {
	          doneCritical = true;
	        }
	      }
	    }
	    return Number(Math.max(firstPaint, 0).toFixed(0));
	  };

	function fullyLoaded(){
		// this wierdo checks last loaded resource, e.g. recuring requests
		// influence on this metric
		if (performanceObj && performanceObj.getEntriesByType) {
		    var resources = performanceObj.getEntriesByType('resource');
		    var max = 0;
		    for (var i = 1, len = resources.length; i < len; i++) {
		      if (resources[i].responseEnd > max) {
		        max = resources[i].responseEnd;
		      }
		    }
		    return max;
		  } else {
		    return -1;
		  }
	}

	function RUMSpeedIndex(win) {
	  win = win || window;
	  var doc = win.document;
	  /****************************************************************************
	    Support Routines
	  ****************************************************************************/
	  // Get the rect for the visible portion of the provided DOM element
	  function GetElementViewportRect(el) {
	    var intersect = false;
	    if (el.getBoundingClientRect) {
	      var elRect = el.getBoundingClientRect();
	      intersect = {'top': Math.max(elRect.top, 0),
	                       'left': Math.max(elRect.left, 0),
	                       'bottom': Math.min(elRect.bottom, (win.innerHeight || doc.documentElement.clientHeight)),
	                       'right': Math.min(elRect.right, (win.innerWidth || doc.documentElement.clientWidth))};
	      if (intersect.bottom <= intersect.top ||
	          intersect.right <= intersect.left) {
	        intersect = false;
	      } else {
	        intersect.area = (intersect.bottom - intersect.top) * (intersect.right - intersect.left);
	      }
	    }
	    return intersect;
	  };

	  // Check a given element to see if it is visible
	  function CheckElement(el, url) {
	    if (url) {
	      var rect = GetElementViewportRect(el);
	      if (rect) {
	        rects.push({'url': url,
	                     'area': rect.area,
	                     'rect': rect});
	      }
	    }
	  };

	  // Get the visible rectangles for elements that we care about
	  function GetRects() {
	    // Walk all of the elements in the DOM (try to only do this once)
	    var elements = doc.getElementsByTagName('*');
	    var re = /url\(.*(http.*)\)/ig;
	    for (var i = 0; i < elements.length; i++) {
	      var el = elements[i];
	      var style = win.getComputedStyle(el);

	      // check for Images
	      if (el.tagName == 'IMG') {
	        CheckElement(el, el.src);
	      }
	      // Check for background images
	      if (style['background-image']) {
	        re.lastIndex = 0;
	        var matches = re.exec(style['background-image']);
	        if (matches && matches.length > 1)
	          CheckElement(el, matches[1].replace('"', ''));
	      }
	      // recursively walk any iFrames
	      if (el.tagName == 'IFRAME') {
	        try {
	          var rect = GetElementViewportRect(el);
	          if (rect) {
	            var tm = RUMSpeedIndex(el.contentWindow);
	            if (tm) {
	              rects.push({'tm': tm,
	                          'area': rect.area,
	                          'rect': rect});
	            }
	        }
	        } catch(e) {
	        }
	      }
	    }
	  };

	  // Get the time at which each external resource loaded
	  function GetRectTimings() {
	    var timings = {};
	    var requests = win.performance.getEntriesByType("resource");
	    for (var i = 0; i < requests.length; i++)
	      timings[requests[i].name] = requests[i].responseEnd;
	    for (var j = 0; j < rects.length; j++) {
	      if (!('tm' in rects[j]))
	        rects[j].tm = timings[rects[j].url] !== undefined ? timings[rects[j].url] : 0;
	    }
	  };


	  // Sort and group all of the paint rects by time and use them to
	  // calculate the visual progress
	  var CalculateVisualProgress = function() {
	    var paints = {'0':0};
	    var total = 0;
	    for (var i = 0; i < rects.length; i++) {
	      var tm = firstPaint;
	      if ('tm' in rects[i] && rects[i].tm > firstPaint)
	        tm = rects[i].tm;
	      if (paints[tm] === undefined)
	        paints[tm] = 0;
	      paints[tm] += rects[i].area;
	      total += rects[i].area;
	    }
	    // Add a paint area for the page background (count 10% of the pixels not
	    // covered by existing paint rects.
	    var pixels = Math.max(doc.documentElement.clientWidth, win.innerWidth || 0) *
	                 Math.max(doc.documentElement.clientHeight, win.innerHeight || 0);
	    if (pixels > 0 ) {
	      pixels = Math.max(pixels - total, 0) * pageBackgroundWeight;
	      if (paints[firstPaint] === undefined)
	        paints[firstPaint] = 0;
	      paints[firstPaint] += pixels;
	      total += pixels;
	    }
	    // Calculate the visual progress
	    if (total) {
	      for (var time in paints) {
	        if (paints.hasOwnProperty(time)) {
	          progress.push({'tm': time, 'area': paints[time]});
	        }
	      }
	      progress.sort(function(a,b){return a.tm - b.tm;});
	      var accumulated = 0;
	      for (var j = 0; j < progress.length; j++) {
	        accumulated += progress[j].area;
	        progress[j].progress = accumulated / total;
	      }
	    }
	  };

	  // Given the visual progress information, Calculate the speed index.
	  function CalculateSpeedIndex() {
	    if (progress.length) {
	      SpeedIndex = 0;
	      var lastTime = 0;
	      var lastProgress = 0;
	      for (var i = 0; i < progress.length; i++) {
	        var elapsed = progress[i].tm - lastTime;
	        if (elapsed > 0 && lastProgress < 1)
	          SpeedIndex += (1 - lastProgress) * elapsed;
	        lastTime = progress[i].tm;
	        lastProgress = progress[i].progress;
	      }
	    } else {
	      SpeedIndex = firstPaint;
	    }
	  };

	  /****************************************************************************
	    Main flow
	  ****************************************************************************/
	  var rects = [];
	  var progress = [];
	  var firstPaint;
	  var SpeedIndex;
	  var pageBackgroundWeight = 0.1;
	  try {
	    GetRects();
	    GetRectTimings();
	    firstPaint = GetFirstPaint();
	    CalculateVisualProgress();
	    CalculateSpeedIndex();
	  } catch(e) {
	  }
	 return Number(SpeedIndex.toFixed(0));
	};

	return {
		firstPaint: GetFirstPaint(),
		fullyLoaded: fullyLoaded(),
		speedIndex: RUMSpeedIndex(window)
	}

}


return {
	accessibility: checkAccessibility(),
	bestPractices: checkBestPractice(),
	performance: checkPerformance(),
	timing: checkTiming(),
	privacy: checkPrivacy(),
	info: checkInfo(),
	marks: marks,
	measures: measures,
	performancetiming: timing,
	performanceResources: resources
}})();
'''
