import base64
import re
from os import path, mkdir, environ
from subprocess import Popen, PIPE
from multiprocessing import Pool
from jinja2 import Environment, PackageLoader, select_autoescape

ffmpeg_path = environ.get("ffmpg_path", "/opt/ffmpeg/bin/ffmpeg")
report_path = '/tmp'


def sanitize(filename):
    return "".join(x for x in filename if x.isalnum())[0:25]

def trim_screenshot(kwargs):
    try:
        image_path = f'{path.join(kwargs["processing_path"], sanitize(kwargs["test_name"]), str(kwargs["ms"]))}_out.jpg'
        command = f'{ffmpeg_path} -ss {str(round(kwargs["ms"] / 1000, 3))} -i {kwargs["video_path"]} ' \
            f'-vframes 1 {image_path}'
        print(Popen(command, stderr=PIPE, shell=True, universal_newlines=True).communicate())
        with open(image_path, "rb") as image_file:
            return {kwargs["ms"]: base64.b64encode(image_file.read()).decode("utf-8")}
    except FileNotFoundError:
        from traceback import format_exc
        print(format_exc())
        return {}


class prepareReport(object):
    def __init__(self, video_path, request_params, processing_path, return_report=True):
        self.processing_path = processing_path
        self.return_report = return_report
        self.acc_score, self.acc_data = self.accessibility_audit(request_params['accessibility'])
        self.bp_score, self.bp_data = self.bestpractice_audit(request_params['bestPractices'])
        self.perf_score, self.perf_data = self.performance_audit(request_params['performance'])
        self.priv_score, self.priv_data = self.privacy_audit(request_params['privacy'])
        test_result = 'fail'
        total_score = (self.acc_score * 30 + self.priv_score * 50 + self.bp_score * 22 + self.perf_score * 44) / 146
        if total_score > 90 and request_params['timing']['speedIndex'] < 1000:
            test_result = 'pass'
        elif total_score > 75 and request_params['timing']['speedIndex'] < 3000:
            test_result = 'warning'
        self.report = self.generate_html(request_params['info']['title'], video_path, test_result,
                                         request_params['info'].get('testStart', 0), self.perf_score, self.priv_score,
                                         self.acc_score, self.bp_score, self.acc_data, self.perf_data, self.bp_data,
                                         self.priv_data, request_params['performanceResources'],
                                         request_params['marks'], request_params['measures'],
                                         request_params['performancetiming'], request_params['info'],
                                         request_params['timing'])

    @staticmethod
    def privacy_audit(privacy_data):
        result = []
        if privacy_data['amp'][0] != 100:
            result.append({
                'title': 'Avoid including AMP',
                'description': "You share share private user information with Google that "
                               "your user hasn't agreed on sharing.",
                'advice': 'The page is using AMP, that makes you share private user information with Google.',
                'score': 0
            })
        if privacy_data['facebook'][0] != 100:
            result.append({
                'title': 'Avoid including Facebook',
                'description': "You share share private user information with Facebook that "
                               "your user hasn't agreed on sharing.",
                'advice': 'The page gets content from Facebook. That means you share your '
                          'users private information with Facebook.',
                'score': 0

            })
        if privacy_data['ga'][0] != 100:
            result.append({
                'title': 'Avoid using Google Analytics',
                'description': "Google Analytics share private user information with "
                               "Google that your user hasn't agreed on sharing.",
                'advice': 'The page is using Google Analytics meaning you share your users '
                          'private information with Google. You should use analytics that care about user privacy',
                'score': 0})
        if privacy_data['https'][0] != 100:
            result.append({
                'title': 'Serve your content securely',
                'description': 'A page should always use HTTPS (https://https.cio.gov/everything/). Y'
                               'ou also need that for HTTP/2. You can get your free SSL/TLC certificate '
                               'from https://letsencrypt.org/.',
                'advice': 'The page is not using HTTPS. Every unencrypted HTTP request reveals information about '
                          'user’s behavior',
                'score': 0,
            })
        if privacy_data['survilance'][0] != 100:
            result.append({
                'title': 'Avoid using surveillance web sites',
                'description': 'Do not use web sites that harvest private user information and sell it to other '
                               'companies.',
                'advice': " ".join(privacy_data['survilance'][1]) +
                          ' uses harvest user information and sell it to other '
                          'companies without the users agreement. That is not OK.',
                'score': privacy_data['survilance'][0]
            })
        if privacy_data['youtube'][0] != 100:
            result.append({
                'title': 'Avoid including Youtube videos',
                'description': 'If you include Youtube videos on your page, you are sharing private user '
                               'information with Google.',
                'advice': 'The page is including code from Youtube. You share user private information with Google. '
                          'Instead you can host a video screenshot and let the user choose to go to '
                          'Youtube or not, by clicking on the screenshot. '
                          'You can look at http://labnol.org/?p=27941 and make sure you host your screenshot yourself.'
                          ' Or choose another video service.',
                'score': 0,
            })

        score = (privacy_data['amp'][0]*8 + privacy_data['facebook'][0]*8 +
                 privacy_data['ga'][0] * 8 + privacy_data['https'][0] * 10 + privacy_data['survilance'][0] * 10 +
                 privacy_data['youtube'][0] * 6)/ 50

        return int(score), result

    @staticmethod
    def accessibility_audit(accessibility_data):
        result = []
        if accessibility_data['altImage'][0] != 100:
            advice = ''
            if accessibility_data['altImage'][2]:
                advice = f"The page has {accessibility_data['altImage'][2]} images that lack alt attribute(s) " \
                    f"and {len(list(accessibility_data['altImage'][1].keys()))} of them are unique."
            if accessibility_data['altImage'][3]:
                advice += f"<br />The page has {accessibility_data['altImage'][3]} images where the alt text are " \
                    f"too long (longer than 125 characters)."
            result.append({
                'title': 'Always use an alt attribute on image tags',
                'description': 'All img tags require an alt attribute. This goes without exception. '
                               'Everything else is an error. If you have an img tag in your HTML without '
                               'an alt attribute, add it now. https://www.marcozehe.de/2015/12/14/the-'
                               'web-accessibility-basics/',
                'advice': advice,
                'score': accessibility_data['altImage'][0],
                'details': list(accessibility_data['altImage'][1].keys())
            })

        if accessibility_data['heading'][0] != 100:
            result.append({
                "title": 'Use heading tags to structure your page',
                "description": 'Headings give your document a logical, easy to follow structure. Have you ever'
                               ' wondered how Wikipedia puts together its table of contents for each article? '
                               'They use the logical heading structure for that, too! The H1 through H6 elements '
                               'are unambiguous in telling screen readers, search engines and other technologies'
                               ' what the structure of your document is.'
                               ' https://www.marcozehe.de/2015/12/14/the-web-accessibility-basics/',
                "advice": "The page is missing <" + ", ".join(accessibility_data['heading'][1]) +
                          "and has heading(s) with lower priority.",
                "score": accessibility_data['heading'][0],
                "details": []
            })
        if accessibility_data['labelOnInput'][0] != 100:
            result.append({
                'title': 'Always set labels on inputs in forms',
                'description': 'Most input elements, as well as the select and textarea elements, need '
                               'an associated label element that states their purpose. The only exception '
                               'is those that produce a button, like the reset and submit buttons do. Others, '
                               'be it text, checkbox, password, radio (button), search etc. require a label '
                               'element to be present. '
                               'https://www.marcozehe.de/2015/12/14/the-web-accessibility-basics/',
                'advice': f"There are {len(accessibility_data['labelOnInput'][1])} input(s) that are missing labels "
                f"on a form.",
                'score': accessibility_data['labelOnInput'][0],
                'details': accessibility_data['labelOnInput'][1]
            })
        if accessibility_data['landmark'][0] != 100:
            result.append({
                "title": 'Structure your content by using landmarks',
                "description": 'Landmarks can be article, aside, footer, header, nav or main tag. '
                               'Adding such landmarks appropriately can help further provide sense to '
                               'your document and help users more easily navigate it. '
                               'https://www.marcozehe.de/2015/12/14/the-web-accessibility-basics/',
                "advice": "The page doesn't use any landmarks.",
                'score': accessibility_data['landmark'][0],
                'details': []})
        if accessibility_data['neverSuppressZoom'][0] != 100:
            result.append({
                "title": "Don't suppress pinch zoom",
                "description": "A key feature of mobile browsing is being able to zoom in to read content "
                               "and out to locate content within a page. "
                               "http://www.iheni.com/mobile-accessibility-tip-dont-suppress-pinch-zoom/",
                "advice": "What! The page suppresses zooming, you really shouldn't do that.",
                "score": accessibility_data['neverSuppressZoom'][0],
                "details": accessibility_data['neverSuppressZoom'][1]
            })
        if accessibility_data['section'][0] != 100:
            result.append({
                "title": 'Use headings tags within section tags to better structure your page',
                "description": 'Section tags should have at least one heading element as a direct descendant.',
                "advice": f"The page is missing heading(s) within a section tag on the page. "
                f"It happens {accessibility_data['section'][1]} times.",
                "score": accessibility_data['section'][0],
                'details': []})
        if accessibility_data['table'][0] != 100:
            result.append({
                "title": 'Use caption and th in tables',
                "description": 'Add a caption element to give the table a proper heading or summary. '
                               'Use th elements to denote column and row headings. Make use of their '
                               'scope and other attributes to clearly associate what belongs to which. '
                               'https://www.marcozehe.de/2015/12/14/the-web-accessibility-basics/',
                "advice": 'The page has tables that are missing caption, please use them to give'
                          ' them a proper heading or summary.',
                "score": accessibility_data['table'][0],
                "details": accessibility_data['table'][1]
            })
        total_score = round((accessibility_data['altImage'][0] * 5 + accessibility_data['heading'][0] * 4 +
                             accessibility_data['labelOnInput'][0] * 3 + accessibility_data['landmark'][0] * 5 +
                             accessibility_data['neverSuppressZoom'][0] * 8 + accessibility_data['section'][0] * 0 +
                             accessibility_data['table'][0] * 5) / 30)
        return total_score, result

    @staticmethod
    def bestpractice_audit(bestpractice_data):
        result = []
        if bestpractice_data['bestPracticeCharset'][0] != 100:
            advice = 'The page is missing a character set. ' \
                     'If you use Chrome/Firefox we know you are missing it, ' \
                     'if you use another browser, it could be an implementation problem.'

            if bestpractice_data['bestPracticeCharset'][0] == 50:
                advice = 'You are not using charset UTF-8?'
            result.append({
                "title": 'Declare a charset in your document',
                "description": 'The Unicode Standard (UTF-8) covers (almost) all the characters, punctuations,'
                               ' and symbols in the world. Please use that.',
                "advice": advice,
                "score": bestpractice_data['bestPracticeCharset'][0],
                "details": []
            })
        if bestpractice_data['bestPracticeDoctype'][0] != 100:
            advice = 'The page is missing a doctype. Please use <!DOCTYPE html>.'
            if bestpractice_data['bestPracticeDoctype'][0] == 25:
                advice = 'Just do yourself a favor and use the HTML5 doctype declaration: <!DOCTYPE html>'
            result.append({
                "title": 'Declare a doctype in your document',
                "description": 'The <!DOCTYPE> declaration is not an HTML tag; it is an instruction to the web browser '
                               'about what version of HTML the page is written in.',
                "advice": advice,
                "score": bestpractice_data['bestPracticeDoctype'][0],
                "details": []
            })
        if bestpractice_data['bestPracticeHttpsH2'][0] != 100:
            advice = 'The page is using HTTPS but not HTTP/2. Change to HTTP/2 ' \
                     ' to follow new best practice with compressed headers and maybe make the site faster.'
            result.append({
                "title": 'Serve your content using HTTP/2',
                "description": 'Using HTTP/2 together with HTTPS is the new best practice. '
                               'If you use HTTPS (you should), you should also use HTTP/2 since you will then '
                               'get compressed headers. However it may not '
                               'be faster for all users.',
                "advice": advice,
                "score": bestpractice_data['bestPracticeHttpsH2'][0],
                "details": []
            })
        if bestpractice_data['bestPracticeLanguage'][0] != 100:
            advice = 'What! The page is missing the HTML tag!'
            if bestpractice_data['bestPracticeLanguage'][1] is None:
                advice = 'The page is missing a language definition in the HTML tag. Define it with <html ' \
                         'lang="YOUR_LANGUAGE_CODE">'
            result.append({
                "title": 'Declare the language code for your document',
                "description": 'According to the W3C recommendation you should declare the primary '
                               'language for each Web page with the lang attribute inside the <html> tag '
                               'https://www.w3.org/International/questions/qa-html-language-declarations#basics.',
                "advice": advice,
                "score": bestpractice_data['bestPracticeLanguage'][0],
                "details": []
            })
        if bestpractice_data['bestPracticeMetaDescription'][0] != 100:
            advice = 'The page is missing a meta description.'
            if bestpractice_data['bestPracticeMetaDescription'][0] == 50:
                advice = f"The meta description is too long. " \
                    f"It has {bestpractice_data['bestPracticeMetaDescription'][1]} " \
                    f"characters, the recommended max is 155 "
            result.append({
                "title": 'Meta description',
                "description": 'Use a page description to make the page more relevant to search engines.',
                "advice": advice,
                "score": bestpractice_data['bestPracticeMetaDescription'][0],
                "details": []
            })
        if bestpractice_data['bestPracticePageTitle'][0] != 100:
            advice = 'The page is missing a title.'
            if bestpractice_data['bestPracticePageTitle'][0] == 50:
                advice = f"The title is too long by {bestpractice_data['bestPracticePageTitle'][1] - 60} " \
                    f"characters. The recommended max is 60"
            result.append({
                "title": 'Page title',
                "description": 'Use a title to make the page more relevant to search engines.',
                "advice": advice,
                "score": bestpractice_data['bestPracticePageTitle'][0],
                "details": []
            })
        if bestpractice_data['bestPracticePageURL'][0] != 100:
            advice = ''
            if bestpractice_data['bestPracticePageURL'][1]['session_id']:
                advice += 'The page has the session id for the user as a parameter, please change so the ' \
                          'session handling is done only with cookies. '
            if bestpractice_data['bestPracticePageURL'][1]['parameters'] > 2:
                advice += 'The page is using more than two request parameters. You should really rethink ' \
                          'and try to minimize the number of parameters. '
            if bestpractice_data['bestPracticePageURL'][1]['len'] > 100:
                advice += f"The URL is {bestpractice_data['bestPracticePageURL'][1]['len']} " \
                    f"characters long. Try to make it less than 100 characters. "
            if bestpractice_data['bestPracticePageURL'][1]['spaces']:
                advice += 'Could the developer or the CMS be on Windows? Avoid using spaces in the ' \
                          'URLs, use hyphens or underscores. '
            result.append({
                "title": 'Have a good URL format',
                "description": 'A clean URL is good for the user and for SEO. Make them human readable, avoid too long '
                               'URLs, spaces in the URL, too many request parameters, and never '
                               'ever have the session id in your URL.',
                "advice": advice,
                "score": bestpractice_data['bestPracticePageURL'][0],
                "details": []
            })
        if bestpractice_data['bestPracticeSPDY'][0] != 100:
            result.append({
                "title": 'EOL for SPDY in Chrome',
                "description": "Chrome dropped supports for SPDY in Chrome 51, upgrade to HTTP/2 "
                               "as soon as possible. The page has more users (browsers) supporting "
                               "HTTP/2 than supports SPDY. ",
                "advice": 'The page is using SPDY. Chrome dropped support for SPDY in Chrome 51. '
                          'Change to HTTP/2 asap.',
                "score": bestpractice_data['bestPracticeSPDY'][0],
                "details": []
            })
        total_score = round((bestpractice_data['bestPracticeCharset'][0] * 2 +
                             bestpractice_data['bestPracticeDoctype'][0] * 2 +
                             bestpractice_data['bestPracticeHttpsH2'][0] * 2 +
                             bestpractice_data['bestPracticeLanguage'][0] * 3 +
                             bestpractice_data['bestPracticeMetaDescription'][0] * 5 +
                             bestpractice_data['bestPracticePageTitle'][0] * 5 +
                             bestpractice_data['bestPracticePageURL'][0] * 2 +
                             bestpractice_data['bestPracticeSPDY'][0] * 1) / 22)
        return total_score, result

    @staticmethod
    def performance_audit(performance_data):
        result = []
        if performance_data['performanceCssPrint'][0] != 100:
            advice = ""
            if len(performance_data['performanceCssPrint'][1]) > 0:
                advice += f"The page has {len(performance_data['performanceCssPrint'][1])} print stylesheets. You " \
                    f"should include that stylesheet using @media type print instead. "
            result.append({
                "title": "Do not load specific print stylesheets.",
                "description": "Loading a specific stylesheet for printing slows down the page, even though it is not "
                               "used. You can include the print styles inside your other CSS file(s) just by using an "
                               "@media query targeting type print.",
                "advice": advice,
                "score": performance_data['performanceCssPrint'][0],
                "details": performance_data['performanceCssPrint'][1]
            })

        if performance_data['performanceFastRender'][0] != 100:
            advice = ""
            fast_render_data = performance_data['performanceFastRender'][1]
            if fast_render_data['isHTTP2']:
                if fast_render_data['blockingCSS']:
                    advice += "Make sure that the server pushes your CSS resources for faster rendering. "
                    advice += "The style(s): "
                    for css_resource in fast_render_data['blockingCSS']:
                         advice += f"<p>{css_resource}</p>"
                    advice += "is larger than the magic number TCP window size 14.5 kB. " \
                              "Make the file smaller and the page will render faster. "
                if fast_render_data['blockingJS']:
                    advice += "Avoid loading synchronously JavaScript inside of head, you shouldn't" \
                              " need JavaScript to render your page! <br /> list of blocking JS: <br />"
                    for js_resource in fast_render_data['blockingCSS']:
                         advice += f"<p>{js_resource}</p>"

            advice += f"The page has {len(fast_render_data['blockingCSS'])} render blocking CSS request(s) and " \
                f" {len(fast_render_data['blockingJS'])} blocking JavaScript request(s) inside of head."

            result.append({
                "title": "Avoid slowing down the critical rendering path",
                "description": 'The critical rendering path is what the browser needs to do to start '
                               'rendering the page. Every file requested inside of the head element will '
                               'postpone the rendering of the page, because the browser need to do the request. '
                               'Avoid loading JavaScript synchronously inside of the head (you should not '
                               'need JavaScript to render the page), request files from the same domain as '
                               'the main document (to avoid DNS lookups) and inline CSS or use server push '
                               'for really fast rendering and a short rendering path.',
                "advice": advice,
                "score": performance_data['performanceFastRender'][0],
                "details": fast_render_data['blockingCSS'] + fast_render_data['blockingJS']
            })

        if performance_data['performanceGoogleTagManager'][0] != 100:
            result.append({
                "title": "Avoid using Google Tag Manager",
                "description": "Google Tag Manager makes it possible for non tech users to add scripts to your "
                               "page that will downgrade performance.",
                "advice": "The page is using Google Tag Manager, this is a performance risk since non-tech "
                          "users can add JavaScript to your page.",
                "score": performance_data['performanceGoogleTagManager'][0],
                "details": []
            })

        if performance_data['performanceInlineCss'][0] != 100:
            advice = ''
            data = performance_data['performanceInlineCss'][1]
            if data['head_css'] > 0 & data['style_css'] > 0:
                if data['isHTTP2']:
                    advice += "The page has both inline CSS and CSS requests even though it uses a " \
                              "HTTP/2-ish connection. If you have many users on slow connections, it can be " \
                              "better to only inline the CSS. Run " \
                              "your own tests and check the waterfall graph to see what happens. "
                else:
                    advice += f"The page has both inline styles as well as it is requesting {data['head_css']} " \
                        f"CSS file(s) inside of the head. Let's only inline CSS for really fast render. "
            if data['head_css'] > 0 & data['style_css'] == 0:
                if data['isHTTP2']:
                    advice += "The page has inline CSS and uses HTTP/2. Do you have a lot of users with " \
                              "slow connections on the site? It is good to inline CSS when using HTTP/2. " \
                              "If not, and your server supports server push, you can probably " \
                              "push the CSS files instead."
                else:
                    advice += f"The page loads {data['head_css']} CSS request(s) inside of head, " \
                        f"try to inline the CSS for the first render and lazy load the rest."
            if data['isHTTP2'] & data['head_css'] > 0:
                advice += "It is always faster for the user if you inline CSS instead of making a CSS request."
            result.append({
                "title": "Inline CSS for faster first render",
                "description": "In the early days of the Internet, inlining CSS was one of the ugliest "
                               "things you can do. That has changed if you want your page to start rendering "
                               "fast for your user. Always inline the critical CSS when you use HTTP/1 and HTTP/2 "
                               "(avoid doing CSS requests that block rendering) and lazy load and cache the "
                               "rest of the CSS. It is a little more complicated when using HTTP/2. Does your "
                               "server support HTTP push? Then maybe that can help. Do you have a lot of users "
                               "on a slow connection and are serving large chunks of HTML? Then it could be better "
                               "to use the inline technique, becasue some servers always prioritize HTML content "
                               "over CSS so the user needs to download the HTML first, before the CSS is downloaded. ",
                "advice": advice,
                "score": performance_data['performanceInlineCss'][0],
                "details": []
            })

        if performance_data['performanceJQuery'][0] != 100:
            result.append({
                "title": "Avoid using more than one jQuery version per page",
                "description": "There are sites out there that use multiple versions of jQuery on the same page. You "
                               "shouldn't do that because the user will then unnecessarily download extra data. "
                               "Cleanup the code and make sure you only use one version.",
                "advice": f"The page uses {len(performance_data['performanceJQuery'][1])} versions of jQuery! You only "
                f"need one version, please remove the unnecessary version(s).",
                "score": performance_data['performanceJQuery'][0],
                "details": performance_data['performanceJQuery'][1]
            })

        if performance_data['performanceSPOF'][0] != 100:
            result.append({
                "title": "Avoid Frontend single point of failures",
                "description": "A page can be stopped from loading in the browser if a single JavaScript, CSS, "
                               "and in some cases a font, couldn't be fetched or is loading really slowly (the white "
                               "screen of death). That is a scenario you really want to avoid. Never load 3rd-party "
                               "components synchronously inside of the head tag.",
                "advice": f"The page has {len(performance_data['performanceSPOF'][1])} requests inside of the head "
                          f"that can cause a SPOF (single point of failure). Load them asynchronously or move "
                          f"them outside of the document head.",
                "score": performance_data['performanceSPOF'][0],
                "details": performance_data['performanceSPOF'][1]
            })

        if performance_data['performanceScalingImages'][0] != 100:
            advice = f"The page has {len(performance_data['performanceScalingImages'][1])} image(s) " \
                     f"that are scaled more than 100 pixels. It would be better if those images are sent " \
                     f"so the browser don't need to scale them. "
            result.append({
                "title": "Don't scale images in the browser",
                "description": "It's easy to scale images in the browser and make  sure they look good in different "
                               "devices, however that is bad for performance! Scaling images in the "
                               "browser takes extra CPU time and will hurt performance on mobile. And the user "
                               "will download extra kilobytes (sometimes megabytes) of data that could be avoided. "
                               "Don't do that, make sure you create multiple version of the same image server-side "
                               "and serve the appropriate one.",
                "advice": advice,
                "score": performance_data['performanceScalingImages'][0],
                "details": performance_data['performanceScalingImages'][1]
                })

        if performance_data['performanceThirdPartyAsyncJs'][0] != 100:
            result.append({
                "title": "Always load third-party JavaScript asynchronously",
                "description": "Use JavaScript snippets that load the JS files asynchronously in order to speed up the "
                               "user experience and avoid blocking the initial load.",
                "advice": f"The page has {len(performance_data['performanceThirdPartyAsyncJs'][1])} synchronous "
                          f"3rd-party JavaScript request(s). Change it to be asynchronous instead.",
                "score": performance_data['performanceThirdPartyAsyncJs'][0],
                "details": performance_data['performanceThirdPartyAsyncJs'][1]
            })

        total_score = round((
            performance_data['performanceCssPrint'][0] * 1 + performance_data['performanceFastRender'][0] * 10 +
            performance_data['performanceGoogleTagManager'][0] * 5 + performance_data['performanceInlineCss'][0] * 7 +
            performance_data['performanceJQuery'][0] * 4 + performance_data['performanceSPOF'][0] * 7 +
            performance_data['performanceScalingImages'][0] * 5 +
            performance_data['performanceThirdPartyAsyncJs'][0] * 5)/44)
        return total_score,result

    def concut_video(self, start, end, page_name, video_path):
        p = Pool(7)
        res = []
        try:
            page_name = page_name.replace(" ", "_")
            process_params = [{
                "video_path": video_path,
                "ms": part,
                "test_name": page_name,
                "processing_path": self.processing_path,
            } for part in range(start, end, (end-start)//8)][1:]
            if not path.exists(path.join(self.processing_path, page_name)):
                mkdir(path.join(self.processing_path, sanitize(page_name)))
            res = p.map(trim_screenshot, process_params)
        except:
            from traceback import format_exc
            print(format_exc())
        finally:
            p.terminate()
        return res

    def generate_html(self, page_name, video_path, test_status, start_time, perf_score,
                      priv_score, acc_score, bp_score, acc_findings, perf_findings, bp_findings,
                      priv_findings, resource_timing, marks, measures, navigation_timing, info, timing):
        env = Environment(
            loader=PackageLoader('galloper', 'templates'),
            autoescape=select_autoescape(['html', 'xml'])
        )
        if test_status == 'pass':
            str_test_status = 'PASSED'
            test_status = 'ok'
        elif test_status == 'warning':
            str_test_status = 'WARNING'
            test_status = 'warning'
        else:
            str_test_status = 'FAILED'
            test_status = 'error'
        last_response_end = max([resource['responseEnd'] for resource in resource_timing])
        end = int(max([navigation_timing['loadEventEnd'] - navigation_timing['navigationStart'], last_response_end]))
        screenshots_dict = []
        for each in self.concut_video(start_time, end, page_name, video_path):
            if each:
                screenshots_dict.append(each)
        screenshots = [list(e.values())[0] for e in sorted(screenshots_dict, key=lambda d: list(d.keys()))]
        template = env.get_template('perftemplate/perfreport.html')
        res = template.render(page_name=page_name, str_test_status=str_test_status, test_status=test_status,
                              perf_score=perf_score, priv_score=priv_score, acc_score=acc_score, bp_score=bp_score,
                              screenshots=screenshots, acc_findings=acc_findings, perf_findings=perf_findings,
                              bp_findings=bp_findings, priv_findings=priv_findings, resource_timing=resource_timing,
                              marks=marks, measures=measures, navigation_timing=navigation_timing,
                              info=info, timing=timing)
        report_name = f'{page_name}.html'
        report_name = path.join(report_path, f'{report_name}.html')
        if self.return_report:
            return re.sub(r'[^\x00-\x7f]', r'', res)
        else:
            with open(report_name, "w") as f:
                f.write(re.sub(r'[^\x00-\x7f]', r'', res))
            return report_name

    def get_report(self):
        if self.report:
            return self.report
