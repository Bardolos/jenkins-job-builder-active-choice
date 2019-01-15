# Copyright 2016 Bulat Gaifullin
#
# This file is part of jenkins-job-builder-active-choice
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import xml.etree.ElementTree as Xml


CHOICE_TYPE = {
    'input_textbox': 'ET_TEXT_BOX',
    'numbered_list': 'ET_ORDERED_LIST',
    'bullet_items_list': 'ET_UNORDERED_LIST',
    'formatted_html': 'ET_FORMATTED_HTML',
    'formatted_hidden_html': 'ET_FORMATTED_HIDDEN_HTML',
}

REQUIRED = [
    # (yaml tag)
    ('name', 'name'),
    ('project', 'projectName'),
]

OPTIONAL = [
    # ( yaml tag, xml tag, default value )
    ('description', 'description', ''),
    ('visible-item-count', 'visibleItemCount', 1),
    ('reference', 'referencedParameters', ''),
    ('filterable', 'filterable', False),
    ('omit-value-field', 'omitValueField', False),
]


def _to_str(x):
    if not isinstance(x, (str, unicode)):
        return str(x).lower()
    return x


def _add_element(xml_parent, tag, value):
    Xml.SubElement(xml_parent, tag).text = _to_str(value)


def _add_script(xml_parent, tag, value):
    section = Xml.SubElement(xml_parent, tag)
    Xml.SubElement(section, "script").text = value
    Xml.SubElement(section, "sandbox").text = "false"


def _unique_string(project, name):
    return 'choice-param-{0}-{1}'.format(project, name).lower()


def active_reactive_choice_parameter(parser, xml_parent, data):
    """yaml: active-reactive-choice
    Creates an active choice parameter
    Requires the Jenkins :jenkins-wiki:`Active Choices Plugin <Active+Choices+Plugin>`.

    :arg str name: the name of the parameter
    :arg str script: the groovy script which generates choices
    :arg str description: a description of the parameter (optional)
    arg: int visible-item-count: a number of visible items
    arg: str fallback-script: a groovy script which will be evaluated if main script fails (optional)
    arg: str reference: the name of parameter on changing that the parameter will be re-evaluated
    arg: str choice-type: a choice type, can be on of single, multi, checkbox or radio
    arg: bool filterable: added text box to filter elements
    Example::

    .. code-block:: yaml

        - active-reactive-choice:
          name: DYNAMIC_CHOICE
          project: test_project
          script: |
            return ['foo', 'bar']
    """

    element_name = 'org.biouno.unochoice.DynamicReferenceParameter'

    section = Xml.SubElement(xml_parent, element_name)
    scripts = Xml.SubElement(section, 'script', {'class': 'org.biouno.unochoice.model.GroovyScript'})
    Xml.SubElement(section, 'parameters', {'class': 'linked-hash-map'})

    for name, tag in REQUIRED:
        try:
            _add_element(section, tag, data[name])
        except KeyError:
            raise Exception("missing mandatory argument %s" % name)

    for name, tag, default in OPTIONAL:
        _add_element(section, tag, data.get(name, default))

    try:
        script_file = data.get("script-file", "")
        contents = ""
        if not script_file:
            contents = data["script"]
        else:
            contents = open(script_file, "r").read()
        _add_script(scripts, "secureScript", contents)
    except KeyError:
        raise Exception("missing mandatory argument script or script-file (check if file exists)")

    _add_script(scripts, "secureFallbackScript", data.get("fallback-script", ""))

    _add_element(section, 'choiceType', CHOICE_TYPE[data.get('choice-type', 'input_textbox')])
    # added calculated fields
    _add_element(section, 'randomName', _unique_string(data['project'], data['name']))
