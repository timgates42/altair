import os
import shutil
import warnings
import json
import random
from operator import itemgetter

import jinja2

from subprocess import CalledProcessError

from docutils import nodes
from docutils.statemachine import ViewList
from docutils.parsers.rst import Directive
from docutils.parsers.rst.directives import flag

from .utils import get_docstring_and_rest, prev_this_next
from altair.vegalite.v2.examples import iter_examples


GALLERY_TEMPLATE = jinja2.Template(u"""
.. This document is auto-generated by the altair-gallery extension. Do not modify directly.

.. _{{ gallery_ref }}:

{{ title }}
{% for char in title %}-{% endfor %}

The following examples are automatically generated from
`Vega-Lite's Examples <http://vega.github.io/vega-lite/examples>`_

{% for group in examples|groupby('category') %}
* :ref:`gallery-category-{{ group.grouper }}`
{% endfor %}

{% for group in examples|groupby('category') %}

.. _gallery-category-{{ group.grouper }}:

{{ group.grouper }}
{% for char in group.grouper %}~{% endfor %}

{% for example in group.list %}

- :ref:`gallery_{{ example.name }}`

{% endfor %}
{% endfor %}


.. toctree::
   :hidden:
{% for example in examples %}
   {{ example.name }}
{%- endfor %}
""")


EXAMPLE_TEMPLATE = jinja2.Template(u"""
.. This document is auto-generated by the altair-gallery extension. Do not modify directly.

{% if prev_ref -%} < :ref:`{{ prev_ref }}` {% endif %}
| :ref:`{{ gallery_ref }}` |
{%- if next_ref %} :ref:`{{ next_ref }}` >{% endif %}

.. _gallery_{{ name }}:

{{ docstring }}

.. altair-plot::
    {% if code_below %}:code-below:{% endif %}

    {{ code | indent(4) }}

.. toctree::
   :hidden:
""")


def populate_examples(**kwds):
    """Iterate through Altair examples and extract code"""

    examples = sorted(iter_examples(), key=itemgetter('name'))

    for example in examples:
        docstring, code, lineno = get_docstring_and_rest(example['filename'])
        code += '\nchart'
        example.update(kwds)
        example.update({'docstring': docstring,
                        'code': code,
                        'lineno': lineno})

    return examples


def main(app):
    print('altair-gallery main')

    gallery_dir = app.builder.config.altair_gallery_dir
    target_dir = os.path.join(app.builder.srcdir, gallery_dir)
    image_dir = os.path.join(app.builder.srcdir, '_images')

    gallery_ref = app.builder.config.altair_gallery_ref
    gallery_title = app.builder.config.altair_gallery_title
    examples = populate_examples(gallery_ref=gallery_ref,
                                 code_below=True)

    if not os.path.exists(target_dir):
        os.makedirs(target_dir)

    # Write the gallery index file
    with open(os.path.join(target_dir, 'index.rst'), 'w') as f:
        f.write(GALLERY_TEMPLATE.render(title=gallery_title,
                                        examples=examples,
                                        image_dir='/_images',
                                        gallery_ref=gallery_ref))

    # Write the individual example files
    for prev_ex, example, next_ex in prev_this_next(examples):
        if prev_ex:
            example['prev_ref'] = "gallery_{name}".format(**prev_ex)
        if next_ex:
            example['next_ref'] = "gallery_{name}".format(**next_ex)
        target_filename = os.path.join(target_dir, example['name'] + '.rst')
        with open(os.path.join(target_filename), 'w') as f:
            f.write(EXAMPLE_TEMPLATE.render(example))


def setup(app):
    app.connect('builder-inited', main)
    app.add_stylesheet('altair-gallery.css')
    app.add_config_value('altair_gallery_dir', 'gallery', 'env')
    app.add_config_value('altair_gallery_ref', 'example-gallery', 'env')
    app.add_config_value('altair_gallery_title', 'Example Gallery', 'env')
