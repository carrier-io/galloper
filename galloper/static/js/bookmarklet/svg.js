/*
SVG Helpers
*/

export function newEl (tagName, settings, css){
    console.log(JSON.stringify(settings));
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


/**
 * Creates a new SVG `text` element
 *
 * @param  {string} text
 * @param  {number} y
 * @param  {string} css
 * @returns {SVGTextElement}
 */
export function newTextEl (text, y, css) {
	return newEl("text", {
			fill : "#111",
			y : y,
			text : text
		}, (css||"") + " text-shadow:0 0 4px #fff;");
};

/**
 * Calculates the with of a SVG `text` element
 *
 * _needs access to iFrame, since width depends on context_
 *
 * @param  {SVGTextElement} textNode
 * @returns {number} width of `textNode`
 */
export function getNodeTextWidth (parent_element, textNode) {
	const tmp = newEl("svg:svg", {}, "visibility:hidden;");
	tmp.appendChild(textNode);
	document.getElementById(parent_element).appendChild(tmp);

	const nodeWidth = textNode.getBBox().width;
	tmp.parentNode.removeChild(tmp);
	return nodeWidth;
};